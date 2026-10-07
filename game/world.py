import random

import pygame

from game.assets import load_frames
from game.settings import (CANAL_CHANCE, CITY_MAPS, COAST_WIDTH, DEFAULT_CITY_MAP, GROUND_DARKEN_ALPHA,
                           GROUND_DARKEN_CHANCE, HOUSE_SOLID_PART, MAP_TILES, MIN_ROAD_GAP, OBSTACLE_SIZE,
                           POND_COUNT, POND_RADIUS, SCREEN_HEIGHT, SCREEN_WIDTH, START_AREA_TILES, TILE_SIZE,
                           TREE_TRUNK_HEIGHT, TREE_TRUNK_WIDTH)

GRASS, ROAD, WATER = "grass", "road", "water"
TILE_FILES = {GRASS: "base_ground_tile", ROAD: "road_tile", WATER: "water_tile"}
TILE_COLORS = {GRASS: (70, 120, 60), ROAD: (110, 105, 100), WATER: (50, 100, 190)}


def load_tile(kind):
    return load_frames(f"city_assets/tiles/{TILE_FILES[kind]}.png", 1, (TILE_SIZE, TILE_SIZE),
                       fallback_color=TILE_COLORS[kind])[0]


def load_obstacle(path, fallback_color):
    return load_frames(path, 1, (OBSTACLE_SIZE, OBSTACLE_SIZE), fallback_color=fallback_color)[0]


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
    def __init__(self, image, tile_x, tile_y, solid_rect):
        self.image = image
        self.rect = image.get_rect(midbottom=((tile_x + 0.5) * TILE_SIZE, (tile_y + 1) * TILE_SIZE))
        self.pos = pygame.Vector2(self.rect.midbottom)
        self.solid = solid_rect

    def draw(self, surface, camera):
        surface.blit(self.image, self.rect.move(-round(camera.x), -round(camera.y)))


