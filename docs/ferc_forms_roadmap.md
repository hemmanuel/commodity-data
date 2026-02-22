# FERC Forms Roadmap

Goal: make the commodity database rich with historical FERC context—storage, tariffs, pipelines, transactions, and operations. This doc tracks which forms we want, where bulk data exists, and what’s next.

## Forms we want (priority)

| Form | Name | Data type | Bulk download status | Ingestion status |
|------|------|-----------|----------------------|------------------|
| **Form 2** | Major Natural Gas Pipeline Annual Report | VFP ZIP (DBF) | ✅ `forms.ferc.gov/f2allyears/f2_YYYY.zip` (1996–2021) | ✅ Ingested (respondents, income, balance sheet, cash flow) |
| **Form 2A** | Non-major Natural Gas Pipeline Annual Report | VFP (same family as Form 2) | 🔍 Same historical page as Form 2/3-Q; no `f2a_YYYY.zip` found at f2allyears | ❌ Need URL or eLibrary scrape |
| **Form 3-Q** | Quarterly Financial Report (Electric & Gas) | VFP | 🔍 Same page; no `f3q_YYYY.zip` at f2allyears | ❌ Need URL or eLibrary scrape |
| **Form 11** | Quarterly Statement of Monthly Data | — | ❓ eLibrary / FERC download database | ❌ To research |
| **Form 537** | Multiple (Annual Certificate, 311 Facility Activities, Bypass, Semi-annual Storage Report) | — | ❓ eLibrary | ❌ To research; storage report historically valuable |
| **549B** | Index of Customers; Capacity Report (§284.13) | — | ❓ eLibrary / data.ferc.gov | ❌ To research |
| **Form 549D** | Quarterly Transportation & Storage (Intrastate/Hinshaw) | — | eForms public (eformspublic.ferc.gov) | ❌ To research |
| **Form 552** | Annual Report of Natural Gas Transactions | CSV / API | ✅ data.ferc.gov (Form 552 Master, Form 552 Page 3) | ✅ Download + ingest (ferc_form552_master) |
| **Form 567** | System Flow Diagrams | — | ❓ eLibrary | ❌ To research |
| **Form 576** | Report of Service Interruptions or Damage to Facilities | — | ❓ eLibrary | ❌ To research |
| **Form 577** | Annual Report of Replacement of Certificated Facilities | — | ❓ eLibrary | ❌ To research |
| **Form 592** | Marketing Affiliates of Interstate Pipelines | — | ❓ eLibrary | ❌ To research |

## Other valuable FERC context

- **Tariffs**: FERC eLibrary (eTariff, rate schedules).
- **Underground storage**: Historical “Underground Natural Gas Storage Report” (semi-annual) was eliminated by Order No. 757 (2012); older data may exist in eLibrary. EIA remains the main source for ongoing storage time series.
- **Orders**: Order No. 678/678-A (storage), 757 (reporting changes)—useful for interpreting which reports exist for which years.

## Bulk data sources (known)

1. **forms.ferc.gov**  
   - Form 2: `https://forms.ferc.gov/f2allyears/f2_YYYY.zip` (1996–2021).  
   - Form 2A / 3-Q: listed on [Form 2, 2A, & 3-Q (Gas) Historical VFP Data](https://www.ferc.gov/industries-data/natural-gas/industry-forms/form-2-2a-3-q-gas-historical-vfp-data) but direct ZIP URLs not yet found; may require manual download or different path.

2. **data.ferc.gov**  
   - Form 552: [Form No. 552 - Download Data](https://data.ferc.gov/form-no.-552-download-data) — Form 552 Master Table, Form 552 Page 3 (CSV/API).  
   - Data catalog (Natural Gas): [data.ferc.gov/datacatalog/?industry=Natural+Gas](https://data.ferc.gov/datacatalog/?industry=Natural+Gas).

3. **eLibrary / eForms**  
   - [eLibrary](https://elibrary.ferc.gov/) — filings by form, company, date.  
   - [eFormspublic.ferc.gov](https://eformspublic.ferc.gov/) — e.g. Form 549D.

## Next steps

1. **Form 552**: Run download (script updated); add `ingest_ferc_form552.py` (or extend existing ingest) and wire to DuckDB + API/dashboard.
2. **Form 2A / 3-Q**: Confirm bulk ZIP URL pattern (e.g. from FERC page or support Form2@ferc.gov); add to `download_ferc.py` and ingestion.
3. **Forms 11, 537, 549B, 549D, 567, 576, 577, 592**: Check FERC download database and eLibrary for bulk or per-filing access; add to this table and to download/ingest as URLs or APIs are found.
4. **Tariffs / storage**: Document eLibrary eTariff and any storage report archives; add to pipeline when we have a clear source.

---

*Updated from project goal: rich historical context; no data left on the table where FERC provides bulk access.*
