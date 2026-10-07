import pygame

from game import save
from game.assets import load_frames
from game.settings import (CREDITS_LINES, CREDITS_SCROLL_SPEED, DIFFICULTY_INFO, KEYS_CONFIRM, KEYS_DOWN, KEYS_LEFT,
                           KEYS_RIGHT, KEYS_UP, MENU_DUCK_SIZE, PLAYER_ANIMATION_FPS, SCREEN_HEIGHT, SCREEN_WIDTH, TIERS,
                           UI_COLORS, VERSION)
from game.ui import Button, centered_rect, city_name, draw_panel, draw_text, format_time, wrap_text


class MenuScreen:
    def __init__(self, game):
        self.game = game
        self.buttons = []
        self.focus = 0

    def on_enter(self):
        pass

    def update(self, dt):
        pass

    def choose(self, index):
        pass

    def back(self):
        pass

    def move_focus(self, step):
        for _ in range(len(self.buttons)):
            self.focus = (self.focus + step) % len(self.buttons)
            if self.buttons[self.focus].enabled:
                return

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            for i, button in enumerate(self.buttons):
                if button.enabled and button.rect.collidepoint(event.pos):
                    self.focus = i
        elif event.type == pygame.MOUSEBUTTONDOWN:
            for i, button in enumerate(self.buttons):
                if button.clicked(event):
                    self.choose(i)
                    return
        elif event.type == pygame.KEYDOWN:
            if event.key in KEYS_UP or event.key in KEYS_LEFT:
                self.move_focus(-1)
            elif event.key in KEYS_DOWN or event.key in KEYS_RIGHT:
                self.move_focus(1)
            elif event.key in KEYS_CONFIRM and self.buttons and self.buttons[self.focus].enabled:
                self.choose(self.focus)
            elif event.key == pygame.K_ESCAPE:
                self.back()

    def draw_buttons(self, surface):
        for i, button in enumerate(self.buttons):
            button.draw(surface, i == self.focus)

    def draw_title(self, surface, text, y=60):
        draw_text(surface, text, (SCREEN_WIDTH / 2, y), 56, UI_COLORS["accent"], center=True, shadow=True)


class TitleScreen(MenuScreen):
    def __init__(self, game):
        super().__init__(game)
        self.time = 0.0
        self.frames = load_frames("duck_front.png", 4, (MENU_DUCK_SIZE, MENU_DUCK_SIZE), fallback_color="yellow")

    def on_enter(self):
        labels = ["Play", "Shop", "Settings", "Credits", "Quit"]
        self.buttons = [Button(centered_rect(300, 54, (SCREEN_WIDTH / 2, 360 + i * 66)), label)
                        for i, label in enumerate(labels)]
        if "shop" not in self.game.screens:
            self.buttons[1].text = "Shop (coming soon)"
            self.buttons[1].enabled = False
        self.focus = 0

    def update(self, dt):
        self.time += dt

    def choose(self, index):
        if index == 4:
            self.game.running = False
        else:
            self.game.change_state(["city_select", "shop", "settings", "credits"][index])

    def draw(self, surface):
        draw_text(surface, "TouCan'tCure", (SCREEN_WIDTH / 2, 110), 110, UI_COLORS["accent"], center=True, shadow=True)
        frame = self.frames[int(self.time * PLAYER_ANIMATION_FPS) % len(self.frames)]
        surface.blit(frame, frame.get_rect(center=(SCREEN_WIDTH / 2, 240)))
        self.draw_buttons(surface)
        draw_text(surface, f"v{VERSION}", (SCREEN_WIDTH - 12, SCREEN_HEIGHT - 8), 22, UI_COLORS["muted"],
                  anchor="bottomright")