class CityMap:
    def __init__(self, city):
        style = CITY_MAPS.get(city, DEFAULT_CITY_MAP)
        rng = random.Random(style["seed"])
        self.city = city
        self.size = MAP_TILES
        self.width = self.height = MAP_TILES * TILE_SIZE
        self.inner_rect = pygame.Rect(TILE_SIZE, TILE_SIZE, self.width - 2 * TILE_SIZE, self.height - 2 * TILE_SIZE)
        self.center = MAP_TILES // 2
        self.tiles = [[GRASS] * MAP_TILES for _ in range(MAP_TILES)]
        self.obstacles = []
        self.solid_by_tile = {}
        self.blocked = set()

        self.house_image = load_obstacle(f"city_assets/{city}/house.png", (190, 150, 110))
        self.tree_image = load_obstacle("city_assets/tiles/tree_tile.png", (40, 110, 50))

        rows = self.add_roads(rng, style, horizontal=True)
        columns = self.add_roads(rng, style, horizontal=False)
        self.add_water(rng, style["water"], rows, columns)
        self.add_border_trees()
        self.add_houses(rng, style["house_density"])
        self.add_trees(rng, style["tree_density"])
        self.floor = self.build_floor(rng)

    def in_start_area(self, x, y):
        return abs(x - self.center) <= START_AREA_TILES and abs(y - self.center) <= START_AREA_TILES

    def inside(self, x, y):
        return 1 <= x < self.size - 1 and 1 <= y < self.size - 1

    def pick_lines(self, rng, count):
        lines = [self.center]
        for _ in range(200):
            if len(lines) >= count:
                break
            line = rng.randint(3, self.size - 4)
            if all(abs(line - other) >= MIN_ROAD_GAP for other in lines):
                lines.append(line)
        return lines

    def add_roads(self, rng, style, horizontal):
        lines = self.pick_lines(rng, style["roads_h"] if horizontal else style["roads_v"])
        for line in lines:
            for i in range(1, self.size - 1):
                x, y = (i, line) if horizontal else (line, i)
                self.tiles[y][x] = ROAD
        return lines

    def set_water(self, x, y):
        if self.inside(x, y) and self.tiles[y][x] == GRASS and not self.in_start_area(x, y):
            self.tiles[y][x] = WATER

    def add_water(self, rng, kind, rows, columns):
        if kind == "canals":
            canals = [(True, row) for row in rows] + [(False, column) for column in columns]
            chosen = [canal for canal in canals if rng.random() < CANAL_CHANCE] or [canals[-1]]
            for horizontal, line in chosen:
                for i in range(1, self.size - 1):
                    if horizontal:
                        self.set_water(i, line + 1)
                    else:
                        self.set_water(line + 1, i)
        elif kind == "coast":
            width = rng.randint(*COAST_WIDTH)
            side = rng.choice(["top", "bottom", "left", "right"])
            for i in range(1, self.size - 1):
                for depth in range(1, width + 1):
                    x, y = {"top": (i, depth), "bottom": (i, self.size - 1 - depth),
                            "left": (depth, i), "right": (self.size - 1 - depth, i)}[side]
                    self.set_water(x, y)
        else:
            for _ in range(rng.randint(*POND_COUNT)):
                center_x, center_y = rng.randint(4, self.size - 5), rng.randint(4, self.size - 5)
                radius = rng.uniform(*POND_RADIUS)
                for y in range(int(center_y - radius), int(center_y + radius) + 1):
                    for x in range(int(center_x - radius), int(center_x + radius) + 1):
                        if (x - center_x) ** 2 + (y - center_y) ** 2 <= radius ** 2:
                            self.set_water(x, y)

    def add_obstacle(self, image, x, y, solid):
        obstacle = Obstacle(image, x, y, solid)
        self.obstacles.append(obstacle)
        self.blocked.add((x, y))
        if solid is None:
            return
        for tile_y in range(solid.top // TILE_SIZE, solid.bottom // TILE_SIZE + 1):
            for tile_x in range(solid.left // TILE_SIZE, solid.right // TILE_SIZE + 1):
                self.solid_by_tile.setdefault((tile_x, tile_y), []).append(solid)

    def add_border_trees(self):
        last = self.size - 1
        for i in range(self.size):
            for x, y in ((i, 0), (i, last), (0, i), (last, i)):
                if (x, y) not in self.blocked:
                    self.add_obstacle(self.tree_image, x, y, None)

    def free_grass(self, x, y):
        return (self.inside(x, y) and self.tiles[y][x] == GRASS and (x, y) not in self.blocked
                and not self.in_start_area(x, y))

    def next_to_road(self, x, y):
        return any(self.tiles[y + dy][x + dx] == ROAD for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))

    def add_houses(self, rng, density):
        visible = self.house_image.get_bounding_rect()
        solid_height = round(visible.height * HOUSE_SOLID_PART)
        for y in range(1, self.size - 1):
            for x in range(1, self.size - 1):
                road_above = self.tiles[y - 1][x] == ROAD
                if self.free_grass(x, y) and self.next_to_road(x, y) and not road_above and rng.random() < density:
                    left = (x + 0.5) * TILE_SIZE - OBSTACLE_SIZE / 2 + visible.left
                    solid = pygame.Rect(round(left), (y + 1) * TILE_SIZE - solid_height, visible.width, solid_height)
                    self.add_obstacle(self.house_image, x, y, solid)

    def add_trees(self, rng, density):
        visible = self.tree_image.get_bounding_rect()
        width = round(visible.width * TREE_TRUNK_WIDTH)
        height = round(visible.height * TREE_TRUNK_HEIGHT)
        for y in range(1, self.size - 1):
            for x in range(1, self.size - 1):
                if self.free_grass(x, y) and rng.random() < density:
                    solid = pygame.Rect(0, 0, width, height)
                    solid.midbottom = ((x + 0.5) * TILE_SIZE, (y + 1) * TILE_SIZE)
                    self.add_obstacle(self.tree_image, x, y, solid)

    def build_floor(self, rng):
        images = {kind: load_tile(kind) for kind in TILE_FILES}
        shade = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        floor = pygame.Surface((self.width, self.height)).convert()
        for y in range(self.size):
            for x in range(self.size):
                kind = self.tiles[y][x]
                floor.blit(images[kind], (x * TILE_SIZE, y * TILE_SIZE))
                if kind == GRASS and rng.random() < GROUND_DARKEN_CHANCE:
                    shade.fill((0, 0, 0, rng.randint(*GROUND_DARKEN_ALPHA)))
                    floor.blit(shade, (x * TILE_SIZE, y * TILE_SIZE))
        return floor

    def clamp(self, pos, radius):
        x = max(self.inner_rect.left + radius, min(pos.x, self.inner_rect.right - radius))
        y = max(self.inner_rect.top + radius, min(pos.y, self.inner_rect.bottom - radius))
        return pygame.Vector2(x, y)

    def nearby_solids(self, pos):
        tile_x, tile_y = int(pos.x // TILE_SIZE), int(pos.y // TILE_SIZE)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                yield from self.solid_by_tile.get((tile_x + dx, tile_y + dy), ())

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
        x, y = int(pos.x // TILE_SIZE), int(pos.y // TILE_SIZE)
        return 0 <= x < self.size and 0 <= y < self.size and self.tiles[y][x] == WATER

    def visible_obstacles(self, camera):
        view = pygame.Rect(round(camera.x), round(camera.y), SCREEN_WIDTH, SCREEN_HEIGHT)
        return [obstacle for obstacle in self.obstacles if view.colliderect(obstacle.rect)]

    def draw(self, surface, camera):
        view = pygame.Rect(round(camera.x), round(camera.y), SCREEN_WIDTH, SCREEN_HEIGHT)
        surface.blit(self.floor, (0, 0), area=view)
