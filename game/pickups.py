import math
import random

import pygame

from game.assets import load_frames
from game.settings import (BIG_GEM_SIZE, BIG_GEM_VALUE, GEM_SIZE, HEART_HEAL, HEART_SIZE, PICKUP_BOB_HEIGHT,
                           PICKUP_BOB_SPEED, PICKUP_FLY_SPEED)


class Pickup:
    magnet = True

    def __init__(self, pos, image):
        self.pos = pygame.Vector2(pos)
        self.image = image
        self.radius = max(image.get_width(), image.get_height()) / 2
        self.alive = True
        self.flying = False
        self.bob_time = random.uniform(0, math.tau)

    def update(self, dt, player):
        self.bob_time += dt * PICKUP_BOB_SPEED
        distance_sq = self.pos.distance_squared_to(player.pos)
        if self.magnet and distance_sq < player.stats.pickup_range.value ** 2:
            self.flying = True
        if self.flying:
            to_player = player.pos - self.pos
            step = PICKUP_FLY_SPEED * dt
            if to_player.length() <= step:
                self.pos = pygame.Vector2(player.pos)
            else:
                self.pos += to_player.normalize() * step
        if self.pos.distance_squared_to(player.pos) < (self.radius + player.radius) ** 2:
            self.collect(player)
            self.alive = False

    def collect(self, player):
        pass

    def draw(self, surface, camera):
        bob = 0 if self.flying else math.sin(self.bob_time) * PICKUP_BOB_HEIGHT
        surface.blit(self.image, self.image.get_rect(center=(self.pos.x - camera.x, self.pos.y - camera.y + bob)))


class XPGem(Pickup):
    def __init__(self, pos, value):
        self.value = value
        super().__init__(pos, self.pick_image(value))

    @staticmethod
    def pick_image(value):
        size = BIG_GEM_SIZE if value >= BIG_GEM_VALUE else GEM_SIZE
        return load_frames("antibody.png", 1, size, fallback_color="green")[0]

    def add_value(self, value):
        self.value += value
        self.image = self.pick_image(self.value)

    def collect(self, player):
        player.add_xp(self.value)


class HealthPickup(Pickup):
    magnet = False

    def __init__(self, pos):
        super().__init__(pos, load_frames("heart.png", 1, HEART_SIZE, fallback_color="red")[0])

    def collect(self, player):
        player.heal(HEART_HEAL)
