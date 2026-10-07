import pygame

TITLE = "TouCan'tCure"
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
MAX_DT = 0.05

PIXEL_SCALE = 3
TILE_SIZE = 16 * PIXEL_SCALE

ARENA_WIDTH = 2400
ARENA_HEIGHT = 2400
WALL_THICKNESS = 40

BACKGROUND_COLOR = (15, 25, 18)
WALL_EDGE_COLOR = (10, 18, 12)
TEXT_COLOR = (240, 240, 240)
DODGE_TEXT_COLOR = (170, 220, 255)

DEBUG = True
ADMIN_SPAWN_DISTANCE = 300
KEY_STAT_SHEET = pygame.K_TAB

KEYS_UP = (pygame.K_w, pygame.K_z, pygame.K_UP)
KEYS_DOWN = (pygame.K_s, pygame.K_DOWN)
KEYS_LEFT = (pygame.K_a, pygame.K_q, pygame.K_LEFT)
KEYS_RIGHT = (pygame.K_d, pygame.K_RIGHT)
KEY_DASH = pygame.K_SPACE

PLAYER_STATS = {
    "max_hp":            (100,  1,    None),
    "move_speed":        (220,  50,   None),
    "armor":             (0,    0,    None),
    "regen":             (0.0,  0,    None),
    "dodge_chance":      (0.0,  0,    0.4),
    "damage":            (1.0,  0,    None),
    "crit_rate":         (0.05, 0,    1),
    "crit_damage":       (1.5,  1,    None),
    "attack_speed":      (1.0,  0.1,  None),
    "projectile_speed":  (1.0,  0.1,  None),
    "extra_projectiles": (0,    0,    None),
    "pickup_range":      (90,   0,    None),
    "xp_gain":           (1.0,  0,    None),
    "luck":              (1.0,  0,    None),
    "cure_chance":       (0.0,  0,    0.5),
    "soap_slow":         (0.0,  0,    0.4),
    "extra_lives":       (0,    0,    None),
}
ARMOR_SCALE = 100
MIN_COOLDOWN = 0.05
PLAYER_RADIUS = 18
PLAYER_SPRITE_SIZE = 16 * PIXEL_SCALE
PLAYER_ANIMATION_FPS = 8
PLAYER_SHADOW_SIZE = (34, 12)
PLAYER_SHADOW_OFFSET = 21
INVULNERABLE_TIME = 0.5
BLINK_INTERVAL = 0.08

DASH_SPEED_MULT = 3.0
DASH_TIME = 0.18
DASH_COOLDOWN = 1.5
AFTERIMAGE_INTERVAL = 0.05
AFTERIMAGE_LIFETIME = 0.2

XP_BASE = 5
XP_PER_LEVEL = 6
MAX_WEAPONS = 4

COVERAGE_LOW, COVERAGE_HIGH = 0.70, 0.99
CURE_CHANCE_MIN, CURE_CHANCE_MAX = 0.03, 0.15
ENEMY_MULT_MIN, ENEMY_MULT_MAX = 0.80, 1.60
FEATURED_ENEMY = {"virus": "infected", "bacteria": "bacteria"}
FEATURED_WEIGHT = 3
R0_SPEED_MIN, R0_SPEED_MAX = 0.9, 1.1
DEFAULT_COVERAGE = 0.9
DEFAULT_STRENGTH = 0.5
DEFAULT_R0 = 9
DISEASE_INFO = {
    "MEASLES":    {"name": "Measles",                    "pathogen": "virus",    "r0": 15},
    "PERTUSSIS":  {"name": "Pertussis (whooping cough)", "pathogen": "bacteria", "r0": 14.5},
    "DIPHTHERIA": {"name": "Diphtheria",                 "pathogen": "bacteria", "r0": 6.5},
    "RUBELLA":    {"name": "Rubella",                    "pathogen": "virus",    "r0": 6.5},
    "MUMPS":      {"name": "Mumps",                      "pathogen": "virus",    "r0": 5.5},
}
STARTING_CITY = "Leiden"

