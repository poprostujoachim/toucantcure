import pygame

from game import save
from game.city_select import CitySelectScreen
from game.menus import CreditsScreen, DifficultyScreen, ResultsScreen, SettingsScreen, TextScreen, TitleScreen
from game.run import Run
from game.settings import (BACKGROUND_COLOR, CITY_ORDER, FADE_TIME, FPS, MAX_DT, SCREEN_HEIGHT, SCREEN_WIDTH,
                           STARTING_CITY, TITLE)
from game.ui import city_name


class Game:
    def __init__(self, admin=False):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.admin = admin
        self.save = save.load()
        if admin:
            self.save["cities_unlocked"] = list(CITY_ORDER)
            self.save["difficulty_unlocked"] = 3
            self.save["endless_unlocked"] = True
        self.screen = None
        self.set_display_mode()
        self.clock = pygame.time.Clock()
        self.running = True
        self.current_run = None
        self.last_run = None
        self.last_unlocks = []
        self.selected_city = STARTING_CITY
        self.screens = {
            "title": TitleScreen(self),
            "city_select": CitySelectScreen(self),
            "difficulty": DifficultyScreen(self),
            "results": ResultsScreen(self),
            "settings": SettingsScreen(self),
            "credits": CreditsScreen(self),
        }
        self.fade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.fade_timer = 0.0
        self.state = "title"
        self.change_state("title")

    def set_display_mode(self):
        flags = pygame.FULLSCREEN | pygame.SCALED if self.save["settings"]["fullscreen"] else 0
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)

    def write_save(self):
        if not self.admin:
            save.save(self.save)

    def change_state(self, state):
        self.state = state
        self.fade_timer = FADE_TIME
        if state != "run":
            self.screens[state].on_enter()

    def start_run(self, city=STARTING_CITY, tier=1):
        self.current_run = Run(self, city, tier)
        self.change_state("run")

    def show_results(self, run):
        self.last_run = run
        self.last_unlocks = self.record_run(run)
        self.write_save()
        self.change_state("results")

    def record_run(self, run):
        stats = self.save["stats"]
        stats["runs"] += 1
        stats["kills"] += run.player.kills
        if run.state != "victory":
            return []
        stats["wins"] += 1
        if isinstance(run.tier, int):
            cured = self.save["cities_cured"]
            cured[run.city] = max(cured.get(run.city, 0), run.tier)
        if run.city not in CITY_ORDER or run.city == CITY_ORDER[-1]:
            return []
        next_city = CITY_ORDER[CITY_ORDER.index(run.city) + 1]
        if next_city in self.save["cities_unlocked"]:
            return []
        self.save["cities_unlocked"].append(next_city)
        return [f"NEW: {city_name(next_city)} unlocked!"]

    def show_text(self, title, paragraphs, next_state):
        self.screens["text"] = TextScreen(self, title, paragraphs, next_state)
        self.change_state("text")

    def active_screen(self):
        return self.current_run if self.state == "run" else self.screens[self.state]

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000, MAX_DT)
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                self.active_screen().handle_event(event)

    def update(self, dt):
        self.fade_timer = max(0.0, self.fade_timer - dt)
        self.active_screen().update(dt)

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        self.active_screen().draw(self.screen)
        if self.fade_timer > 0:
            self.fade.set_alpha(int(255 * self.fade_timer / FADE_TIME))
            self.screen.blit(self.fade, (0, 0))
        pygame.display.flip()
