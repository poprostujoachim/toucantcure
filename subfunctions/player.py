import os

import pygame

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

    def update(self, delta_time, keys, bounds):
        speed = self.stats.move_speed.value
        if keys[pygame.K_w]:
            self.pos.y -= speed * delta_time
        if keys[pygame.K_s]:
            self.pos.y += speed * delta_time
        if keys[pygame.K_a]:
            self.pos.x -= speed * delta_time
        if keys[pygame.K_d]:
            self.pos.x += speed * delta_time

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

        # bounds is the arena Rect, so stay inside it rather than the screen.
        self.pos.x = max(bounds.left + self.radius, min(self.pos.x, bounds.right - self.radius))
        self.pos.y = max(bounds.top + self.radius, min(self.pos.y, bounds.bottom - self.radius))

    def draw(self, surface):
        frame_index = int(self.animation_time * PLAYER_ANIMATION_FPS) % PLAYER_FRAME_COUNT
        image = self.frames[self.facing][frame_index]
        if self.facing == "side" and self.facing_left:
            image = pygame.transform.flip(image, True, False)
        surface.blit(image, image.get_rect(center=(round(self.pos.x), round(self.pos.y))))
