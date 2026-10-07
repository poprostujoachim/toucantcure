import glob
import json
import os

import pytest

from game.waves import level_scaling

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CITIES = ["Leiden", "Tallinn", "Istanbul", "Sparta", "Wloclawek", "Dusseldorf", "Avignon"]
DISEASES = ["MEASLES", "RUBELLA", "PERTUSSIS", "DIPHTHERIA", "MUMPS"]


def no_nan(value):
    raise ValueError(f"{value} is not allowed in a level file")


def load(city):
    with open(os.path.join(ROOT, "levels", f"{city}.json"), encoding="utf-8") as f:
        return json.load(f, parse_constant=no_nan)


def test_one_file_per_city():
    names = sorted(os.path.basename(path)[:-5] for path in glob.glob(os.path.join(ROOT, "levels", "*.json")))
    assert names == sorted(CITIES)


@pytest.mark.parametrize("city", CITIES)
def test_level_values_are_valid(city):
    level = load(city)
    assert level["city"] == city
    assert level["country"]
    assert 1980 <= level["year"] <= 2025
    assert level["disease"] in DISEASES
    assert level["cases"] > 0
    assert 0 <= level["vaccine_coverage"] <= 1
    assert 0 <= level["outbreak_strength"] <= 1


def test_outbreak_strength_is_a_rank():
    strengths = sorted(load(city)["outbreak_strength"] for city in CITIES)
    assert strengths == [round(i / (len(CITIES) - 1), 2) for i in range(len(CITIES))]


@pytest.mark.parametrize("city", CITIES)
def test_game_turns_levels_into_sane_numbers(city):
    scaling = level_scaling(load(city))
    assert 0.03 <= scaling["cure_chance"] <= 0.15
    assert 0.8 <= scaling["enemy_mult"] <= 1.6
    assert 0.9 <= scaling["speed_mult"] <= 1.1