class DifficultyScreen(MenuScreen):
    def on_enter(self):
        self.buttons = []
        for i, info in enumerate(DIFFICULTY_INFO):
            rect = centered_rect(900, 96, (SCREEN_WIDTH / 2, 190 + i * 112))
            self.buttons.append(Button(rect, "", self.unlocked(info["tier"])))
        self.buttons.append(Button(centered_rect(240, 50, (SCREEN_WIDTH / 2, 660)), "Back"))
        self.focus = 0

    def unlocked(self, tier):
        if tier == "endless":
            return self.game.save["endless_unlocked"]
        return tier <= self.game.save["difficulty_unlocked"]

    def choose(self, index):
        if index == len(DIFFICULTY_INFO):
            self.back()
        else:
            self.game.start_run(self.game.selected_city, DIFFICULTY_INFO[index]["tier"])

    def back(self):
        self.game.change_state("city_select")

    def draw(self, surface):
        self.draw_title(surface, f"{city_name(self.game.selected_city)} · choose a difficulty")
        self.draw_buttons(surface)
        for info, button in zip(DIFFICULTY_INFO, self.buttons):
            color = UI_COLORS["text"] if button.enabled else UI_COLORS["disabled"]
            draw_text(surface, info["name"], (button.rect.x + 24, button.rect.y + 14), 40, color)
            tier = TIERS[info["tier"]]
            mults = f"Enemy HP x{tier['hp_mult']:g} · count x{tier['count_mult']:g} · damage x{tier['damage_mult']:g}"
            details = f"{info['length']}  ·  {info['bosses']}  ·  {mults}"
            draw_text(surface, details, (button.rect.x + 24, button.rect.y + 58), 24, UI_COLORS["muted"])
            if not button.enabled:
                draw_text(surface, f"Locked: {info['requirement']}", (button.rect.right - 24, button.rect.y + 22), 24,
                          UI_COLORS["danger"], anchor="topright")


class ResultsScreen(MenuScreen):
    def on_enter(self):
        labels = ["Retry", "City map", "Main menu"]
        self.buttons = [Button(centered_rect(240, 54, (SCREEN_WIDTH / 2 + (i - 1) * 270, 640)), label)
                        for i, label in enumerate(labels)]
        self.focus = 0

    def choose(self, index):
        run = self.game.last_run
        if index == 0:
            self.game.start_run(run.city, run.tier)
        else:
            self.game.change_state(["city_select", "title"][index - 1])

    def back(self):
        self.game.change_state("city_select")

    def draw(self, surface):
        run = self.game.last_run
        won = run.state == "victory"
        title = f"{city_name(run.city)} cured!" if won else "Marcus fainted..."
        draw_text(surface, title, (SCREEN_WIDTH / 2, 90), 80, UI_COLORS["good" if won else "danger"], center=True,
                  shadow=True)
        player = run.player
        rows = [("Time survived", format_time(run.time)), ("Kills", str(player.kills)), ("Level", str(player.level))]
        rows += [(weapon.display_name, f"Lv {weapon.level}") for weapon in player.weapons]
        rows += [(name.replace("_", " ").title(), f"Lv {level}") for name, level in player.items.items()]
        if getattr(run, "duckbucks", None) is not None:
            rows.append(("Duckbucks", str(run.duckbucks)))
        for name, count in (getattr(run, "trophies", None) or {}).items():
            rows.append((name.replace("_", " ").title(), str(count)))
        rows = rows[:10]
        draw_panel(surface, pygame.Rect(SCREEN_WIDTH / 2 - 380, 170, 760, 40 + 30 * len(rows)))
        for i, (label, value) in enumerate(rows):
            y = 190 + i * 30
            draw_text(surface, label, (SCREEN_WIDTH / 2 - 340, y), 28)
            draw_text(surface, value, (SCREEN_WIDTH / 2 + 340, y), 28, anchor="topright")
        for i, message in enumerate(self.game.last_unlocks):
            draw_text(surface, message, (SCREEN_WIDTH / 2, 575 - i * 30), 30, UI_COLORS["accent"], center=True)
        self.draw_buttons(surface)


