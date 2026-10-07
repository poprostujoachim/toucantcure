import random

import pygame

from game.assets import load_frames, tinted_frames, white_frames
from game.settings import (CURE_TEXT_COLOR, ENEMY_ANIMATION_FPS, ENEMY_RADIUS_FACTOR, ENEMY_SHOT_COLOR,
                           ENEMY_SHOT_COOLDOWN, ENEMY_SHOT_DAMAGE, ENEMY_SHOT_LIFETIME, ENEMY_SHOT_RADIUS,
                           ENEMY_SHOT_RANGE, ENEMY_SHOT_SPEED, ENEMY_SPEED_VARIATION, ENEMY_TYPES, HIT_FLASH_TIME,
                           KNOCKBACK_DISTANCE, SLOW_TINT)
from game.ui import FloatingText

_shadows = {}


def get_shadow(width):
    if width not in _shadows:
        shadow = pygame.Surface((width, width // 3), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 80), shadow.get_rect())
        _shadows[width] = shadow
    return _shadows[width]


class EnemyProjectile:
    def __init__(self, pos, target_pos, speed=ENEMY_SHOT_SPEED, damage=ENEMY_SHOT_DAMAGE,
                 radius=ENEMY_SHOT_RADIUS, lifetime=ENEMY_SHOT_LIFETIME, color=ENEMY_SHOT_COLOR):
        self.pos = pygame.Vector2(pos)
        direction = target_pos - self.pos
        if direction.length_squared() > 0:
            direction = direction.normalize()
        self.velocity = direction * speed
        self.damage = damage
        self.radius = radius
        self.lifetime = lifetime
        self.color = color
        self.alive = True

    def update(self, dt, run):
        self.pos += self.velocity * dt
        self.lifetime -= dt
        player = run.player
        if self.pos.distance_squared_to(player.pos) < (self.radius + player.radius) ** 2:
            player.take_damage(self.damage)
            self.alive = False
        elif self.lifetime <= 0:
            self.alive = False

    def draw(self, surface, camera):
        pygame.draw.circle(surface, self.color, self.pos - camera, self.radius)
        pygame.draw.circle(surface, (90, 40, 0), self.pos - camera, self.radius, 1)


class Enemy:
    curable = True

    def __init__(self, run, type_name, pos, hp_mult=1.0, speed_mult=1.0):
        stats = ENEMY_TYPES[type_name]
        self.run = run
        self.type_name = type_name
        self.pos = pygame.Vector2(pos)
        self.max_hp = stats["hp"] * hp_mult
        self.hp = self.max_hp
        self.speed = stats["speed"] * speed_mult * random.uniform(1 - ENEMY_SPEED_VARIATION, 1 + ENEMY_SPEED_VARIATION)
        self.damage = stats["damage"]
        self.xp = stats["xp"]
        self.attack = stats["attack"]
        self.shot_timer = 0.0

        size = round(16 * stats["scale"])
        self.frames = load_frames(stats["sprite"], 4, (size, size), fallback_color="purple")
        self.radius = size * ENEMY_RADIUS_FACTOR
        self.shadow = get_shadow(round(size * 0.6))
        self.animation_time = random.uniform(0, 1)

        self.alive = True
        self.cured = False
        self.flash_timer = 0.0
        self.slow_amount = 0.0
        self.slow_timer = 0.0

    def update(self, dt):
        player = self.run.player
        self.animation_time += dt
        self.flash_timer = max(0.0, self.flash_timer - dt)
        self.slow_timer = max(0.0, self.slow_timer - dt)

        speed = self.speed * self.speed_factor()
        to_player = player.pos - self.pos
        if to_player.length_squared() > 1:
            self.pos += to_player.normalize() * speed * dt

        if self.attack == "contact":
            if self.pos.distance_squared_to(player.pos) < (self.radius + player.radius) ** 2:
                player.take_damage(self.damage)
        else:
            self.shot_timer = max(0.0, self.shot_timer - dt)
            if self.shot_timer <= 0 and to_player.length_squared() <= ENEMY_SHOT_RANGE ** 2:
                self.shot_timer = ENEMY_SHOT_COOLDOWN
                self.run.enemy_projectiles.append(EnemyProjectile(self.pos, player.pos))

    def speed_factor(self):
        if self.slow_timer > 0:
            return 1 - self.slow_amount
        return 1.0

    def take_damage(self, amount, knockback_from=None, crit=False):
        if not self.alive:
            return
        self.flash_timer = HIT_FLASH_TIME
        if knockback_from is not None:
            away = self.pos - knockback_from
            if away.length_squared() > 0:
                self.pos += away.normalize() * KNOCKBACK_DISTANCE * (2 if crit else 1)

        if self.curable and self.run.player.stats.cured():
            self.cured = True
            self.hp = 0
            self.run.effects.append(FloatingText("CURED!", self.pos - (0, self.radius + 10), CURE_TEXT_COLOR))
        else:
            self.hp -= amount
        if self.hp <= 0:
            self.alive = False

    def slow(self, amount, duration):
        self.slow_amount = max(self.slow_amount if self.slow_timer > 0 else 0.0, amount)
        self.slow_timer = max(self.slow_timer, duration)

    def current_image(self):
        index = int(self.animation_time * ENEMY_ANIMATION_FPS) % len(self.frames)
        if self.flash_timer > 0:
            return white_frames(self.frames)[index]
        if self.slow_timer > 0:
            return tinted_frames(self.frames, SLOW_TINT)[index]
        return self.frames[index]

    def draw(self, surface, camera):
        screen_pos = self.pos - camera
        image = self.current_image()
        rect = image.get_rect(center=screen_pos)
        surface.blit(self.shadow, self.shadow.get_rect(center=(screen_pos.x, rect.bottom - 3)))
        surface.blit(image, rect)
