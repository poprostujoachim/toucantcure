import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE = os.path.join(ROOT, "data", "who_data.db")
LEVELS_DIR = os.path.join(ROOT, "levels")

# City name
CITIES = {
    "Leiden": ("NLD", "Netherlands"),
    "Tallinn": ("EST", "Estonia"),
    "Istanbul": ("TUR", "Turkey"),
    "Sparta": ("GRC", "Greece"),
    "Wloclawek": ("POL", "Poland"),
    "Dusseldorf": ("DEU", "Germany"),
    "Avignon": ("FRA", "France"),
}

BIGGEST_OUTBREAK = """
SELECT cases.YEAR, cases.DISEASE, cases.CASES, coverage.COVERAGE
FROM cases
JOIN vaccine_for ON vaccine_for.DISEASE = cases.DISEASE
JOIN coverage ON coverage.CODE = cases.CODE
             AND coverage.YEAR = cases.YEAR
             AND coverage.ANTIGEN = vaccine_for.ANTIGEN
WHERE cases.CODE = ?
  AND cases.CASES IS NOT NULL
  AND coverage.COVERAGE_CATEGORY = 'WUENIC'
  AND coverage.COVERAGE IS NOT NULL
ORDER BY cases.CASES DESC
LIMIT 1
"""


def biggest_outbreak(db, city, code, country):
    year, disease, cases, coverage = db.execute(BIGGEST_OUTBREAK, (code,)).fetchone()
    return {
        "city": city,
        "country": country,
        "year": int(year),
        "disease": disease,
        "cases": int(cases),
        "vaccine_coverage": coverage / 100,
    }


def add_outbreak_strength(levels):
    # Outbreak strength: smallest outbreak of our cities = 0.0, biggest = 1.0
    all_cases = sorted([level["cases"] for level in levels])
    for level in levels:
        position = all_cases.index(level["cases"])
        level["outbreak_strength"] = round(position / (len(all_cases) - 1), 2)


def build_levels(db):
    levels = [biggest_outbreak(db, city, code, country) for city, (code, country) in CITIES.items()]
    add_outbreak_strength(levels)
    return levels


def print_summary(levels):
    print(f"{'city':<11} {'disease':<11} {'year':>4} {'cases':>9} {'coverage':>9} {'strength':>9}")
    for level in levels:
        print(f"{level['city']:<11} {level['disease']:<11} {level['year']:>4} {level['cases']:>9,} "
              f"{level['vaccine_coverage']:>9.0%} {level['outbreak_strength']:>9}")


def main():
    if not os.path.exists(DATABASE):
        sys.exit("No database yet: run python data_pipeline/load_database.py first.")
    db = sqlite3.connect(DATABASE)
    levels = build_levels(db)
    db.close()

    # Create the levels folder if it doesn't exist
    os.makedirs(LEVELS_DIR, exist_ok=True)

    for level in levels:
        with open(os.path.join(LEVELS_DIR, f"{level['city']}.json"), "w") as f:
            json.dump(level, f, indent=2)
    print_summary(levels)


if __name__ == "__main__":
    main()
