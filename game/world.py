import random

import pygame

from game.assets import load_frames
from game.settings import (ARENA_HEIGHT, ARENA_WIDTH, SCREEN_HEIGHT, SCREEN_WIDTH,
                           TILE_SIZE, WALL_EDGE_COLOR, WALL_THICKNESS)


class Arena:
    def __init__(self):
        self.width = ARENA_WIDTH
        self.height = ARENA_HEIGHT
        self.inner_rect = pygame.Rect(WALL_THICKNESS, WALL_THICKNESS,
                                      ARENA_WIDTH - 2 * WALL_THICKNESS,
                                      ARENA_HEIGHT - 2 * WALL_THICKNESS)
        self.floor = self.build_floor()

    def build_floor(self):
        tiles = load_frames("ground.png", 3, (TILE_SIZE, TILE_SIZE), fallback_color=(34, 139, 34))
        floor = pygame.Surface((self.width, self.height)).convert()
        for y in range(0, self.height, TILE_SIZE):
            for x in range(0, self.width, TILE_SIZE):
                floor.blit(random.choice(tiles), (x, y))

        shade = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 150))
        pygame.draw.rect(shade, (0, 0, 0, 0), self.inner_rect)
        floor.blit(shade, (0, 0))
        pygame.draw.rect(floor, WALL_EDGE_COLOR, self.inner_rect, 4)
        return floor

    def clamp(self, pos, radius):
        x = max(self.inner_rect.left + radius, min(pos.x, self.inner_rect.right - radius))
        y = max(self.inner_rect.top + radius, min(pos.y, self.inner_rect.bottom - radius))
        return pygame.Vector2(x, y)

    def draw(self, surface, camera):
        view = pygame.Rect(round(camera.x), round(camera.y), SCREEN_WIDTH, SCREEN_HEIGHT)
        surface.blit(self.floor, (0, 0), area=view)