class SettingsScreen(MenuScreen):
    VOLUMES = ["music_volume", "sfx_volume"]
    TOGGLES = ["fullscreen", "damage_numbers", "screen_shake"]
    LABELS = {"music_volume": "Music volume", "sfx_volume": "SFX volume", "fullscreen": "Fullscreen",
              "damage_numbers": "Damage numbers", "screen_shake": "Screen shake"}

    def on_enter(self):
        self.confirm_reset = False
        self.focus = 0
        self.build_buttons()

    def build_buttons(self):
        settings = self.game.save["settings"]
        labels = [f"{self.LABELS[key]}: {settings[key] * 100:.0f}%" for key in self.VOLUMES]
        labels += [f"{self.LABELS[key]}: {'On' if settings[key] else 'Off'}" for key in self.TOGGLES]
        labels.append("Click again to reset!" if self.confirm_reset else "Reset save")
        labels.append("Back")
        self.buttons = [Button((120, 140 + i * 66, 460, 54), label, size=28) for i, label in enumerate(labels)]

    def change_volume(self, key, step):
        settings = self.game.save["settings"]
        settings[key] = round(min(1.0, max(0.0, settings[key] + step)), 1)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and self.focus < len(self.VOLUMES) and (
                event.key in KEYS_LEFT or event.key in KEYS_RIGHT):
            self.change_volume(self.VOLUMES[self.focus], 0.1 if event.key in KEYS_RIGHT else -0.1)
            self.apply()
            return
        super().handle_event(event)

    def choose(self, index):
        settings = self.game.save["settings"]
        if index < len(self.VOLUMES):
            key = self.VOLUMES[index]
            settings[key] = 0.0 if settings[key] >= 1.0 else round(settings[key] + 0.1, 1)
        elif index < len(self.VOLUMES) + len(self.TOGGLES):
            key = self.TOGGLES[index - len(self.VOLUMES)]
            settings[key] = not settings[key]
            if key == "fullscreen":
                self.game.set_display_mode()
        elif index == len(self.buttons) - 2:
            if self.confirm_reset:
                self.game.save = save.fresh()
                self.game.set_display_mode()
                self.confirm_reset = False
            else:
                self.confirm_reset = True
                self.build_buttons()
                return
        else:
            self.back()
            return
        self.apply()

    def apply(self):
        self.game.write_save()
        self.build_buttons()

    def back(self):
        self.game.change_state("title")

    def draw(self, surface):
        self.draw_title(surface, "Settings")
        self.draw_buttons(surface)
        controls = [("Move", "WASD / ZQSD / arrows"), ("Dash", "Space"), ("Choose a card", "1 / 2 / 3 or click"),
                    ("Stats", "Tab"), ("Pause", "Esc or P"), ("Menus", "arrows + Enter, Esc = back"),
                    ("Volume", "left / right arrows")]
        panel = pygame.Rect(660, 140, 500, 66 * 6 + 54)
        draw_panel(surface, panel)
        draw_text(surface, "Controls", (panel.x + 24, panel.y + 18), 34, UI_COLORS["accent"])
        for i, (action, keys) in enumerate(controls):
            draw_text(surface, action, (panel.x + 24, panel.y + 74 + i * 44), 28)
            draw_text(surface, keys, (panel.right - 24, panel.y + 74 + i * 44), 26, UI_COLORS["muted"],
                      anchor="topright")


class CreditsScreen(MenuScreen):
    def on_enter(self):
        self.offset = SCREEN_HEIGHT

    def update(self, dt):
        self.offset -= CREDITS_SCROLL_SPEED * dt
        if self.offset < -sum(size + 16 for _, size in CREDITS_LINES):
            self.offset = SCREEN_HEIGHT

    def handle_event(self, event):
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self.game.change_state("title")

    def draw(self, surface):
        y = self.offset
        for text, size in CREDITS_LINES:
            color = UI_COLORS["accent"] if size >= 40 else UI_COLORS["text"]
            draw_text(surface, text, (SCREEN_WIDTH / 2, y), size, color, center=True)
            y += size + 16
        draw_text(surface, "Any key to go back", (SCREEN_WIDTH - 12, SCREEN_HEIGHT - 8), 22, UI_COLORS["muted"],
                  anchor="bottomright")


class TextScreen(MenuScreen):
    def __init__(self, game, title, paragraphs, next_state):
        super().__init__(game)
        self.title = title
        self.paragraphs = paragraphs
        self.next_state = next_state

    def handle_event(self, event):
        confirm = event.type == pygame.KEYDOWN and (event.key in KEYS_CONFIRM or event.key == pygame.K_ESCAPE)
        if confirm or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
            self.game.change_state(self.next_state)

    def draw(self, surface):
        panel = centered_rect(900, 520)
        draw_panel(surface, panel)
        draw_text(surface, self.title, (SCREEN_WIDTH / 2, panel.y + 60), 56, UI_COLORS["accent"], center=True)
        y = panel.y + 120
        for paragraph in self.paragraphs:
            for line in wrap_text(paragraph, 30, panel.width - 80):
                draw_text(surface, line, (SCREEN_WIDTH / 2, y), 30, center=True)
                y += 34
            y += 16
        draw_text(surface, "Press Enter to continue", (SCREEN_WIDTH / 2, panel.bottom - 36), 26, UI_COLORS["muted"],
                  center=True)
