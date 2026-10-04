import json
import os

LEVELS_DIR = os.path.join(os.path.dirname(__file__), "..", "levels")


def load_level(city):
    with open(os.path.join(LEVELS_DIR, city + ".json")) as f:
        return json.load(f)