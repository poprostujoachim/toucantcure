import os

import pygame

from game.assets import ASSETS_DIR, load_frames
from game.settings import (CITY_DISPLAY_NAMES, CURE_CHANCE_MAX, CURE_CHANCE_MIN, DASH_COOLDOWN, FONT_FILE,
                           HEART_SIZE, MAX_WEAPON_LEVEL, OVERLAY_ALPHA, PANEL_ALPHA, PIXEL_FONT_SCALE, SCREEN_HEIGHT,
                           SCREEN_WIDTH, TEXT_COLOR, UI_COLORS)

_fonts = {}
_panels = {}
_overlay = None


def get_font(size):
    if size not in _fonts:
        path = os.path.join(ASSETS_DIR, FONT_FILE)
        if os.path.exists(path):
            _fonts[size] = pygame.font.Font(path, max(8, round(size * PIXEL_FONT_SCALE)))
        else:
            _fonts[size] = pygame.font.Font(None, size)
    return _fonts[size]


def draw_text(surface, text, pos, size=24, color=TEXT_COLOR, center=False, anchor="topleft", shadow=False):
    font = get_font(size)
    image = font.render(str(text), True, color)
    rect = image.get_rect(**{"center" if center else anchor: pos})
    if shadow:
        surface.blit(font.render(str(text), True, (0, 0, 0)), rect.move(2, 2))
    surface.blit(image, rect)
    return rect


def city_name(city):
    return CITY_DISPLAY_NAMES.get(city, city)


class FloatingText:
    def __init__(self, text, pos, color=TEXT_COLOR, lifetime=0.6, size=22):
        self.image = get_font(size).render(text, True, color)
        self.pos = pygame.Vector2(pos)
        self.lifetime = lifetime
        self.time_left = lifetime
        self.alive = True

    def update(self, dt):
        self.pos.y -= 40 * dt
        self.time_left -= dt
        if self.time_left <= 0:
            self.alive = False

    def draw(self, surface, camera):
        self.image.set_alpha(int(255 * self.time_left / self.lifetime))
        surface.blit(self.image, self.image.get_rect(center=self.pos - camera))


class Button:
    def __init__(self, rect, text, enabled=True, size=30):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.enabled = enabled
        self.size = size

    def draw(self, surface, focused=False):
        active = focused and self.enabled
        if active:
            border = UI_COLORS["accent"]
        elif self.enabled:
            border = UI_COLORS["panel_border"]
        else:
            border = UI_COLORS["disabled"]
        draw_panel(surface, self.rect, color=UI_COLORS["panel_hover" if active else "panel"], border_color=border,
                   radius=10)
        color = UI_COLORS["text"] if self.enabled else UI_COLORS["disabled"]
        draw_text(surface, self.text, self.rect.center, self.size, color, center=True)

    def clicked(self, event):
        return (self.enabled and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.rect.collidepoint(event.pos))


def format_time(seconds):
    return f"{int(seconds) // 60:02d}:{int(seconds) % 60:02d}"


def centered_rect(width, height, center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)):
    rect = pygame.Rect(0, 0, width, height)
    rect.center = center
    return rect


def draw_bar(surface, rect, fraction, color, border=False):
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, UI_COLORS["bar_back"], rect, border_radius=3)
    fill = rect.copy()
    fill.width = round(rect.width * max(0.0, min(1.0, fraction)))
    if fill.width > 0:
        pygame.draw.rect(surface, color, fill, border_radius=3)
    if border:
        pygame.draw.rect(surface, UI_COLORS["panel_border"], rect, 1, border_radius=3)


def draw_panel(surface, rect, color=None, alpha=None, border_color=None, radius=12):
    rect = pygame.Rect(rect)
    color = color or UI_COLORS["panel"]
    if alpha is None:
        pygame.draw.rect(surface, color, rect, border_radius=radius)
    else:
        key = (rect.size, color, alpha, radius)
        if key not in _panels:
            panel = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(panel, (*color, alpha), panel.get_rect(), border_radius=radius)
            _panels[key] = panel
        surface.blit(_panels[key], rect)
    pygame.draw.rect(surface, border_color or UI_COLORS["panel_border"], rect, 2, border_radius=radius)


def dim_screen(surface):
    global _overlay
    if _overlay is None:
        _overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        _overlay.fill((0, 0, 0, OVERLAY_ALPHA))
    surface.blit(_overlay, (0, 0))


def wrap_text(text, size, max_width):
    font = get_font(size)
    lines, line = [], ""
    for word in text.split():
        test = f"{line} {word}".strip()
        if font.size(test)[0] <= max_width:
            line = test
        else:
            lines.append(line)
            line = word
    lines.append(line)
    return lines


