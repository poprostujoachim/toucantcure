import pygame
import random
import math
import sys
from functools import lru_cache

pygame.init()
TILE_SIZE = 64
city_house_images = {}

# Load the tile images once when the module starts.
try:
    assets = {
        "ground": pygame.image.load(
            "subfunctions/assets/city_assets/tiles/base_ground_tile.png"
        ),
        "water": pygame.image.load(
            "subfunctions/assets/city_assets/tiles/water_tile.png"
        ),
        "tree": pygame.image.load(
            "subfunctions/assets/city_assets/tiles/tree_tile.png"
        ),
        "road": pygame.image.load(
            "subfunctions/assets/city_assets/tiles/road_tile.png"
        ),
    }

    # Every tile needs the same size so it fits neatly on the map grid.
    for key in assets:
        assets[key] = pygame.transform.scale(assets[key], (TILE_SIZE, TILE_SIZE))

except FileNotFoundError as e:
    print(f"Error: Missing base tiles!\n{e}")
    pygame.quit()
    sys.exit()


def get_city_house(city_name):
    """Return the house image for a city, loading it only when needed.

    Args:
        city_name: Folder name for the city whose house should be loaded.

    Returns:
        A house image scaled to the size of one map tile.
    """
    if city_name in city_house_images:
        return city_house_images[city_name]

    path = f"subfunctions/assets/city_assets/{city_name}/house.png"
    try:
        house_img = pygame.image.load(path)
        city_house_images[city_name] = pygame.transform.scale(
            house_img, (TILE_SIZE, TILE_SIZE)
        )
        return city_house_images[city_name]
    except FileNotFoundError:
        print(f"Error: Missing house file! Make sure {path} exists.")
        pygame.quit()
        sys.exit()


def lerp(a, b, t):
    """Blend between two values by a fraction from 0 to 1.
    Used to blend corners of the noise grid so the terrain is less blocky"""
    return a + t * (b - a)


def get_noise(x, y, seed_prefix):
    """Return a repeatable, smoothly changing noise value for a position.

    The same seed always produces the same value, which keeps the generated
    map stable when the player moves around or checks collisions.
    """
    # Find the corners of the grid cell that contains (x, y).
    x0 = int(math.floor(x))
    x1 = x0 + 1
    y0 = int(math.floor(y))
    y1 = y0 + 1

    # Smooth the edges between noise cells so the terrain is less blocky.
    sx = (x - x0) ** 2 * (3.0 - 2.0 * (x - x0))
    sy = (y - y0) ** 2 * (3.0 - 2.0 * (y - y0))

    def get_dot(ix, iy):
        """Get one repeatable random value for a noise-grid corner."""
        local_random = random.Random(f"{seed_prefix}_{ix}_{iy}")
        return local_random.random()

    # Blend the four corners into one smooth value.
    ix0 = lerp(get_dot(x0, y0), get_dot(x1, y0), sx)
    ix1 = lerp(get_dot(x0, y1), get_dot(x1, y1), sx)
    return lerp(ix0, ix1, sy)


def is_path_tile(x, y, city_name):
    """Return whether a map position falls inside the road noise band."""
    path_noise = get_noise(x * 0.1, y * 0.1, f"path_{city_name}")
    return 0.47 < path_noise < 0.53


def get_house_seed_chance(x, y, city_name):
    """Return the repeatable house roll for one map position.

    A position always gets the same roll, so houses do not move when the map
    is drawn again. Using a local random generator also avoids changing the
    random numbers used by other parts of the game.
    """
    local_random = random.Random(f"{x}_{y}_{city_name}")
    return local_random.random()


@lru_cache(maxsize=10000)
def get_tile_type(x, y, city_name):
    """Choose the tile type for one map position.

    Water is checked first, followed by roads, houses, trees, and finally
    ordinary ground. Neighbor checks help roads connect and houses form small
    villages instead of appearing completely alone. Results are cached because
    the same coordinates always produce the same tile.
    """
    # Water gets priority so buildings and roads do not appear in lakes.
    # The higher frequency and cutoff keep the lakes smaller.
    water_noise = get_noise(x * 0.20, y * 0.20, f"water_{city_name}")
    if water_noise > 0.70:
        return "water"

    # A wider band plus neighboring road tiles makes paths less broken.
    if is_path_tile(x, y, city_name):
        return "road"

    neighboring_paths = sum(
        is_path_tile(x + offset_x, y + offset_y, city_name)
        for offset_x, offset_y in ((1, 0), (-1, 0), (0, 1), (0, -1))
    )
    if neighboring_paths >= 2:
        return "road"

    # Start with the normal house chance, then increase it near villages
    # and roads so buildings naturally gather together.
    chance = get_house_seed_chance(x, y, city_name)

    house_chance = 0.05

    neighboring_houses = sum(
        get_house_seed_chance(x + offset_x, y + offset_y, city_name) < 0.05
        for offset_x, offset_y in ((1, 0), (-1, 0), (0, 1), (0, -1))
    )
    neighboring_paths = sum(
        is_path_tile(x + offset_x, y + offset_y, city_name)
        for offset_x, offset_y in ((1, 0), (-1, 0), (0, 1), (0, -1))
    )

    if neighboring_houses > 0:
        house_chance = 0.20
    elif neighboring_paths > 0:
        house_chance = 0.12

    if chance < house_chance:
        return "house"
    elif chance < 0.15:
        return "tree"

    return "ground"


def is_walkable(world_x, world_y, city_name):
    """Return whether the player can walk at a world-space position.

    Water, trees, and houses block movement. Roads and ground are walkable.
    """
    grid_x = int(world_x // TILE_SIZE)
    grid_y = int(world_y // TILE_SIZE)
    tile = get_tile_type(grid_x, grid_y, city_name)

    if tile in ["water", "tree", "house"]:
        return False
    return True


def draw_infinite_background(surface, camera_x, camera_y, city_name):
    """Draw the visible part of the procedurally generated map.

    Only tiles near the camera are drawn, which allows the world to feel
    infinite without creating the entire map in memory first.
    """
    screen_width, screen_height = surface.get_size()
    start_col = int(camera_x // TILE_SIZE)
    start_row = int(camera_y // TILE_SIZE)
    cols = (screen_width // TILE_SIZE) + 2
    rows = (screen_height // TILE_SIZE) + 2

    city_house_image = get_city_house(city_name)

    for row in range(start_row, start_row + rows):
        for col in range(start_col, start_col + cols):
            tile_type = get_tile_type(col, row, city_name)

            x_pos = (col * TILE_SIZE) - camera_x
            y_pos = (row * TILE_SIZE) - camera_y

            # Houses and trees are transparent overlays, so draw grass first.
            if tile_type in ["house", "tree"]:
                surface.blit(assets["ground"], (x_pos, y_pos))

            # Select the image that belongs on top of the ground tile.
            if tile_type == "house":
                tile_image = city_house_image
            else:
                tile_image = assets[tile_type]

            surface.blit(tile_image, (x_pos, y_pos))
