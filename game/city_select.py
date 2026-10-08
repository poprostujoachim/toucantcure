import pygame

from game.assets import load_city_house
from game.menus import MenuScreen
from game.settings import (CITY_DOT_RADIUS, CITY_MAP_NUDGE, CITY_ORDER, CITY_POSITIONS, CURE_CHANCE_MAX,
                           CURE_CHANCE_MIN, DEBUG, KEYS_LEFT, KEYS_RIGHT, MAP_MARGIN_DEGREES, MAP_RECT, UI_COLORS)
from game.ui import Button, city_name, draw_effect, draw_panel, draw_text
from game.waves import disease_info, level_scaling, load_level

INFO_RECT = pygame.Rect(880, 90, 360, 450)


def map_positions():
    lats = [lat for lat, _ in CITY_POSITIONS.values()]
    lons = [lon for _, lon in CITY_POSITIONS.values()]
    top, bottom = max(lats) + MAP_MARGIN_DEGREES, min(lats) - MAP_MARGIN_DEGREES
    left, right = min(lons) - MAP_MARGIN_DEGREES, max(lons) + MAP_MARGIN_DEGREES
    area = pygame.Rect(MAP_RECT)
    positions = {}
    for city, (lat, lon) in CITY_POSITIONS.items():
        x = area.left + (lon - left) / (right - left) * area.width
        y = area.top + (top - lat) / (top - bottom) * area.height
        positions[city] = pygame.Vector2(x, y) + CITY_MAP_NUDGE.get(city, (0, 0))
    return positions


def load_house(city, size):
    return load_city_house(city, size)


def draw_lock(surface, center, color):
    x, y = center
    pygame.draw.arc(surface, color, (x - 6, y - 12, 12, 14), 0, 3.15, 2)
    pygame.draw.rect(surface, color, (x - 8, y - 4, 16, 12), border_radius=2)


def draw_diamond(surface, center, size, color):
    x, y = center
    pygame.draw.polygon(surface, color, [(x, y - size), (x + size, y), (x, y + size), (x - size, y)])


def draw_check(surface, center, color):
    x, y = center
    pygame.draw.lines(surface, color, False, [(x - 7, y), (x - 2, y + 6), (x + 8, y - 6)], 3)


