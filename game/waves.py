import json
import math
import os
import random

import pygame

from game.enemy import Enemy
from game.settings import (COVERAGE_HIGH, COVERAGE_LOW, CURE_CHANCE_MAX, CURE_CHANCE_MIN, DEFAULT_COVERAGE,
                           DEFAULT_R0, DEFAULT_STRENGTH, DEFAULT_WAVES, DISEASE_INFO, ENEMY_MULT_MAX, ENEMY_MULT_MIN,
                           ENEMY_TYPES, FEATURED_ENEMY, FEATURED_WEIGHT, MAX_ENEMIES, R0_SPEED_MAX, R0_SPEED_MIN,
                           SCREEN_HEIGHT,
                           SCREEN_WIDTH, SPAWN_MARGIN, SWARM_INTERVAL, SWARM_SIZE, SWARM_SPREAD, WAVE_COUNT_GROWTH,
                           WAVE_INTERVAL_GROWTH, WAVE_MAX_SPEED, WAVE_MIN_INTERVAL, WAVE_SPEED_GROWTH)

LEVELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "levels")


def load_level(city):
    path = os.path.join(LEVELS_DIR, f"{city}.json")
    try:
        with open(path, encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        print(f"Warning: could not load {path} ({error}), using defaults")
        return {"city": city}


def disease_info(level):
    code = level.get("disease", "")
    return DISEASE_INFO.get(code, {"name": code.title(), "pathogen": None, "r0": DEFAULT_R0})


def level_scaling(level):
    coverage = level.get("vaccine_coverage", DEFAULT_COVERAGE)
    strength = level.get("outbreak_strength", DEFAULT_STRENGTH)
    disease = disease_info(level)
    r0 = disease["r0"]
    t = max(0.0, min(1.0, (coverage - COVERAGE_LOW) / (COVERAGE_HIGH - COVERAGE_LOW)))
    return {
        "cure_chance": CURE_CHANCE_MIN + (CURE_CHANCE_MAX - CURE_CHANCE_MIN) * t,
        "enemy_mult": ENEMY_MULT_MIN + (ENEMY_MULT_MAX - ENEMY_MULT_MIN) * strength,
        "speed_mult": R0_SPEED_MIN + (R0_SPEED_MAX - R0_SPEED_MIN) * min(r0, 18) / 18,
        "featured": FEATURED_ENEMY.get(disease["pathogen"]),
    }


class WaveSpawner:
    def __init__(self, run, level, scaling):
        self.run = run
        self.scaling = scaling
        self.waves = level.get("waves") or DEFAULT_WAVES
        self.wave_number = 0
        self.wave = None
        self.spawned_in_wave = 0
        self.spawn_timer = 0.0
        self.swarm_timer = SWARM_INTERVAL
        self.start_next_wave()

    def start_next_wave(self):
        self.wave_number += 1
        if self.wave_number <= len(self.waves):
            wave = dict(self.waves[self.wave_number - 1])
        else:
            last = self.wave
            wave = {
                "enemy_count": last["enemy_count"] * WAVE_COUNT_GROWTH,
                "spawn_rate": max(WAVE_MIN_INTERVAL, last["spawn_rate"] * WAVE_INTERVAL_GROWTH),
                "enemy_speed": min(WAVE_MAX_SPEED, last["enemy_speed"] + WAVE_SPEED_GROWTH),
            }
        self.wave = wave
        self.spawned_in_wave = 0

    def wave_size(self):
        return max(1, round(self.wave["enemy_count"] * self.scaling["enemy_mult"]))

    def update(self, dt):
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_timer = self.wave["spawn_rate"]
            if len(self.run.enemies) < MAX_ENEMIES:
                self.spawn(self.pick_type(), self.random_spawn_point())
                self.spawned_in_wave += 1
            if self.spawned_in_wave >= self.wave_size():
                self.start_next_wave()

        self.swarm_timer -= dt
        if self.swarm_timer <= 0:
            self.swarm_timer = SWARM_INTERVAL
            self.spawn_swarm()

    def pick_type(self):
        names, weights = [], []
        for name, stats in ENEMY_TYPES.items():
            if stats["first_wave"] <= self.wave_number:
                names.append(name)
                weights.append(FEATURED_WEIGHT if name == self.scaling["featured"] else 1)
        return random.choices(names, weights)[0]

    def spawn(self, type_name, pos, stats=None):
        speed_mult = self.wave["enemy_speed"] * self.scaling["speed_mult"]
        self.run.enemies.append(Enemy(self.run, type_name, pos, hp_mult=self.run.hp_mult, speed_mult=speed_mult,
                                      stats=stats))

    def spawn_distance(self):
        return math.hypot(SCREEN_WIDTH, SCREEN_HEIGHT) / 2 + SPAWN_MARGIN

    def random_spawn_point(self, angle=None):
        arena = self.run.arena
        for _ in range(10):
            a = angle if angle is not None else random.uniform(0, 360)
            point = self.run.player.pos + pygame.Vector2(self.spawn_distance(), 0).rotate(a)
            if arena.inner_rect.collidepoint(point):
                return point
            angle = None
        return arena.clamp(point, 30)

    def spawn_swarm(self):
        center = self.random_spawn_point()
        for _ in range(max(1, round(SWARM_SIZE * self.scaling["enemy_mult"]))):
            if len(self.run.enemies) >= MAX_ENEMIES:
                return
            offset = pygame.Vector2(random.uniform(-SWARM_SPREAD, SWARM_SPREAD),
                                    random.uniform(-SWARM_SPREAD, SWARM_SPREAD))
            self.spawn("small", self.run.arena.clamp(center + offset, 30))