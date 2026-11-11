import os
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit

import duckdb

TITLE = "Loan Servicing"
TABLE = "sor_loans"
PORT = 8101
STYLE = """*{box-sizing:border-box}body{margin:0;color:#203342;background:#edf1f4;font:14px Arial,sans-serif}a{color:#11696c;text-decoration:none}a:hover{text-decoration:underline}a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid #208fbb;outline-offset:3px}header{display:flex;align-items:center;gap:34px;background:#233a49;color:white;padding:18px 28px}.brand{color:white;font-size:20px;font-weight:bold;letter-spacing:-.5px}.brand span{font-weight:normal}.app{border-left:1px solid #637582;padding-left:28px;font-size:17px}.readonly{margin-left:auto;font-size:12px;color:#d1e0e7}nav{display:flex;align-items:center;justify-content:space-between;padding:10px 28px;background:white;border-bottom:1px solid #c9d3da}nav form{display:flex;align-items:center;gap:10px}nav label{font-size:12px}input,select,button{font:inherit;padding:9px 11px;border:1px solid #b9c7cf;border-radius:3px;background:white;color:inherit}button{background:#176d71;color:white;border-color:#176d71;cursor:pointer}main{max-width:1480px;margin:auto;padding:28px}h1{font-size:29px;letter-spacing:-.7px;margin:5px 0 8px}h2{font-size:20px;margin:0 0 8px}.context{color:#526675;margin:0;font-size:12px}.heading{display:flex;justify-content:space-between;align-items:center;margin-bottom:22px}.count{font-size:13px;padding:8px 12px;border:1px solid #c5d1d8;background:#fff}.filters{display:flex;gap:14px;align-items:end;padding:16px;background:#dde6eb;border:1px solid #c5d1d8;margin-bottom:20px}.filters label{display:flex;flex-direction:column;gap:6px;font-size:12px}.filters a{padding:10px}section,.table-wrap{background:white}section{border:1px solid #cbd5dc}.table-wrap{overflow:auto}table{border-collapse:collapse;width:100%;white-space:nowrap;font-size:13px}th{text-align:left;color:#4c6170;background:#e5ecf0;font-weight:normal;padding:12px 15px;border-bottom:1px solid #bac8d1}td{padding:11px 15px;border-bottom:1px solid #dbe3e8}tbody tr:nth-child(even){background:#f6f8fa}tbody tr:hover{background:#edf5f6}.number{text-align:right;font-variant-numeric:tabular-nums}.section-title{padding:15px 20px;font-weight:bold;border-bottom:1px solid #cbd5dc}.section-title span{float:right;font-weight:normal;font-size:12px;color:#526675}dl{margin:0;display:grid;grid-template-columns:repeat(3,1fr)}dl>div{padding:22px;border-bottom:1px solid #e0e6eb}dt{font-size:12px;color:#5c707e;margin-bottom:9px}dd{margin:0;font-size:19px;font-variant-numeric:tabular-nums}.empty{padding:45px;margin-top:20px}.portfolio{display:flex;justify-content:space-between;align-items:center;margin:30px 0 24px}.portfolio p{color:#526675}.total{text-align:right}.total span{display:block;color:#526675;margin-bottom:8px}.total strong{font-size:32px;font-weight:normal;font-variant-numeric:tabular-nums}footer{max-width:1480px;margin:25px auto;padding:0 28px 20px;font-size:11px;color:#5c707e}footer span{float:right}@media(max-width:700px){header{flex-wrap:wrap;gap:14px;padding:18px}.readonly{margin-left:0}.app{padding-left:14px}nav{align-items:start;gap:15px;flex-direction:column;padding:16px}nav form{flex-wrap:wrap}main{padding:18px}.filters{flex-wrap:wrap}dl{grid-template-columns:repeat(2,1fr)}.portfolio{align-items:start;gap:18px;flex-direction:column}.total{text-align:left}footer span{display:block;float:none;margin-top:10px}}"""
LABELS = {
    "loan_id": "Loan ID", "client_id": "Client ID", "product_code": "Product code",
    "currency": "Currency", "balance": "Local balance", "balance_usd": "Balance USD",
    "status": "Status", "booking_date": "Booking date",
}


def esc(value):
    return escape(str(value), quote=True)


def money(value):
    return "—" if value is None else f"{value:,.2f}"


def link(kind, identifier):
    return f'<a href="/{kind}?id={quote(str(identifier), safe="")}">{esc(identifier)}</a>'


