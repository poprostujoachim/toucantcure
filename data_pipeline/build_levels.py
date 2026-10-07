import json
import os
import sqlite3

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

db = sqlite3.connect("data/who_data.db")

levels = []
for city, (code, country) in CITIES.items():
    year, disease, cases, coverage = db.execute(BIGGEST_OUTBREAK, (code,)).fetchone()
    levels.append({
        "city": city,
        "country": country,
        "year": int(year),
        "disease": disease,
        "cases": int(cases),
        "vaccine_coverage": coverage / 100,
    })

db.close()

# Outbreak strength: smallest outbreak of our cities = 0.0, biggest = 1.0
all_cases = sorted([level["cases"] for level in levels])
for level in levels:
    position = all_cases.index(level["cases"])
    level["outbreak_strength"] = round(position / (len(all_cases) - 1), 2)

# Create the levels folder if it doesn't exist
os.makedirs("levels", exist_ok=True)

for level in levels:
    with open(f"levels/{level['city']}.json", "w") as f:
        json.dump(level, f, indent=2)
    print(level)