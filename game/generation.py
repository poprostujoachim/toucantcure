import math
import random
import zlib
from collections import OrderedDict
from functools import lru_cache

import pygame

from game.assets import load_frames
from game.settings import (CITY_HOUSES, GRASS_DETAIL_CHANCE, GROUND_SHADE, GROUND_SHADE_SCALE, HOUSE_CANVAS,
                           HOUSE_SOLID_PART, OBSTACLE_SIZE, PROP_SCALE, SCREEN_HEIGHT, SCREEN_WIDTH, START_AREA_TILES,
                           TERRAIN_FRAMES, TILE_SIZE, TREE_CANVAS, TREE_TRUNK_HEIGHT, TREE_TRUNK_WIDTH, WORLD_TILES)

# The map is generated tile by tile around the camera, so it never has to exist in memory as a whole.
# The player starts in the middle of a WORLD_TILES-wide square, which is hours of walking from any edge.
START_TILE = WORLD_TILES // 2
CHUNK_TILES = 8           # the ground is drawn in cached chunks of 8x8 tiles
MAX_CHUNKS = 48
HOUSE_SPACING = (3, 4)    # min tiles between two houses (across, down), so the big house sprites never overlap
TILE_COLORS = {"ground": (70, 120, 60), "road": (110, 105, 100), "water": (50, 100, 190)}
WATER_LEVELS = ("shallow", "mid", "deep")
# water tiles get their banks per quadrant (TL, TR, BL, BR); bank sheets hold 4 pieces per quadrant:
# land above/below and beside (outer corner), land above/below only, land beside only, land only diagonally (inner)
QUADRANTS = ((-1, -1), (1, -1), (-1, 1), (1, 1))
BANK_OUTER, BANK_ROW, BANK_COLUMN, BANK_INNER = range(4)
BANK_PIECES = 4 * len(QUADRANTS)

city_house_images = {}
_terrain = None
_chunks = OrderedDict()


def lerp(a, b, t):
    """Blend between two values by a fraction from 0 to 1.
    Used to blend corners of the noise grid so the terrain is less blocky"""
    return a + t * (b - a)


@lru_cache(maxsize=100000)
def get_dot(ix, iy, seed_prefix):
    """Get one repeatable random value for a noise-grid corner."""
    local_random = random.Random(f"{seed_prefix}_{ix}_{iy}")
    return local_random.random()


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

    # Blend the four corners into one smooth value.
    ix0 = lerp(get_dot(x0, y0, seed_prefix), get_dot(x1, y0, seed_prefix), sx)
    ix1 = lerp(get_dot(x0, y1, seed_prefix), get_dot(x1, y1, seed_prefix), sx)
    return lerp(ix0, ix1, sy)


def is_path_tile(x, y, city_name):
    """Return whether a map position falls inside the road noise band."""
    path_noise = get_noise(x * 0.1, y * 0.1, f"path_{city_name}")
    return 0.47 < path_noise < 0.53


@lru_cache(maxsize=100000)
def get_house_seed_chance(x, y, city_name):
    """Return the repeatable house roll for one map position.

    A position always gets the same roll, so houses do not move when the map
    is drawn again. Using a local random generator also avoids changing the
    random numbers used by other parts of the game.
    """
    local_random = random.Random(f"{x}_{y}_{city_name}")
    return local_random.random()


def in_start_area(x, y):
    return abs(x - START_TILE) <= START_AREA_TILES and abs(y - START_TILE) <= START_AREA_TILES


@lru_cache(maxsize=None)
def start_shift(city_name):
    """How far the generated map is moved sideways so the player starts on dry land, instead of a lake
    being cut in half around the start."""
    reach = range(-START_AREA_TILES - 1, START_AREA_TILES + 2)
    for step in range(1000):
        shift = step * 7
        if all(get_noise((START_TILE + shift + dx) * 0.20, (START_TILE + dy) * 0.20, f"water_{city_name}") <= 0.70
               for dx in reach for dy in reach):
            return shift
    return 0


