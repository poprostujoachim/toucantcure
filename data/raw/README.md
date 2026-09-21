claude generated instructions for interpreting the data
have fun



# Raw data

Downloaded 21 September 2026 from the
[WHO Immunization Data portal](https://immunizationdata.who.int/global)
and [Our World in Data](https://ourworldindata.org/grapher/global-vaccination-coverage).

**Do not edit these files.** They are the unmodified exports. Everything the game
uses gets generated from them by `data_pipeline/` and written to `levels/`.
The game itself never reads this folder and never touches the network.

## The files

| File | Rows | What it is |
|---|---|---|
| `coverage-data.xlsx` | 396,212 | Vaccination coverage %, by country / year / vaccine |
| `reported-cases-data.xlsx` | 90,400 | Reported disease cases, by country / year / disease |
| `global-vaccination-coverage.csv` | 9,202 | Our World in Data mirror. Only here because it has polio — see below |

Both spreadsheets have the real table on the sheet named `Data`, header in row 1.
The other sheets (`Reference`, `Reference (WUENIC)`, ...) are lookup tables we don't use.

Both cover **1980–2025**.

## Three traps

**1. Filter `COVERAGE_CATEGORY` to `WUENIC`.**
The coverage file stacks five different estimates on top of each other as separate
rows: `ADMIN`, `OFFICIAL`, `WUENIC`, `HPV`, `PAB`. If you don't filter, you get
about four rows per country/year/vaccine and your numbers will be wrong in a way
that doesn't look wrong. `WUENIC` is the WHO/UNICEF harmonised estimate — it's the
one that's consistent across all years, so it's the one we use.

**2. Filter `GROUP` to `COUNTRIES`.**
Rows for `GLOBAL`, `WHO_REGIONS`, `UNICEF_REGIONS`, `WB_LONG` and others are mixed
in with the country rows. Any average you take without filtering is wrong.

**3. Drop the footer row.**
Both files end with a junk row (`Created: 2026-21-09 12:00 UTC` in the `GROUP`
column) that has no year. Dropping rows where `YEAR` is null removes it.

## Vaccine codes

The `ANTIGEN` column uses codes, not names. The ones we care about:

| Code | Vaccine | Diseases it maps to | Data from |
|---|---|---|---|
| `MCV1` | Measles, 1st dose | `MEASLES` | 1980 |
| `DTPCV3` | Diphtheria/tetanus/pertussis, 3rd dose | `DIPHTHERIA`, `PERTUSSIS`, `TTETANUS`, `NTETANUS` | 1980 |
| `RCV1` | Rubella, 1st dose | `RUBELLA`, `CRS` | 1980 |
| `BCG` | Tuberculosis | (no cases column) | 1980 |
| `Pol3` | Polio, 3rd dose | `POLIO` | 1980, **CSV only** |

It is `DTPCV3`, not `DTP3`.

Vaccines that only exist from the 2000s (`ROTAC`, `PCVC`, `HIB3`, `HEPB3`, `MCV2`,
`IPV1`, `IPVC`) can't be used for early levels — there's simply no data before the
vaccine existed.

**The polio catch:** `coverage-data.xlsx` has no `Pol3` at all. Its only polio
vaccines are `IPV1` (2015+) and `IPVC` (2021+). `global-vaccination-coverage.csv`
is the only file here with polio coverage going back to 1980, which is the entire
reason it's committed. For polio levels, use the CSV. For everything else, the xlsx.

**Netherlands has no `BCG` row.** 170 countries do; the Netherlands doesn't
vaccinate for TB universally, so there's no tuberculosis level in Dutch cities.

## Loading it correctly

```python
import pandas as pd

cov = pd.read_excel("data/raw/coverage-data.xlsx", sheet_name="Data")
cov = cov[
    (cov.COVERAGE_CATEGORY == "WUENIC")
    & (cov.GROUP == "COUNTRIES")
    & cov.YEAR.notna()
]

cases = pd.read_excel("data/raw/reported-cases-data.xlsx", sheet_name="Data")
cases = cases[(cases.GROUP == "COUNTRIES") & cases.YEAR.notna()]

# measles coverage in Ghana, 1980
cov[(cov.CODE == "GHA") & (cov.ANTIGEN == "MCV1") & (cov.YEAR == 1980)].COVERAGE
# -> 16.0
```

Reading the 17 MB spreadsheet takes a few seconds, which is why the pipeline runs
offline and the game only ever loads the small JSON files in `levels/`.

Needs `pandas` and `openpyxl`.

## Citing this

The source is WHO/UNICEF, not Our World in Data — OWID just republishes it. Cite as:

> WHO/UNICEF Estimates of National Immunization Coverage (WUENIC), 2025 revision.
> WHO Immunization Data portal, retrieved 21 September 2026.