def draw_arrow(surface, center, up, color, size=10):
    x, y = center
    if up:
        points = [(x, y - size), (x - size, y + size * 0.6), (x + size, y + size * 0.6)]
    else:
        points = [(x, y + size), (x - size, y - size * 0.6), (x + size, y - size * 0.6)]
    pygame.draw.polygon(surface, color, points)


def draw_level_pips(surface, pos, level, color):
    x, y = pos
    for i in range(MAX_WEAPON_LEVEL):
        pip = pygame.Rect(x + i * 14, y, 10, 10)
        if i < level:
            pygame.draw.rect(surface, color, pip, border_radius=2)
        else:
            pygame.draw.rect(surface, UI_COLORS["muted"], pip, 1, border_radius=2)


def draw_player_hp_bar(surface, player, camera):
    pos = player.pos - camera
    draw_bar(surface, (pos.x - 20, pos.y + 30, 40, 5), player.hp / player.max_hp, UI_COLORS["hp"])


def draw_hud(surface, run):
    player = run.player
    draw_bar(surface, (0, 0, SCREEN_WIDTH, 16), player.xp / player.xp_to_next(), UI_COLORS["xp"])
    draw_text(surface, f"LV {player.level}", (SCREEN_WIDTH - 10, 0), 22, anchor="topright", shadow=True)

    draw_panel(surface, (10, 24, 400, 96), alpha=PANEL_ALPHA)
    heart = load_frames("heart.png", 1, HEART_SIZE, fallback_color="red")[0]
    surface.blit(heart, (22, 36))
    hp_bar = pygame.Rect(52, 36, 346, 20)
    draw_bar(surface, hp_bar, player.hp / player.max_hp, UI_COLORS["hp"], border=True)
    draw_text(surface, f"{player.hp:.0f} / {player.max_hp:.0f}", hp_bar.center, 22, center=True, shadow=True)
    city = city_name(run.level.get("city", run.city))
    draw_text(surface, f"{city} · {run.disease['name']} · Wave {run.spawner.wave_number}", (22, 66), 22,
              UI_COLORS["muted"])
    draw_text(surface, f"Cure rate {player.stats.cure_chance.value * 100:.0f}%", (22, 90), 22, UI_COLORS["good"])

    draw_text(surface, format_time(run.time), (SCREEN_WIDTH / 2, 44), 46, center=True, shadow=True)
    draw_panel(surface, (SCREEN_WIDTH - 170, 24, 160, 40), alpha=PANEL_ALPHA)
    draw_text(surface, f"Kills {player.kills}", (SCREEN_WIDTH - 90, 44), 26, center=True)

    if player.weapons:
        height = 18 + 30 * len(player.weapons)
        draw_panel(surface, (10, SCREEN_HEIGHT - 10 - height, 320, height), alpha=PANEL_ALPHA)
        for i, weapon in enumerate(player.weapons):
            y = SCREEN_HEIGHT - 10 - height + 10 + i * 30
            draw_text(surface, weapon.display_name, (22, y + 2), 24)
            draw_level_pips(surface, (236, y + 6), weapon.level, UI_COLORS["accent"])

    ready = 1 - player.dash_cooldown_timer / DASH_COOLDOWN
    draw_panel(surface, (SCREEN_WIDTH - 170, SCREEN_HEIGHT - 50, 160, 40), alpha=PANEL_ALPHA)
    draw_text(surface, "DASH", (SCREEN_WIDTH - 158, SCREEN_HEIGHT - 40), 22)
    draw_bar(surface, (SCREEN_WIDTH - 98, SCREEN_HEIGHT - 36, 76, 12), ready,
             UI_COLORS["text"] if ready >= 1 else UI_COLORS["muted"])

    if run.boss is not None and run.boss.alive:
        draw_text(surface, run.boss.name, (SCREEN_WIDTH / 2, 82), 26, center=True, shadow=True)
        draw_bar(surface, (SCREEN_WIDTH / 2 - 260, 96, 520, 16), run.boss.hp / run.boss.max_hp, UI_COLORS["boss"],
                 border=True)
    if run.boss_banner_timer > 0:
        draw_text(surface, "!! TOUCAN INCOMING !!", (SCREEN_WIDTH / 2, 170), 68, UI_COLORS["danger"], center=True,
                  shadow=True)


def card_rects(count):
    width, height, gap = 300, 240, 30
    total = count * width + (count - 1) * gap
    left = (SCREEN_WIDTH - total) / 2
    return [pygame.Rect(left + i * (width + gap), SCREEN_HEIGHT / 2 - height / 2, width, height) for i in range(count)]