ENEMY_TYPES = {
    "small":    {"sprite": "duck_small.png",    "scale": 2.5, "hp": 6,  "speed": 140, "damage": 5,  "xp": 1, "first_wave": 1, "attack": "contact"},
    "bird":     {"sprite": "duck_bird.png",     "scale": 3,   "hp": 12, "speed": 100, "damage": 8,  "xp": 1, "first_wave": 1, "attack": "projectile"},
    "infected": {"sprite": "duck_infected.png", "scale": 3,   "hp": 20, "speed": 90,  "damage": 10, "xp": 2, "first_wave": 2, "attack": "contact"},
    "bacteria": {"sprite": "duck_bacteria.png", "scale": 3,   "hp": 16, "speed": 125, "damage": 8,  "xp": 2, "first_wave": 3, "attack": "contact"},
    "parasite": {"sprite": "duck_parasite.png", "scale": 3,   "hp": 30, "speed": 80,  "damage": 12, "xp": 3, "first_wave": 4, "attack": "contact"},
    "big":      {"sprite": "duck_big.png",      "scale": 4,   "hp": 90, "speed": 55,  "damage": 20, "xp": 8, "first_wave": 5, "attack": "contact"},
}
ENEMY_SHOT_RANGE = 500
ENEMY_SHOT_COOLDOWN = 2
ENEMY_SHOT_SPEED = 200
ENEMY_SHOT_DAMAGE = 10
ENEMY_SHOT_RADIUS = 8
ENEMY_SHOT_LIFETIME = 3.0
ENEMY_SHOT_COLOR = (255, 150, 40)
ENEMY_ANIMATION_FPS = 8
ENEMY_RADIUS_FACTOR = 0.35
ENEMY_SPEED_VARIATION = 0.10
MAX_ENEMIES = 300
HIT_FLASH_TIME = 0.08
KNOCKBACK_DISTANCE = 8
SLOW_TINT = (140, 190, 255)
CURE_TEXT_COLOR = (120, 255, 140)
HEART_DROP_CHANCE = 0.03
HEART_HEAL = 20

# modified by milo with the boss.py
BOSS_SPAWN_TIME = 300
BOSS_STATS = {"name": "Toco the Enforcer", "sprite": "toucan.png", "frame_size": (32, 30), "scale": 3,
              "hp": 1500, "speed": 70, "damage": 20, "radius": 40, "xp": 40, "attack": "contact",
              "knockback": 0.15}
BOSS_ENRAGE_AT = 0.4
BOSS_ENRAGE_SPEED_MULT = 1.6
BOSS_ENRAGE_COOLDOWN_MULT = 0.6
BOSS_ENRAGE_TINT = (255, 120, 120)
BOSS_BANNER_TIME = 2.0
BOSS_ATTACK_COOLDOWN = 3.0
BOSS_WINDUP_TIME = 0.8
BOSS_RECOVER_TIME = 1.0
BOSS_WINDUP_BLINK_RATE = 10
BOSS_CHARGE_SPEED = 650
BOSS_CHARGE_TIME = 0.7
BOSS_FAN_SHOTS = 7
BOSS_FAN_ANGLE = 70
BOSS_RING_SHOTS = 16
BOSS_FEATHER_SPEED = 260
BOSS_FEATHER_DAMAGE = 16
BOSS_FEATHER_RADIUS = 12
BOSS_FEATHER_LIFETIME = 3.0
BOSS_FEATHER_COLOR = (255, 200, 60)
BOSS_SUMMONS = {
    "normal":  [{"type": "small", "count": 5}],
    "enraged": [{"type": "big", "count": 5}],
}
BOSS_SUMMON_DISTANCE = 90

GEM_SIZE = (6 * PIXEL_SCALE, 6 * PIXEL_SCALE)
BIG_GEM_SIZE = (6 * 4, 6 * 4)
BIG_GEM_VALUE = 5
HEART_SIZE = (7 * PIXEL_SCALE, 6 * PIXEL_SCALE)
PICKUP_FLY_SPEED = 450
PICKUP_BOB_HEIGHT = 3
PICKUP_BOB_SPEED = 4
MAX_PICKUPS = 400

