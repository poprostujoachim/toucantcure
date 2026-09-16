import os

import pygame

ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')


def load_ground():
    """Load the ground tile, falling back to a plain green square."""
    try:
        return pygame.image.load(os.path.join(ASSETS_DIR, 'ground.png')).convert()
    except pygame.error:
        fallback = pygame.Surface((64, 64))
        fallback.fill((34, 139, 34))
        return fallback


def generate_terrain(width, height):
    """Build the tiled background surface, offsetting every row for a brick pattern."""
    ground = load_ground()
    tile_width = ground.get_width()
    tile_height = ground.get_height()
    offset_amount = tile_width // 3

    background = pygame.Surface((width, height))

    row_index = 0
    for y in range(0, height, tile_height):
        current_offset = (row_index % 3) * offset_amount
        for x in range(-tile_width, width + tile_width, tile_width):
            background.blit(ground, (x + current_offset, y))
        row_index += 1

    return background
