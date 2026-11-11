import duckdb
import pytest

from ui.server import render


def test_citi_branding(database):
    status, html = render("/")
    assert status == 200
    assert '<svg xmlns="http://www.w3.org/2000/svg"' in html
    assert 'aria-label="Citi"' in html
    assert "Demonstration data – synthetic" in html
    assert "Northhaven" not in html


@pytest.fixture
def database(tmp_path, monkeypatch):
    path = tmp_path / "ui.duckdb"
    monkeypatch.setenv("RECON_DB", str(path))
    with duckdb.connect(str(path)) as db:
        db.execute("CREATE TABLE sor_loans (loan_id VARCHAR, client_id VARCHAR, product_code VARCHAR, currency VARCHAR, balance DECIMAL(18,2), balance_usd DECIMAL(18,2), status VARCHAR, booking_date DATE)")
        db.execute("INSERT INTO sor_loans VALUES ('L1','C01','MTG','GBP',1000,1273.40,'ACTIVE','2025-03-01'), ('L2','C02','REV','USD',0,0,'CLOSED','2025-02-01')")
    return path


def test_pages_and_release_connection(database):
    for url, text in [("/", "Loan register"), ("/?status=ACTIVE&currency=GBP&loan_id=L1", "1 loans"), ("/loan?id=L1", "1.273400"), ("/client?id=C01", "1,273.40"), ("/loan?id=L2", "Not available")]:
        status, html = render(url)
        assert status == 200
        assert text in html
        assert 'charset="utf-8"' in html
    with duckdb.connect(str(database)) as db:
        db.execute("UPDATE sor_loans SET balance_usd=1300 WHERE loan_id='L1'")
    assert "1,300.00" in render("/loan?id=L1")[1]


@pytest.mark.parametrize("url", ["/loan?id=absent", "/client?id=absent"])
def test_absent_record(database, url):
    status, html = render(url)
    assert status == 200
    assert "No records found" in html


def test_missing_table_and_missing_database(tmp_path, monkeypatch):
    path = tmp_path / "missing.duckdb"
    monkeypatch.setenv("RECON_DB", str(path))
    assert render("/")[0] == 503
    assert not path.exists()
    with duckdb.connect(str(path)):
        pass
    status, html = render("/")
    assert status == 503
    assert "Data refreshing" in html
    assert "Run the pipeline" in html


def test_locked_database(database, monkeypatch):
    def locked(*args, **kwargs):
        assert kwargs["read_only"] is True
        raise duckdb.IOException("locked")
    monkeypatch.setattr("ui.server.duckdb.connect", locked)
    assert render("/loan?id=L1")[0] == 503


def test_empty_table_and_unknown_page(database):
    with duckdb.connect(str(database)) as db:
        db.execute("DELETE FROM sor_loans")
    assert "No records found" in render("/")[1]
    assert render("/unknown")[0] == 404


def test_filters_and_escaped_search(database):
    html = render("/?currency=GBP")[1]
    assert "L1</a>" in html and "L2</a>" not in html
    assert "No records found" in render("/?status=DELINQUENT")[1]
    assert "No records found" in render("/?loan_id=xyz")[1]
    assert "&lt;script&gt;" in render("/?loan_id=%3Cscript%3E")[1]
