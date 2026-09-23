# Sprint 1 Retrospective — Day 01–07

## Sprint Goal
Build and validate the Nifty100 Financial Intelligence ETL pipeline, SQLite database, data-quality framework, and exploratory SQL analysis.

## What Went Well
- Project setup and data ingestion were completed.
- SQLite database was successfully populated with 92 valid companies.
- Foreign-key validation passed with 0 violations.
- DQ-01 to DQ-16 validation was implemented.
- Day 06 manual review of five companies was completed.
- ATGL, JIOFIN, and SBIN data gaps were investigated and found to be source-data availability issues rather than loader bugs.
- 35 ETL unit tests passed with 0 failures.
- Ten exploratory SQL queries were completed.

## Challenges
- Duplicate company IDs were identified during validation.
- A foreign-key mismatch involving `market_cap` was identified and fixed.
- Some companies have incomplete historical financial data in the source files.

## What We Learned
- Source-data completeness must be checked separately from ETL correctness.
- Foreign-key validation is important after schema or loader changes.
- Manual review helps distinguish genuine source-data limitations from ETL problems.

## Improvements
- Add stronger source-data completeness reporting.
- Keep manual-review findings in a dedicated report.
- Document data-quality exceptions clearly.

## Sprint Outcome
Sprint 1 objectives were completed and the project is ready for the next stage of analytics and application development.

## Next Sprint
- Build financial analytics and derived metrics.
- Develop dashboard/API components.
- Continue testing and documentation.
