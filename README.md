# lending-sor-extract
Reads: data/sor_loans.csv; config.json controls the booking cut-off.
Writes: sor_loans and stg_loans.
Owns: Lending core extraction and source snapshot.
Run: pip install -r requirements.txt; make run; make test. Shared DB: $RECON_DB (default ~/lending-demo/lending.duckdb); tables are replaced on each run.
