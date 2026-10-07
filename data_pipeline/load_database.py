'''
creates the database in sql from excel
'''


import sqlite3

import pandas as pd

USED_DISEASES = ["MEASLES", "RUBELLA", "PERTUSSIS", "DIPHTHERIA"]


def print_junk_report(coverage, cases):
    wuenic = coverage[coverage.COVERAGE_CATEGORY == "WUENIC"]
    coverage_countries = wuenic[wuenic.GROUP == "COUNTRIES"]
    useful_coverage = coverage_countries[coverage_countries.YEAR.notna() & coverage_countries.COVERAGE.notna()]
    print(f"coverage: {len(coverage):,} rows -> WUENIC only {len(wuenic):,} -> countries only "
          f"{len(coverage_countries):,} -> with a year and a value {len(useful_coverage):,}")

    case_countries = cases[cases.GROUP == "COUNTRIES"]
    useful_cases = case_countries[case_countries.YEAR.notna() & case_countries.CASES.notna()]
    used = useful_cases[useful_cases.DISEASE.isin(USED_DISEASES)]
    print(f"cases: {len(cases):,} rows -> countries only {len(case_countries):,} -> with a year and a count "
          f"{len(useful_cases):,} -> diseases we use {len(used):,}")

# Opening the Excel files takes long
coverage = pd.read_excel("data/raw/coverage-data.xlsx", sheet_name="Data")
cases = pd.read_excel("data/raw/reported-cases-data.xlsx", sheet_name="Data")
print_junk_report(coverage, cases)

db = sqlite3.connect("data/who_data.db")

# Each Excel sheet becomes a table in the database
coverage.to_sql("coverage", db, if_exists="replace", index=False)
cases.to_sql("cases", db, if_exists="replace", index=False)

# Our own small table: which vaccine protects against which disease
db.executescript("""
    DROP TABLE IF EXISTS vaccine_for;
    CREATE TABLE vaccine_for (DISEASE TEXT, ANTIGEN TEXT);
    INSERT INTO vaccine_for VALUES
        ('MEASLES', 'MCV1'),
        ('RUBELLA', 'RCV1'),
        ('PERTUSSIS', 'DTPCV3'),
        ('DIPHTHERIA', 'DTPCV3');
""")

db.commit()
db.close()
print("Saved data/who_data.db")