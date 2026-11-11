# lending-sor-extract
Reads: data/sor_loans.csv; config.json controls the booking cut-off.
Writes: sor_loans and stg_loans.
Owns: Lending core extraction and source snapshot.
Run: pip install -r requirements.txt; make run; make test. Shared DB: $RECON_DB (default ~/lending-demo/lending.duckdb); tables are replaced on each run.

## Loan Servicing UI
Run `make ui` and open http://127.0.0.1:8101. Filter the loan register by status,
currency or loan ID; open a loan for all account fields and its implied FX rate,
or follow its client ID to that client's loans. This read-only UI reads only
`sor_loans` from `$RECON_DB` (same default as above), using a short-lived connection
per request. Run the pipeline first; refresh the page after a load. If data is
unavailable or refreshing, the page asks you to retry. Stop the server with Ctrl-C.
