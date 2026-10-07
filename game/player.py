import pygame

from game.assets import load_frames
from game.settings import (AFTERIMAGE_INTERVAL, AFTERIMAGE_LIFETIME, BLINK_INTERVAL, DASH_COOLDOWN,
                           DASH_SPEED_MULT, DASH_TIME, DODGE_TEXT_COLOR, INVULNERABLE_TIME, KEYS_DOWN,
                           KEYS_LEFT, KEYS_RIGHT, KEYS_UP, PLAYER_ANIMATION_FPS, PLAYER_RADIUS,
                           PLAYER_SHADOW_OFFSET, PLAYER_SHADOW_SIZE, PLAYER_SPRITE_SIZE, WATER_SPEED_MULT,
                           XP_BASE, XP_PER_LEVEL)
from game.stats import PlayerStats
from game.ui import FloatingText


def read_move_direction(keys):
    x = any(keys[k] for k in KEYS_RIGHT) - any(keys[k] for k in KEYS_LEFT)
    y = any(keys[k] for k in KEYS_DOWN) - any(keys[k] for k in KEYS_UP)
    return pygame.Vector2(x, y)


def load_player_sheets():
    size = (PLAYER_SPRITE_SIZE, PLAYER_SPRITE_SIZE)
    right = load_frames("duck_side.png", 4, size, fallback_color="yellow")
    return {
        "down": load_frames("duck_front.png", 4, size, fallback_color="yellow"),
        "up": load_frames("duck_back.png", 4, size, fallback_color="yellow"),
        "right": right,
        "left": [pygame.transform.flip(frame, True, False) for frame in right],
    }


def make_shadow():
    shadow = pygame.Surface(PLAYER_SHADOW_SIZE, pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
    return shadow


class Player:
    def __init__(self, run, pos):
        self.run = run
        self.pos = pygame.Vector2(pos)
        self.radius = PLAYER_RADIUS

        self.stats = PlayerStats()
        self.level = 1
        self.xp = 0
        self.weapons = []
        self.items = {}
        self.kills = 0

        self.facing = pygame.Vector2(1, 0)
        self.moving = False
        self.invincible = False
        self.invulnerable_timer = 0.0
        self.dash_timer = 0.0
        self.dash_cooldown_timer = 0.0
        self.dash_direction = pygame.Vector2(1, 0)
        self.afterimages = []
        self.afterimage_timer = 0.0

        self.sheets = load_player_sheets()
        self.sheet_name = "down"
        self.animation_time = 0.0
        self.shadow = make_shadow()

    @property
    def hp(self):
        return self.stats.hp

    @property
    def max_hp(self):
        return self.stats.max_hp.value

    @property
    def alive(self):
        return self.stats.alive

    @property
    def dashing(self):
        return self.dash_timer > 0

    @property
    def invulnerable(self):
        return self.invulnerable_timer > 0 or self.dashing

    def xp_to_next(self):
        return XP_BASE + (self.level - 1) * XP_PER_LEVEL

    def update(self, dt, keys, move_override=None):
        direction = move_override if move_override is not None else read_move_direction(keys)
        self.moving = direction.length_squared() > 0
        if self.moving:
            direction = direction.normalize()
            self.facing = direction

        self.invulnerable_timer = max(0.0, self.invulnerable_timer - dt)
        self.dash_cooldown_timer = max(0.0, self.dash_cooldown_timer - dt)

        speed = self.stats.move_speed.value
        if self.run.arena.is_water(self.pos):
            speed *= WATER_SPEED_MULT
        if self.dashing:
            self.dash_timer -= dt
            self.pos += self.dash_direction * speed * DASH_SPEED_MULT * dt
            self.leave_afterimage(dt)
        else:
            self.pos += direction * speed * dt
        self.pos = self.run.arena.resolve(self.pos, self.radius)

        self.update_animation(dt, direction)
        self.heal(self.stats.regen.value * dt)

        for image_and_pos in self.afterimages:
            image_and_pos[2] -= dt
        self.afterimages = [a for a in self.afterimages if a[2] > 0]

        for weapon in self.weapons:
            weapon.update(dt, self.run)

    def update_animation(self, dt, direction):
        if not self.moving:
            self.animation_time = 0.0
            return
        self.animation_time += dt
        if abs(direction.x) >= abs(direction.y):
            self.sheet_name = "right" if direction.x > 0 else "left"
        else:
            self.sheet_name = "down" if direction.y > 0 else "up"

    def current_frame(self):
        frames = self.sheets[self.sheet_name]
        if not self.moving and not self.dashing:
            return frames[0]
        return frames[int(self.animation_time * PLAYER_ANIMATION_FPS) % len(frames)]

    def try_dash(self):
        if self.dashing or self.dash_cooldown_timer > 0 or not self.alive:
            return
        self.dash_direction = pygame.Vector2(self.facing)
        self.dash_timer = DASH_TIME
        self.dash_cooldown_timer = DASH_COOLDOWN
        self.afterimage_timer = 0.0

    def leave_afterimage(self, dt):
        self.afterimage_timer -= dt
        if self.afterimage_timer <= 0:
            self.afterimage_timer = AFTERIMAGE_INTERVAL
            self.afterimages.append([self.current_frame().copy(), pygame.Vector2(self.pos), AFTERIMAGE_LIFETIME])

    def take_damage(self, amount):
        if self.invincible or self.invulnerable or not self.alive:
            return False
        if self.stats.dodged():
            self.invulnerable_timer = INVULNERABLE_TIME
            self.run.effects.append(FloatingText("dodge", self.pos - (0, 30), DODGE_TEXT_COLOR))
            return False

        self.stats.take_damage(amount * self.run.damage_mult)
        self.invulnerable_timer = INVULNERABLE_TIME
        return True

    def heal(self, amount):
        self.stats.heal(amount)

    def add_xp(self, amount):
        self.xp += self.stats.xp_from(amount)
        while self.xp >= self.xp_to_next():
            self.xp -= self.xp_to_next()
            self.level += 1
            self.run.pending_level_ups += 1

    def draw(self, surface, camera):
        screen_pos = self.pos - camera

        for image, world_pos, time_left in self.afterimages:
            image.set_alpha(int(120 * time_left / AFTERIMAGE_LIFETIME))
            surface.blit(image, image.get_rect(center=world_pos - camera))

        surface.blit(self.shadow, self.shadow.get_rect(center=(screen_pos.x, screen_pos.y + PLAYER_SHADOW_OFFSET)))

        blinking = self.invulnerable_timer > 0 and int(self.invulnerable_timer / BLINK_INTERVAL) % 2 == 0
        if not blinking:
            frame = self.current_frame()
            surface.blit(frame, frame.get_rect(center=screen_pos))

        for weapon in self.weapons:
            weapon.draw(surface, camera)
