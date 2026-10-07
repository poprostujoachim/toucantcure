import copy
import json
import os

SAVE_PATH = os.path.join(os.path.expanduser("~"), ".toucantcure", "save.json")

DEFAULT_SAVE = {
    "version": 1,
    "duckbucks": 0,
    "boss_items": {"toucan_feather": 0, "golden_beak": 0, "royal_crest": 0},
    "weapons": {"syringe": 1, "spray": 1, "defibrillator": 0, "iv_bag": 0, "scalpel": 0},
    "permanent": {"max_hp": 0, "armor": 0, "move_speed": 0, "cure": 0, "extra_life": 0},
    "cities_unlocked": ["Leiden"],
    "cities_cured": {"Leiden": 0},
    "difficulty_unlocked": 1,
    "endless_unlocked": False,
    "cosmetics_owned": [],
    "cosmetic_equipped": None,
    "best_time": {},
    "stats": {"runs": 0, "kills": 0, "wins": 0},
    "settings": {"music_volume": 0.6, "sfx_volume": 0.8, "fullscreen": False, "damage_numbers": True,
                 "screen_shake": True},
}


def fresh():
    return copy.deepcopy(DEFAULT_SAVE)


def merge(defaults, data):
    result = copy.deepcopy(defaults)
    for key, value in data.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = value
    return result


def load(path=None):
    path = path or SAVE_PATH
    try:
        with open(path, encoding="utf-8") as f:
            return merge(DEFAULT_SAVE, json.load(f))
    except FileNotFoundError:
        return fresh()
    except (OSError, ValueError, AttributeError):
        print(f"Warning: {path} is broken, starting a fresh save (the old one is kept as {path}.bad)")
        try:
            os.replace(path, path + ".bad")
        except OSError:
            pass
        return fresh()


def save(data, path=None):
    path = path or SAVE_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp_path = path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(temp_path, path)
