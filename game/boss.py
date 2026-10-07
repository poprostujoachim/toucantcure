# modified by Milo for a whole new Boss type not a stronger enemy

import random

import pygame

from game.assets import flipped_frames, load_frames, tinted_frames, white_frames
from game.enemy import Enemy, EnemyProjectile, get_shadow
from game.settings import (BOSS_ATTACK_COOLDOWN, BOSS_CHARGE_SPEED, BOSS_CHARGE_TIME, BOSS_ENRAGE_AT,
                           BOSS_ENRAGE_COOLDOWN_MULT, BOSS_ENRAGE_SPEED_MULT, BOSS_ENRAGE_TINT, BOSS_FAN_ANGLE,
                           BOSS_FAN_SHOTS, BOSS_FEATHER_COLOR, BOSS_FEATHER_DAMAGE, BOSS_FEATHER_LIFETIME,
                           BOSS_FEATHER_RADIUS, BOSS_FEATHER_SPEED, BOSS_RECOVER_TIME, BOSS_RING_SHOTS, BOSS_STATS,
                           BOSS_SUMMON_DISTANCE, BOSS_SUMMONS, BOSS_WINDUP_BLINK_RATE, BOSS_WINDUP_TIME,
                           ENEMY_ANIMATION_FPS, ENEMY_TYPES, MAX_ENEMIES)

ATTACKS = ("charge", "feathers", "summon")


class Boss(Enemy):
    curable = False

    def __init__(self, run, pos, hp_mult=1.0):
        super().__init__(run, "boss", pos, hp_mult=hp_mult, stats=BOSS_STATS)
        stats = BOSS_STATS
        self.name = stats["name"]
        self.speed = stats["speed"]
        self.radius = stats["radius"]
        width, height = stats["frame_size"]
        size = (width * stats["scale"], height * stats["scale"])
        self.frames = load_frames(stats["sprite"], 4, size, fallback_color="black")
        self.shadow = get_shadow(size[0] // 2)
        self.enraged = False

        # chase -> windup -> (charge) -> recover -> chase
        self.state = "chase"
        self.state_timer = BOSS_ATTACK_COOLDOWN
        self.next_attack = None
        self.charge_direction = pygame.Vector2(1, 0)

    def set_state(self, state, duration):
        self.state = state
        self.state_timer = duration

    def update(self, dt):
        if not self.enraged and self.hp <= self.max_hp * BOSS_ENRAGE_AT:
            self.enraged = True
            self.speed *= BOSS_ENRAGE_SPEED_MULT
        self.tick_timers(dt)
        self.state_timer -= dt

        if self.state == "chase":
            self.chase(dt)
            if self.state_timer <= 0:
                self.next_attack = random.choice([a for a in ATTACKS if a != self.next_attack])
                self.set_state("windup", BOSS_WINDUP_TIME)
        elif self.state == "windup":
            if self.state_timer <= 0:
                self.start_attack()
        elif self.state == "charge":
            self.charge(dt)
        elif self.state == "recover":
            if self.state_timer <= 0:
                cooldown = BOSS_ATTACK_COOLDOWN * (BOSS_ENRAGE_COOLDOWN_MULT if self.enraged else 1)
                self.set_state("chase", cooldown)

        self.touch_player()

    def start_attack(self):
        if self.next_attack == "charge":
            to_player = self.run.player.pos - self.pos
            if to_player.length_squared() > 0:
                self.charge_direction = to_player.normalize()
            self.set_state("charge", BOSS_CHARGE_TIME)
            return
        if self.next_attack == "feathers":
            self.shoot_feathers()
        else:
            self.summon()
        self.set_state("recover", BOSS_RECOVER_TIME)

    def charge(self, dt):
        target = self.pos + self.charge_direction * BOSS_CHARGE_SPEED * dt
        self.pos = self.run.arena.clamp(target, self.radius)
        hit_wall = self.pos != target
        if hit_wall or self.state_timer <= 0:
            self.set_state("recover", BOSS_RECOVER_TIME)

    def shoot_feathers(self):
        aim = self.run.player.pos - self.pos
        aim = aim.normalize() if aim.length_squared() > 0 else pygame.Vector2(1, 0)
        if self.enraged:
            angles = [360 * i / BOSS_RING_SHOTS for i in range(BOSS_RING_SHOTS)]
        else:
            angles = [BOSS_FAN_ANGLE * (i / (BOSS_FAN_SHOTS - 1) - 0.5) for i in range(BOSS_FAN_SHOTS)]
        for angle in angles:
            direction = aim.rotate(angle)
            start = self.pos + direction * self.radius
            self.run.enemy_projectiles.append(EnemyProjectile(
                start, start + direction, speed=BOSS_FEATHER_SPEED,
                damage=BOSS_FEATHER_DAMAGE, radius=BOSS_FEATHER_RADIUS, lifetime=BOSS_FEATHER_LIFETIME,
                color=BOSS_FEATHER_COLOR))

    def summon(self):
        group = BOSS_SUMMONS["enraged" if self.enraged else "normal"]
        minions = [entry for entry in group for _ in range(entry["count"])]
        for i, entry in enumerate(minions):
            if len(self.run.enemies) >= MAX_ENEMIES:
                return
            stats = {**ENEMY_TYPES[entry["type"]], **entry.get("stats", {})}
            offset = pygame.Vector2(BOSS_SUMMON_DISTANCE, 0).rotate(360 * i / len(minions))
            self.run.spawner.spawn(entry["type"], self.run.arena.clamp(self.pos + offset, 30), stats=stats)

    def current_image(self):
        frames = self.frames
        facing_x = self.charge_direction.x if self.state == "charge" else self.run.player.pos.x - self.pos.x
        if facing_x > 0:
            frames = flipped_frames(frames)
        blinking = self.state == "windup" and int(self.state_timer * BOSS_WINDUP_BLINK_RATE) % 2 == 0
        if self.flash_timer > 0 or blinking:
            frames = white_frames(frames)
        elif self.enraged:
            frames = tinted_frames(frames, BOSS_ENRAGE_TINT)
        return frames[int(self.animation_time * ENEMY_ANIMATION_FPS) % len(frames)]