def draw_level_up(surface, cards):
    dim_screen(surface)
    draw_text(surface, "LEVEL UP!", (SCREEN_WIDTH / 2, 140), 64, UI_COLORS["accent"], center=True, shadow=True)
    draw_text(surface, "Choose one: 1 / 2 / 3 or click", (SCREEN_WIDTH / 2, 190), 28, UI_COLORS["muted"], center=True)
    mouse = pygame.mouse.get_pos()
    for i, (card, rect) in enumerate(zip(cards, card_rects(len(cards)))):
        rarity = card.get("rarity", "common")
        hovered = rect.collidepoint(mouse)
        draw_panel(surface, rect, color=UI_COLORS["panel_hover" if hovered else "panel"],
                   border_color=UI_COLORS[rarity])
        draw_text(surface, str(i + 1), (rect.x + 14, rect.y + 10), 28, UI_COLORS["muted"])
        if rarity != "common":
            draw_text(surface, rarity.title(), (rect.right - 14, rect.y + 12), 22, UI_COLORS[rarity], anchor="topright")
        top = rect.y + 44
        if card.get("icon") is not None:
            surface.blit(card["icon"], card["icon"].get_rect(midtop=(rect.centerx, top)))
            top += card["icon"].get_height() + 8
        draw_text(surface, card["title"], (rect.centerx, top + 12), 30, center=True)
        draw_text(surface, card.get("subtitle", ""), (rect.centerx, top + 42), 22, UI_COLORS["accent"], center=True)
        for j, line in enumerate(wrap_text(card["desc"], 24, rect.width - 30)):
            draw_text(surface, line, (rect.centerx, top + 80 + j * 26), 24, center=True)


def draw_effect(surface, center, text, up, good):
    color = UI_COLORS["good" if good else "danger"]
    rect = draw_text(surface, text, center, 32, color, center=True)
    draw_arrow(surface, (rect.right + 16, rect.centery), up, color)


def draw_intro(surface, run):
    dim_screen(surface)
    draw_panel(surface, centered_rect(760, 420))
    house = load_frames(f"city_assets/{run.city}/house.png", 1, (120, 120), fallback_color=(190, 150, 110))[0]
    surface.blit(house, house.get_rect(midbottom=(SCREEN_WIDTH / 2, 280)))
    draw_text(surface, city_name(run.level.get("city", run.city)), (SCREEN_WIDTH / 2, 320), 72, center=True)
    draw_text(surface, run.disease["name"], (SCREEN_WIDTH / 2, 375), 40, UI_COLORS["accent"], center=True)
    cure = run.scaling["cure_chance"]
    cure_good = cure >= (CURE_CHANCE_MIN + CURE_CHANCE_MAX) / 2
    draw_effect(surface, (SCREEN_WIDTH / 2 - 150, 430), f"Cure rate {cure * 100:.0f}%", cure_good, cure_good)
    enemies = run.scaling["enemy_mult"]
    draw_effect(surface, (SCREEN_WIDTH / 2 + 150, 430), f"Infected x{enemies:.2f}", enemies > 1, enemies <= 1)
    draw_text(surface, "Press any key to start", (SCREEN_WIDTH / 2, 500), 26, UI_COLORS["muted"], center=True)


def draw_stat_sheet(surface, stats):
    rows = stats.sheet()
    line_height = 26
    panel = pygame.Rect(0, 0, 380, line_height * (len(rows) + 1) + 24)
    panel.topright = (SCREEN_WIDTH - 10, 100)
    draw_panel(surface, panel, radius=10)
    y = panel.top + 12
    draw_text(surface, "Stats  (Tab)", (panel.left + 14, y), 26, UI_COLORS["accent"])
    for label, text in rows:
        y += line_height
        draw_text(surface, label, (panel.left + 14, y), 24)
        draw_text(surface, text, (panel.right - 14, y), 24, anchor="topright")


def draw_pause(surface):
    dim_screen(surface)
    center_x = (SCREEN_WIDTH - 400) / 2
    draw_panel(surface, centered_rect(520, 200, (center_x, SCREEN_HEIGHT / 2)))
    draw_text(surface, "Paused", (center_x, SCREEN_HEIGHT / 2 - 30), 72, center=True)
    draw_text(surface, "Esc / P to resume  ·  Q to main menu", (center_x, SCREEN_HEIGHT / 2 + 34), 28,
              UI_COLORS["muted"], center=True)


def draw_end_banner(surface, title, good):
    dim_screen(surface)
    draw_text(surface, title, (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2), 84, UI_COLORS["good" if good else "danger"],
              center=True, shadow=True)