def page(title, body):
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} | {TITLE}</title><style>{STYLE}</style></head>
<body><header><a class="brand" href="/">Northhaven <span>Bank</span></a>
<div class="app">{TITLE}</div><span class="readonly">Read-only workspace</span></header>
<nav><a href="/">Loan register</a>
<form action="/loan" method="get"><label for="quick">Find a loan</label>
<input id="quick" name="id" placeholder="Loan ID, e.g. L0016" required>
<button>Open loan</button></form></nav>
<main>{body}</main><footer>Northhaven Bank · Fictional demonstration data
<span>Refresh the page to load the latest data</span></footer></body></html>"""


def holdings(rows):
    columns = ["loan_id", "client_id", "product_code", "currency", "balance", "balance_usd", "status", "booking_date"]
    header = "".join(f'<th scope="col">{LABELS[c]}</th>' for c in columns)
    body = ""
    for row in rows:
        cells = []
        for col in columns:
            value = row.get(col, "")
            content = (link("loan", value) if col == "loan_id" else
                       link("client", value) if col == "client_id" else
                       esc(money(value)) if col in ("balance", "balance_usd") else esc(value))
            cls = ' class="number"' if col in ("balance", "balance_usd") else ""
            cells.append(f"<td{cls}>{content}</td>")
        body += "<tr>" + "".join(cells) + "</tr>"
    return f'<div class="table-wrap"><table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table></div>'


def empty():
    return '<section class="empty"><h2>No records found</h2><p>Check the identifier or adjust your filters.</p><a href="/">Return to the directory</a></section>'


def render_rows(url, rows):
    request = urlsplit(url)
    query = parse_qs(request.query)
    get = lambda key: query.get(key, [""])[0].strip()
    identifier = get("id")
    if request.path == "/loan":
        selected = [r for r in rows if r["loan_id"] == identifier]
        heading = f'<div class="heading"><div><p class="context">Loan record</p><h1>{esc(identifier)}</h1></div><a class="back" href="/">Back to directory</a></div>'
        if not selected:
            return 200, page(identifier, heading + empty())
        row = selected[0]
        fields = ""
        for key, value in row.items():
            content = (link("client", value) if key == "client_id" else
                       esc(money(value)) if key in ("balance", "balance_usd") else esc(value))
            fields += f'<div><dt>{esc(LABELS.get(key, key))}</dt><dd>{content}</dd></div>'
        rate = "Not available" if not row["balance"] else f'{row["balance_usd"] / row["balance"]:.6f}'
        fields += f'<div><dt>Implied FX rate</dt><dd>{rate}</dd></div>'
        body = heading + f'<section class="record"><div class="section-title">Account particulars <span>{esc(row["status"])}</span></div><dl>{fields}</dl></section>'
        return 200, page(identifier, body)
    if request.path == "/client":
        selected = [r for r in rows if r["client_id"] == identifier]
        name = identifier
        body = f'<div class="heading"><div><p class="context">Client portfolio / {esc(identifier)}</p><h1>{esc(name)}</h1></div><a class="back" href="/">Back to directory</a></div>'
        if selected:
            total = sum(r["balance_usd"] for r in selected)
            body += f'<div class="portfolio"><div><h2>Lending holdings</h2><p>{len(selected)} rows · Values in account currency unless noted</p></div><div class="total"><span>Total USD</span><strong>{money(total)}</strong></div></div><section>{holdings(selected)}</section>'
        else:
            body += empty()
        return 200, page(name, body)
    if request.path != "/":
        return 404, page("Page not found", '<h1>Page not found</h1><a href="/">Return to the directory</a>')
    options = ""
    for field in ("status", "currency"):
        choices = "".join(f'<option value="{esc(v)}"{" selected" if get(field) == v else ""}>{esc(v)}</option>'
                          for v in sorted({r[field] for r in rows}))
        options += f'<label>{LABELS[field]}<select name="{field}"><option value="">All {field}</option>{choices}</select></label>'
    filters = f'<form class="filters" method="get"><label>Loan ID<input name="loan_id" value="{esc(get("loan_id"))}" placeholder="Search loan ID"></label>{options}<button>Apply filters</button><a href="/">Clear</a></form>'
    selected = [r for r in rows if (not get("loan_id") or get("loan_id").upper() in r["loan_id"].upper())
                and (not get("status") or r["status"] == get("status"))
                and (not get("currency") or r["currency"] == get("currency"))]
    body = f'<div class="heading"><div><p class="context">Servicing operations</p><h1>Loan register</h1></div><span class="count">{len(selected)} loans</span></div>{filters}'
    body += holdings(selected) if selected else empty()
    return 200, page(TITLE, body)


def render(url):
    path = Path(os.environ.get("RECON_DB", "~/lending-demo/lending.duckdb")).expanduser()
    try:
        with duckdb.connect(str(path), read_only=True) as db:
            result = db.execute(f"SELECT * FROM {TABLE} ORDER BY loan_id")
            columns = [c[0] for c in result.description]
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
    except duckdb.Error:
        return 503, page("Data refreshing", '<section class="empty"><h1>Data refreshing</h1><p>Run the pipeline if data is not yet available, then refresh this page.</p><a href="/">Try again</a></section>')
    return render_rows(url, rows)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        status, html = render(self.path)
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        if status == 503:
            self.send_header("Retry-After", "3")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"{TITLE}: http://127.0.0.1:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