@lru_cache(maxsize=100000)
def get_tile_type(x, y, city_name):
    """Choose the tile type for one map position.

    The start area around the player is kept free of houses and trees.
    Results are cached because the same coordinates always produce the same tile.
    """
    tile = generate_tile_type(x + start_shift(city_name), y, city_name)
    if tile in ("house", "tree") and in_start_area(x, y):
        return "ground"
    return tile


def generate_tile_type(x, y, city_name):
    """Choose the tile type for one map position.

    Water is checked first, followed by roads, houses, trees, and finally
    ordinary ground. Neighbor checks help roads connect and houses form small
    villages instead of appearing completely alone.
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
        get_house_seed_chance(x + offset_x, y + offset_y, city_name) < house_chance
        for offset_x, offset_y in ((1, 0), (-1, 0), (0, 1), (0, -1))
    )
    neighboring_paths = sum(
        is_path_tile(x + offset_x, y + offset_y, city_name)
        for offset_x, offset_y in ((1, 0), (-1, 0), (0, 1), (0, -1))
    )

    if neighboring_houses > 0 and neighboring_paths > 0:
        house_chance = 0.30
    elif neighboring_paths > 0:
        house_chance = 0.12

    if chance < house_chance:
        return "house"
    elif chance < 0.15:
        return "tree"

    return "ground"


def house_fits(x, y, city_name):
    """A house sprite is three tiles wide, so its side tiles must not be road or water."""
    return (get_tile_type(x, y, city_name) == "house"
            and all(get_tile_type(x + dx, y, city_name) not in ("road", "water") for dx in (-1, 1)))


@lru_cache(maxsize=100000)
def is_house_spot(x, y, city_name):
    """Whether a house tile really gets a house: of the houses too close to each other, only the one with
    the lowest roll is built, so the big sprites never overlap."""
    if not house_fits(x, y, city_name):
        return False
    mine = (get_house_seed_chance(x, y, city_name), x, y)
    across, down = HOUSE_SPACING
    for dy in range(1 - down, down):
        for dx in range(1 - across, across):
            other_x, other_y = x + dx, y + dy
            if (dx or dy) and house_fits(other_x, other_y, city_name):
                if (get_house_seed_chance(other_x, other_y, city_name), other_x, other_y) < mine:
                    return False
    return True


@lru_cache(maxsize=100000)
def get_object(x, y, city_name):
    """'house', 'tree' or None for a tile. Trees standing where a house is drawn are left out."""
    tile = get_tile_type(x, y, city_name)
    if tile == "house":
        return "house" if is_house_spot(x, y, city_name) else None
    if tile == "tree":
        covered = any(is_house_spot(x + dx, y + dy, city_name)
                      for dx in (-1, 0, 1) for dy in range(HOUSE_SPACING[1]))
        return None if covered else "tree"
    return None


def is_walkable(world_x, world_y, city_name):
    """Return whether the player can walk at a world-space position.

    Water, trees, and houses block movement. Roads and ground are walkable.
    """
    grid_x = int(world_x // TILE_SIZE)
    grid_y = int(world_y // TILE_SIZE)
    return get_tile_type(grid_x, grid_y, city_name) != "water" and get_object(grid_x, grid_y, city_name) is None


def tile_hash(x, y, city_name):
    """A repeatable number per tile, used to pick which grass, water or tree image to show."""
    return zlib.crc32(f"{x},{y},{city_name}".encode())


def body_rect(image):
    """Bounding box of the opaque part of a sprite, without its soft ground shadow."""
    return image.get_bounding_rect(min_alpha=200)


def with_sink(image):
    """Pairs a sprite with how far it reaches below its ground line (the shadow)."""
    return image, image.get_height() - body_rect(image).bottom


def get_city_house(city_name):
    """Return the house image for a city (and how far its shadow reaches below the ground), loading it once."""
    if city_name not in city_house_images:
        style = CITY_HOUSES.get(city_name)
        if style is None:
            image = load_frames(f"city_assets/{city_name}/house.png", 1, (OBSTACLE_SIZE, OBSTACLE_SIZE),
                                fallback_color=(190, 150, 110))[0]
            city_house_images[city_name] = (image, 0)
        else:
            width, height = HOUSE_CANVAS
            image = load_frames(f"pixel-dutch-house/{style}_house.png", 1, (width * PROP_SCALE, height * PROP_SCALE),
                                fallback_color=(190, 150, 110))[0]
            city_house_images[city_name] = with_sink(image)
    return city_house_images[city_name]


class Terrain:
    def __init__(self):
        size, half = (TILE_SIZE, TILE_SIZE), (TILE_SIZE // 2, TILE_SIZE // 2)
        self.road = load_frames("city_assets/tiles/road_tile.png", 1, size, fallback_color=TILE_COLORS["road"])[0]
        self.grass = load_frames("terrain/grass.png", TERRAIN_FRAMES["grass"], size,
                                 fallback_color=TILE_COLORS["ground"])
        details = load_frames("terrain/grass_details.png", TERRAIN_FRAMES["grass_details"], size,
                              fallback_color=(0, 0, 0, 0))
        self.details = details + [pygame.transform.flip(detail, True, False) for detail in details]
        self.water = {level: load_frames(f"terrain/water_{level}.png", TERRAIN_FRAMES["water"], size,
                                         fallback_color=TILE_COLORS["water"]) for level in WATER_LEVELS}
        self.banks = {kind: load_frames(f"terrain/bank_{name}.png", BANK_PIECES, half, fallback_color=(0, 0, 0, 0))
                      for kind, name in (("ground", "grass"), ("road", "quay"))}
        width, height = TREE_CANVAS
        trees = load_frames("terrain/trees.png", TERRAIN_FRAMES["trees"], (width * PROP_SCALE, height * PROP_SCALE),
                            fallback_color=(40, 110, 50))
        self.trees = [with_sink(image) for image in trees]


def get_terrain():
    global _terrain
    if _terrain is None:
        _terrain = Terrain()
    return _terrain


def water_level(x, y, city_name):
    """Water right at the shore is shallow, one tile further is mid, the rest is deep."""
    for distance in (1, 2):
        for dx in range(-distance, distance + 1):
            dy = distance - abs(dx)
            if any(get_tile_type(x + dx, y + side, city_name) != "water" for side in {dy, -dy}):
                return WATER_LEVELS[distance - 1]
    return WATER_LEVELS[2]


def draw_banks(chunk, terrain, x, y, pos, city_name):
    half = TILE_SIZE // 2
    for quadrant, (dx, dy) in enumerate(QUADRANTS):
        row_side, column_side = get_tile_type(x, y + dy, city_name), get_tile_type(x + dx, y, city_name)
        diagonal = get_tile_type(x + dx, y + dy, city_name)
        if row_side != "water" and column_side != "water":
            case, land = BANK_OUTER, row_side
        elif row_side != "water":
            case, land = BANK_ROW, row_side
        elif column_side != "water":
            case, land = BANK_COLUMN, column_side
        elif diagonal != "water":
            case, land = BANK_INNER, diagonal
        else:
            continue
        pieces = terrain.banks["road" if land == "road" else "ground"]
        if len(pieces) == BANK_PIECES:
            chunk.blit(pieces[quadrant * 4 + case], (pos[0] + (quadrant % 2) * half, pos[1] + (quadrant // 2) * half))


def shade_chunk(chunk, chunk_x, chunk_y, city_name):
    """Soft light and dark patches across the map, so the tiles don't read as a repeating grid."""
    corners = CHUNK_TILES + 1
    noise = pygame.Surface((corners, corners))
    low, high = GROUND_SHADE
    for j in range(corners):
        for i in range(corners):
            value = get_noise((chunk_x * CHUNK_TILES + i) * GROUND_SHADE_SCALE,
                              (chunk_y * CHUNK_TILES + j) * GROUND_SHADE_SCALE, f"shade_{city_name}")
            level = round(255 * (low + (high - low) * value))
            noise.set_at((i, j), (level, level, level))
    # each noise pixel becomes the centre of a tile-sized block; cropping half a tile puts the values on the
    # tile corners, so neighbouring chunks line up without seams
    smooth = pygame.transform.smoothscale(noise, (corners * TILE_SIZE, corners * TILE_SIZE))
    area = pygame.Rect(TILE_SIZE // 2, TILE_SIZE // 2, CHUNK_TILES * TILE_SIZE, CHUNK_TILES * TILE_SIZE)
    chunk.blit(smooth, (0, 0), area=area, special_flags=pygame.BLEND_RGB_MULT)


def render_chunk(chunk_x, chunk_y, city_name):
    terrain = get_terrain()
    chunk = pygame.Surface((CHUNK_TILES * TILE_SIZE, CHUNK_TILES * TILE_SIZE)).convert()
    for row in range(CHUNK_TILES):
        for col in range(CHUNK_TILES):
            x, y = chunk_x * CHUNK_TILES + col, chunk_y * CHUNK_TILES + row
            pos = (col * TILE_SIZE, row * TILE_SIZE)
            tile_type = get_tile_type(x, y, city_name)
            pick = tile_hash(x, y, city_name)
            if tile_type == "water":
                images = terrain.water[water_level(x, y, city_name)]
                chunk.blit(images[pick % len(images)], pos)
                draw_banks(chunk, terrain, x, y, pos, city_name)
            elif tile_type == "road":
                chunk.blit(terrain.road, pos)
            else:
                # houses and trees are drawn as obstacles, so their tiles get grass like the ground
                chunk.blit(terrain.grass[pick % len(terrain.grass)], pos)
                if tile_type == "ground" and (pick >> 8) % 1000 < GRASS_DETAIL_CHANCE * 1000:
                    chunk.blit(terrain.details[(pick >> 16) % len(terrain.details)], pos)
    shade_chunk(chunk, chunk_x, chunk_y, city_name)
    return chunk


def get_chunk(chunk_x, chunk_y, city_name):
    key = (chunk_x, chunk_y, city_name)
    if key in _chunks:
        _chunks.move_to_end(key)
    else:
        _chunks[key] = render_chunk(chunk_x, chunk_y, city_name)
        if len(_chunks) > MAX_CHUNKS:
            _chunks.popitem(last=False)
    return _chunks[key]


def draw_infinite_background(surface, camera_x, camera_y, city_name):
    """Draw the visible part of the procedurally generated map.

    Only chunks near the camera are drawn, which allows the world to feel
    infinite without creating the entire map in memory first.
    """
    screen_width, screen_height = surface.get_size()
    size = CHUNK_TILES * TILE_SIZE
    camera_x, camera_y = round(camera_x), round(camera_y)
    for chunk_y in range(camera_y // size, (camera_y + screen_height) // size + 1):
        for chunk_x in range(camera_x // size, (camera_x + screen_width) // size + 1):
            surface.blit(get_chunk(chunk_x, chunk_y, city_name), (chunk_x * size - camera_x, chunk_y * size - camera_y))


def push_circle_out_of_rect(pos, radius, rect):
    closest = pygame.Vector2(max(rect.left, min(pos.x, rect.right)), max(rect.top, min(pos.y, rect.bottom)))
    offset = pos - closest
    distance_sq = offset.length_squared()
    if distance_sq >= radius * radius:
        return pos
    if distance_sq > 0:
        return closest + offset.normalize() * radius
    exits = [
        (pos.x - rect.left, pygame.Vector2(rect.left - radius, pos.y)),
        (rect.right - pos.x, pygame.Vector2(rect.right + radius, pos.y)),
        (pos.y - rect.top, pygame.Vector2(pos.x, rect.top - radius)),
        (rect.bottom - pos.y, pygame.Vector2(pos.x, rect.bottom + radius)),
    ]
    return min(exits, key=lambda exit_: exit_[0])[1]


class Obstacle:
    def __init__(self, image, tile_x, tile_y, solid_rect, sink=0):
        self.image = image
        ground = ((tile_x + 0.5) * TILE_SIZE, (tile_y + 1) * TILE_SIZE)
        self.rect = image.get_rect(midbottom=(ground[0], ground[1] + sink))
        self.pos = pygame.Vector2(ground)
        self.solid = solid_rect

    def draw(self, surface, camera):
        surface.blit(self.image, self.rect.move(-round(camera.x), -round(camera.y)))


@lru_cache(maxsize=20000)
def get_obstacle(x, y, city_name):
    """The house or tree standing on a tile, with the part of it you bump into, or None."""
    kind = get_object(x, y, city_name)
    if kind == "house":
        image, sink = get_city_house(city_name)
        body = body_rect(image)
        height = round(body.height * HOUSE_SOLID_PART)
        left = (x + 0.5) * TILE_SIZE - image.get_width() / 2 + body.left
        return Obstacle(image, x, y, pygame.Rect(round(left), (y + 1) * TILE_SIZE - height, body.width, height), sink)
    if kind == "tree":
        trees = get_terrain().trees
        image, sink = trees[tile_hash(x, y, city_name) % len(trees)]
        body = body_rect(image)
        solid = pygame.Rect(0, 0, round(body.width * TREE_TRUNK_WIDTH), round(body.height * TREE_TRUNK_HEIGHT))
        solid.midbottom = ((x + 0.5) * TILE_SIZE, (y + 1) * TILE_SIZE)
        return Obstacle(image, x, y, solid, sink)
    return None


@lru_cache(maxsize=20000)
def tile_solids(x, y, city_name):
    """Every solid that reaches into a tile. Houses are wide and their solid starts up to two rows above
    the tile they stand on, so nearby tiles are checked too."""
    area = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
    solids = []
    for other_y in range(y, y + 3):
        for other_x in range(x - 2, x + 3):
            obstacle = get_obstacle(other_x, other_y, city_name)
            if obstacle is not None and obstacle.solid.colliderect(area):
                solids.append(obstacle.solid)
    return tuple(solids)


class CityMap:
    """The generated world as the run sees it: drawing, obstacles, collisions and water."""

    def __init__(self, city):
        self.city = city
        self.size = WORLD_TILES
        self.width = self.height = WORLD_TILES * TILE_SIZE
        self.inner_rect = pygame.Rect(0, 0, self.width, self.height)

    def clamp(self, pos, radius):
        x = max(self.inner_rect.left + radius, min(pos.x, self.inner_rect.right - radius))
        y = max(self.inner_rect.top + radius, min(pos.y, self.inner_rect.bottom - radius))
        return pygame.Vector2(x, y)

    def nearby_solids(self, pos):
        tile_x, tile_y = int(pos.x // TILE_SIZE), int(pos.y // TILE_SIZE)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                yield from tile_solids(tile_x + dx, tile_y + dy, self.city)

    def resolve(self, pos, radius):
        pos = self.clamp(pos, radius)
        for solid in self.nearby_solids(pos):
            pos = push_circle_out_of_rect(pos, radius, solid)
        return self.clamp(pos, radius)

    def is_free(self, pos, radius):
        if not self.inner_rect.collidepoint(pos):
            return False
        return all(push_circle_out_of_rect(pos, radius, solid) == pos for solid in self.nearby_solids(pos))

    def is_water(self, pos):
        return get_tile_type(int(pos.x // TILE_SIZE), int(pos.y // TILE_SIZE), self.city) == "water"

    def visible_obstacles(self, camera):
        view = pygame.Rect(round(camera.x), round(camera.y), SCREEN_WIDTH, SCREEN_HEIGHT)
        reach_x = math.ceil(HOUSE_CANVAS[0] * PROP_SCALE / 2 / TILE_SIZE)
        reach_y = math.ceil(HOUSE_CANVAS[1] * PROP_SCALE / TILE_SIZE)
        obstacles = []
        for y in range(view.top // TILE_SIZE, view.bottom // TILE_SIZE + reach_y + 1):
            for x in range(view.left // TILE_SIZE - reach_x, view.right // TILE_SIZE + reach_x + 1):
                obstacle = get_obstacle(x, y, self.city)
                if obstacle is not None and view.colliderect(obstacle.rect):
                    obstacles.append(obstacle)
        return obstacles

    def draw(self, surface, camera):
        draw_infinite_background(surface, camera.x, camera.y, self.city)