MAX_WEAPON_LEVEL = 5
STARTING_WEAPON = "syringe"
WEAPON_STATS = {
    "syringe": {
        "display_name": "Syringe", "desc": "Throws syringes where you face",
        "base": {"cooldown": 0.8, "damage": 10, "count": 1, "speed": 520, "pierce": 1, "lifetime": 1.2, "spread": 10},
        "upgrades": {
            2: {"count": 1, "desc": "+1 syringe"},
            3: {"lifetime": 1, "desc": "+40% range"},
            4: {"count": 1, "desc": "+1 syringe"},
            5: {"pierce": 2, "damage": 5, "desc": "+2 pierce, +5 damage"},
        },
    },
    "spray": {
        "display_name": "Sanitizing Spray", "desc": "Sprays a cone where you face",
        "base": {"cooldown": 1.6, "damage": 8, "radius": 110, "angle": 60},
        "upgrades": {
            2: {"angle": 15, "radius": 20, "desc": "Wider and longer cone"},
            3: {"damage": 4, "desc": "+4 damage"},
            4: {"angle": 15, "radius": 20, "desc": "Wider and longer cone"},
            5: {"cooldown": -0.4, "damage": 4, "desc": "Sprays faster, +4 damage"},
        },
    },
    "defibrillator": {
        "display_name": "Defibrillator", "desc": "Chain lightning between enemies",
        "base": {"cooldown": 2.0, "damage": 15, "range": 320, "chain_range": 160, "chains": 3},
        "upgrades": {
            2: {"chains": 1, "desc": "+1 chain"},
            3: {"chains": 1, "damage": 5, "desc": "+1 chain, +5 damage"},
            4: {"chains": 1, "desc": "+1 chain"},
            5: {"chains": 1, "damage": 5, "desc": "+1 chain, +5 damage"},
        },
    },
    "iv_bag": {
        "display_name": "IV Bag + Holder", "desc": "Slowing bag throws and a wide swing",
        "base": {"bag_cooldown": 7.0, "bag_damage": 5, "bag_speed": 350, "bag_lifetime": 1.0, "bag_range": 450,
                 "splash_radius": 70, "slow": 0.3, "slow_time": 3.0,
                 "cooldown": 2.5, "damage": 14, "swing_radius": 90, "swing_angle": 120},
        "upgrades": {
            2: {"bag_cooldown": -1.0, "desc": "Throws bags faster"},
            3: {"swing_radius": 20, "desc": "Bigger swing"},
            4: {"bag_cooldown": -1.5, "slow": 0.1, "desc": "Faster bags, stronger slow"},
            5: {"swing_radius": 25, "damage": 6, "desc": "Bigger swing, +6 damage"},
        },
    },
    "scalpel": {
        "display_name": "Scalpel + Forceps", "desc": "Fast cuts at enemies in front of you",
        "base": {"cooldown": 0.45, "damage": 7, "range": 70, "angle": 120},
        "upgrades": {
            2: {"damage": 4, "desc": "+4 damage"},
            3: {"cooldown": -0.1125, "desc": "25% faster cuts"},
            4: {"range": 25, "desc": "+25 range"},
            5: {"angle": 240, "desc": "Cuts all around you"},
        },
    },
}
SYRINGE_AIM_ASSIST = 30
DART_SIZE = (8 * PIXEL_SCALE, 5 * PIXEL_SCALE)
IV_BAG_SIZE = (14, 18)
SPRAY_COLOR = (150, 220, 255)
LIGHTNING_COLOR = (255, 245, 150)
SPLASH_COLOR = (150, 210, 255)
SWING_COLOR = (255, 255, 255)
EFFECT_TIME = 0.25
LIGHTNING_TIME = 0.15
SLASH_TIME = 0.1

DEFAULT_WAVES = [
    {"enemy_count": 12, "spawn_rate": 1.5, "enemy_speed": 1.0},
    {"enemy_count": 20, "spawn_rate": 1.2, "enemy_speed": 1.2},
]
WAVE_COUNT_GROWTH = 1.12
WAVE_INTERVAL_GROWTH = 0.95
WAVE_MIN_INTERVAL = 0.15
WAVE_SPEED_GROWTH = 0.05
WAVE_MAX_SPEED = 2.0
SPAWN_MARGIN = 60
SWARM_INTERVAL = 60
SWARM_SIZE = 15
SWARM_SPREAD = 90

CARD_COUNT = 3
PLACEHOLDER_HEAL = 30
TEST_UPGRADES = [
    ("max_hp", 20, 0.0, "Vitamins"),
    ("move_speed", 0, 0.10, "Running Shoes"),
    ("armor", 10, 0.0, "Thick Feathers"),
    ("crit_rate", 0.05, 0.0, "Sharp Needles"),
    ("crit_damage", 0.25, 0.0, "Precise Aim"),
    ("luck", 0, 0.10, "Lucky Feather"),
    ("pickup_range", 0, 0.25, "Long Wings"),
    ("xp_gain", 0, 0.10, "Study Notes"),
    ("projectile_speed", 0, 0.10, "Strong Throw"),
    ("attack_speed", 0, 0.10, "Coffee"),
    ("damage", 0, 0.10, "Stronger Medicine"),
]

INTRO_TIME = 3.0
HUD_XP_COLOR = (80, 150, 255)
HUD_HP_COLOR = (220, 60, 60)
HUD_BAR_BACK = (30, 30, 40)
HUD_BOSS_COLOR = (200, 60, 200)
CARD_COLOR = (35, 40, 55)
CARD_HOVER_COLOR = (60, 70, 95)
CARD_BORDER_COLOR = (230, 230, 230)
OVERLAY_COLOR = (0, 0, 0, 160)