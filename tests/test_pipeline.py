import duckdb
import pytest

from pipeline import run


@pytest.fixture
def database(tmp_path, monkeypatch):
    path = tmp_path / "nested" / "test.duckdb"
    monkeypatch.setenv("RECON_DB", str(path))
    return path


def test_extract_schema_and_repeatability(database):
    run()
    with duckdb.connect(str(database)) as db:
        source = db.execute("SELECT * FROM sor_loans ORDER BY loan_id").fetchall()
        first = db.execute("SELECT * FROM stg_loans ORDER BY loan_id").fetchall()
        assert len(source) == 200
        assert len(first) > 100
        assert db.execute("SELECT count(*) FROM stg_loans WHERE status = 'CLOSED'").fetchone()[0] == 0
        assert [c[0] for c in db.execute("SELECT * FROM stg_loans").description] == [
            "loan_id", "client_id", "product_code", "currency", "balance",
            "balance_usd", "status", "booking_date"]
    run()
    with duckdb.connect(str(database)) as db:
        assert db.execute("SELECT * FROM stg_loans ORDER BY loan_id").fetchall() == first
        assert db.execute("SELECT * FROM sor_loans ORDER BY loan_id").fetchall() == source


def test_source_missing(database, monkeypatch, tmp_path):
    monkeypatch.setattr("pipeline.ROOT", tmp_path)
    (tmp_path / "config.json").write_text('{"cutoff_date": "2025-03-31"}')
    with pytest.raises(duckdb.IOException):
        run()