class CitySelectScreen(MenuScreen):
    def __init__(self, game):
        super().__init__(game)
        self.positions = map_positions()
        self.levels = {}
        self.selected = 0

    @property
    def city(self):
        return CITY_ORDER[self.selected]

    def on_enter(self):
        self.levels = {city: load_level(city) for city in CITY_ORDER}
        self.selected = CITY_ORDER.index(self.game.selected_city) if self.game.selected_city in CITY_ORDER else 0
        self.buttons = [Button((INFO_RECT.x + 20, 560, 320, 54), "Choose difficulty"),
                        Button((INFO_RECT.x + 20, 630, 320, 50), "Back")]
        self.focus = 0
        self.refresh()

    def unlocked(self, city):
        return city in self.game.save["cities_unlocked"]

    def status(self, city):
        if self.game.save["cities_cured"].get(city, 0):
            return "cured"
        return "unlocked" if self.unlocked(city) else "locked"

    def refresh(self):
        self.buttons[0].enabled = self.unlocked(self.city)

    def select(self, index):
        self.selected = index % len(CITY_ORDER)
        self.refresh()

    def city_at(self, pos):
        for i, city in enumerate(CITY_ORDER):
            if self.positions[city].distance_to(pos) <= CITY_DOT_RADIUS + 8:
                return i
        return None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in KEYS_LEFT or event.key in KEYS_RIGHT:
                self.select(self.selected + (1 if event.key in KEYS_RIGHT else -1))
                return
            if DEBUG and event.key == pygame.K_F5:
                self.game.save["cities_unlocked"] = list(CITY_ORDER)
                self.game.write_save()
                self.refresh()
                return
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            index = self.city_at(event.pos)
            if index is not None:
                self.select(index)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.choose(0)
                return
        super().handle_event(event)

    def choose(self, index):
        if index == 0 and self.unlocked(self.city):
            self.game.selected_city = self.city
            self.game.change_state("difficulty")
        elif index == 1:
            self.back()

    def back(self):
        self.game.change_state("title")

    def draw(self, surface):
        area = pygame.Rect(MAP_RECT)
        draw_text(surface, "Choose a city", (area.centerx, 50), 56, UI_COLORS["accent"], center=True, shadow=True)
        draw_panel(surface, area, color=(20, 34, 44))
        for x in range(area.left + 60, area.right, 60):
            pygame.draw.line(surface, (32, 48, 60), (x, area.top + 2), (x, area.bottom - 3))
        for y in range(area.top + 60, area.bottom, 60):
            pygame.draw.line(surface, (32, 48, 60), (area.left + 2, y), (area.right - 3, y))
        self.draw_path(surface)
        for i, city in enumerate(CITY_ORDER):
            self.draw_city(surface, i, city)
        self.draw_info(surface)
        self.draw_buttons(surface)

    def draw_path(self, surface):
        for start_city, end_city in zip(CITY_ORDER, CITY_ORDER[1:]):
            start, end = self.positions[start_city], self.positions[end_city]
            steps = int(start.distance_to(end) // 12)
            for step in range(1, steps):
                if step % 2 == 0:
                    pygame.draw.circle(surface, UI_COLORS["muted"], start.lerp(end, step / steps), 2)

    def draw_city(self, surface, index, city):
        pos = self.positions[city]
        status = self.status(city)
        if status != "locked":
            house = load_house(city, 48)
            surface.blit(house, house.get_rect(midleft=(pos.x + 16, pos.y - 10)))
        color = UI_COLORS[{"locked": "locked", "unlocked": "accent", "cured": "cured"}[status]]
        if index == self.selected:
            pygame.draw.circle(surface, UI_COLORS["text"], pos, CITY_DOT_RADIUS + 6, 3)
        pygame.draw.circle(surface, color, pos, CITY_DOT_RADIUS)
        if status == "locked":
            draw_lock(surface, pos, UI_COLORS["background"])
        elif status == "cured":
            draw_check(surface, pos, UI_COLORS["background"])
        label_color = UI_COLORS["muted"] if status == "locked" else UI_COLORS["text"]
        draw_text(surface, city_name(city), (pos.x, pos.y + 28), 24, label_color, center=True, shadow=True)
        tier = self.game.save["cities_cured"].get(city, 0)
        for star in range(tier):
            draw_diamond(surface, (pos.x + (star - (tier - 1) / 2) * 12, pos.y + 46), 5, UI_COLORS["accent"])

    def draw_info(self, surface):
        city = self.city
        level = self.levels.get(city, {})
        draw_panel(surface, INFO_RECT)
        center_x = INFO_RECT.centerx
        house = load_house(city, 120)
        surface.blit(house, house.get_rect(midtop=(center_x, INFO_RECT.y + 10)))
        draw_text(surface, city_name(city), (center_x, INFO_RECT.y + 160), 52, center=True)
        if "disease" in level:
            draw_text(surface, disease_info(level)["name"], (center_x, INFO_RECT.y + 210), 30, UI_COLORS["accent"],
                      center=True)
        else:
            draw_text(surface, "Data coming soon", (center_x, INFO_RECT.y + 210), 30, UI_COLORS["muted"], center=True)
        scaling = level_scaling(level)
        cure = scaling["cure_chance"]
        cure_good = cure >= (CURE_CHANCE_MIN + CURE_CHANCE_MAX) / 2
        draw_effect(surface, (center_x - 12, INFO_RECT.y + 270), f"Cure rate {cure * 100:.0f}%", cure_good, cure_good)
        enemies = scaling["enemy_mult"]
        draw_effect(surface, (center_x - 12, INFO_RECT.y + 315), f"Infected x{enemies:.2f}", enemies > 1, enemies <= 1)
        status = self.status(city)
        if status == "locked":
            previous = CITY_ORDER[self.selected - 1]
            text, color = f"Cure {city_name(previous)} to unlock", UI_COLORS["danger"]
        elif status == "cured":
            text, color = f"Cured on tier {self.game.save['cities_cured'][city]}", UI_COLORS["cured"]
        else:
            text, color = "Ready", UI_COLORS["good"]
        draw_text(surface, text, (center_x, INFO_RECT.y + 380), 28, color, center=True)
        draw_text(surface, "Left / Right: change city", (center_x, INFO_RECT.bottom - 26), 22, UI_COLORS["muted"], center=True)
