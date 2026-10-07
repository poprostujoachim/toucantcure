import json
import os
import sqlite3

import pytest

from data_pipeline.build_levels import DATABASE, LEVELS_DIR, biggest_outbreak, build_levels

pytestmark = pytest.mark.skipif(not os.path.exists(DATABASE),
                                reason="run python data_pipeline/load_database.py first")


@pytest.fixture(scope="module")
def db():
    connection = sqlite3.connect(DATABASE)
    yield connection
    connection.close()


def coverage(db, code, antigen, year):
    row = db.execute("SELECT COVERAGE FROM coverage WHERE CODE = ? AND ANTIGEN = ? AND YEAR = ? "
                     "AND COVERAGE_CATEGORY = 'WUENIC'", (code, antigen, year)).fetchone()
    return row[0]


def cases(db, code, disease, year):
    return db.execute("SELECT CASES FROM cases WHERE CODE = ? AND DISEASE = ? AND YEAR = ?",
                      (code, disease, year)).fetchone()[0]


def test_known_values_from_the_raw_readme(db):
    assert coverage(db, "GHA", "MCV1", 1980) == 16


def test_known_outbreaks(db):
    assert cases(db, "NLD", "MEASLES", 2013) == 2632
    assert coverage(db, "NLD", "MCV1", 2013) == 96
    assert cases(db, "FRA", "MEASLES", 1991) == 156849


def test_biggest_outbreak_picks(db):
    assert biggest_outbreak(db, "Leiden", "NLD", "Netherlands") == {
        "city": "Leiden", "country": "Netherlands", "year": 2024, "disease": "PERTUSSIS",
        "cases": 18180, "vaccine_coverage": 0.91,
    }
    assert biggest_outbreak(db, "Avignon", "FRA", "France")["cases"] == 156849


def test_level_files_are_up_to_date(db):
    for level in build_levels(db):
        with open(os.path.join(LEVELS_DIR, f"{level['city']}.json"), encoding="utf-8") as f:
            assert json.load(f) == level, f"levels/{level['city']}.json is out of date: run build_levels.py"
