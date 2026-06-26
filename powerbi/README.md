# Corvus Power BI Report Pack

This folder contains the Phase 4 report assets for Power BI.

Power BI Desktop is not installed in this development environment, so the binary
`.pbix` export cannot be produced here. The report pack is still built against
the Corvus SQLite database and includes the data exports, SQL, theme, DAX
measures, manifest, and preview screenshots needed to assemble/export the PBIX
in Desktop.

## Build The Report Data

```bash
python scripts/export_powerbi_dataset.py --refresh-db
```

Outputs:

- `powerbi/export/*.csv`
- `powerbi/screenshots/*.png`

## Power BI Desktop Setup

1. Open Power BI Desktop.
2. Import the CSV files from `powerbi/export/`.
3. Import `powerbi/corvus_powerbi_theme.json`.
4. Build the pages listed in `powerbi/report_manifest.json`.
5. Add the measures from `powerbi/measures/corvus_measures.dax`.
6. Save as `powerbi/corvus.pbix`.

The report should keep the same v1 scope:

- Drive health
- Fuel trim
- DTC evidence

Do not add placeholder or coming-soon pages.
