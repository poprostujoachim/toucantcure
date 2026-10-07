import os

import pygame

from subfunctions.generation import is_walkable
from subfunctions.stats import PlayerStats

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
PLAYER_FRAME_COUNT = 4
PLAYER_ANIMATION_FPS = 8


def load_player_frames(filename, size):
    sheet = pygame.image.load(os.path.join(ASSETS_DIR, filename)).convert_alpha()
    frame_width = sheet.get_width() // PLAYER_FRAME_COUNT
    frame_height = sheet.get_height()
    return [
        pygame.transform.scale(
            sheet.subsurface((index * frame_width, 0, frame_width, frame_height)),
            (size, size),
        )
        for index in range(PLAYER_FRAME_COUNT)
    ]


class Player(pygame.sprite.Sprite):
    def __init__(self, start_x, start_y, radius=20):
        super().__init__()
        self.pos = pygame.Vector2(start_x, start_y)
        self.radius = radius
        self.stats = PlayerStats()
        size = radius * 2
        self.frames = {
            "front": load_player_frames("duck_front.png", size),
            "side": load_player_frames("duck_side.png", size),
            "back": load_player_frames("duck_back.png", size),
        }
        self.facing = "front"
        self.facing_left = False
        self.animation_time = 0.0

    # Shortcuts so other code can write player.hp instead of player.stats.hp.
    @property
    def hp(self):
        return self.stats.hp

    @property
    def max_hp(self):
        return self.stats.max_hp.value

    @property
    def alive(self):
        return self.stats.alive

    def take_damage(self, amount):
        self.stats.take_damage(amount)

    def update(self, delta_time, keys, city_name):
        speed = self.stats.move_speed.value
        new_x, new_y = self.pos.x, self.pos.y
        if keys[pygame.K_w]:
            new_y -= speed * delta_time
        if keys[pygame.K_s]:
            new_y += speed * delta_time
        if keys[pygame.K_a]:
            new_x -= speed * delta_time
        if keys[pygame.K_d]:
            new_x += speed * delta_time

        # Check each axis on its own so the player slides along walls instead of sticking.
        if is_walkable(new_x, self.pos.y, city_name):
            self.pos.x = new_x
        if is_walkable(self.pos.x, new_y, city_name):
            self.pos.y = new_y

        if keys[pygame.K_w]:
            self.facing = "back"
        elif keys[pygame.K_s]:
            self.facing = "front"
        elif keys[pygame.K_a]:
            self.facing = "side"
            self.facing_left = True
        elif keys[pygame.K_d]:
            self.facing = "side"
            self.facing_left = False

        if any(keys[key] for key in (pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d)):
            self.animation_time += delta_time

    def draw(self, surface, camera_x, camera_y):
        frame_index = int(self.animation_time * PLAYER_ANIMATION_FPS) % PLAYER_FRAME_COUNT
        image = self.frames[self.facing][frame_index]
        if self.facing == "side" and self.facing_left:
            image = pygame.transform.flip(image, True, False)
        # Shift from world position to screen position using the camera.
        screen_pos = (round(self.pos.x - camera_x), round(self.pos.y - camera_y))
        surface.blit(image, image.get_rect(center=screen_pos))
