import pygame

from game.assets import load_frames
from game.settings import (CARD_BORDER_COLOR, CARD_COLOR, CARD_HOVER_COLOR, DASH_COOLDOWN, HEART_SIZE, HUD_BAR_BACK,
                           HUD_BOSS_COLOR, HUD_HP_COLOR, HUD_XP_COLOR, OVERLAY_COLOR, SCREEN_HEIGHT, SCREEN_WIDTH,
                           TEXT_COLOR)

_fonts = {}


def get_font(size):
    if size not in _fonts:
        _fonts[size] = pygame.font.Font(None, size)
    return _fonts[size]


def draw_text(surface, text, pos, size=24, color=TEXT_COLOR, center=False):
    image = get_font(size).render(str(text), True, color)
    rect = image.get_rect(center=pos) if center else image.get_rect(topleft=pos)
    surface.blit(image, rect)
    return rect


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


_overlay = None


def format_time(seconds):
    return f"{int(seconds) // 60:02d}:{int(seconds) % 60:02d}"


def draw_bar(surface, rect, fraction, color, back=HUD_BAR_BACK):
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, back, rect)
    fill = rect.copy()
    fill.width = round(rect.width * max(0.0, min(1.0, fraction)))
    pygame.draw.rect(surface, color, fill)


def dim_screen(surface):
    global _overlay
    if _overlay is None:
        _overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        _overlay.fill(OVERLAY_COLOR)
    surface.blit(_overlay, (0, 0))


def draw_panel(surface, width, height, center_y=SCREEN_HEIGHT / 2, center_x=SCREEN_WIDTH / 2):
    panel = pygame.Rect(0, 0, width, height)
    panel.center = (center_x, center_y)
    pygame.draw.rect(surface, CARD_COLOR, panel, border_radius=16)
    pygame.draw.rect(surface, CARD_BORDER_COLOR, panel, 2, border_radius=16)


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


def draw_player_hp_bar(surface, player, camera):
    pos = player.pos - camera
    draw_bar(surface, (pos.x - 20, pos.y + 30, 40, 5), player.hp / player.max_hp, HUD_HP_COLOR)


def draw_hud(surface, run):
    player = run.player
    draw_bar(surface, (0, 0, SCREEN_WIDTH, 14), player.xp / player.xp_to_next(), HUD_XP_COLOR)
    draw_text(surface, f"LV {player.level}", (SCREEN_WIDTH - 60, 0), 20)

    heart = load_frames("heart.png", 1, HEART_SIZE, fallback_color="red")[0]
    surface.blit(heart, (12, 24))
    draw_text(surface, f"{player.hp:.0f} / {player.max_hp:.0f}", (40, 24), 26)
    city = run.level.get("city", run.city)
    draw_text(surface, f"{city} · {run.disease['name']} · Wave {run.spawner.wave_number}", (12, 52), 22)
    draw_text(surface, f"Cure rate {player.stats.cure_chance.value * 100:.0f}%", (12, 74), 22, (120, 255, 140))

    draw_text(surface, format_time(run.time), (SCREEN_WIDTH / 2, 36), 40, center=True)
    draw_text(surface, f"Kills {player.kills}", (SCREEN_WIDTH - 130, 24), 26)

    for i, weapon in enumerate(player.weapons):
        draw_text(surface, f"{weapon.display_name}  Lv {weapon.level}", (12, SCREEN_HEIGHT - 30 - 24 * i), 24)

    ready = 1 - player.dash_cooldown_timer / DASH_COOLDOWN
    draw_text(surface, "DASH", (SCREEN_WIDTH - 150, SCREEN_HEIGHT - 32), 22)
    draw_bar(surface, (SCREEN_WIDTH - 100, SCREEN_HEIGHT - 28, 80, 10), ready,
             (255, 255, 255) if ready >= 1 else (120, 120, 140))

    if run.boss is not None and run.boss.alive:
        draw_text(surface, run.boss.name, (SCREEN_WIDTH / 2, 66), 24, center=True)
        draw_bar(surface, (SCREEN_WIDTH / 2 - 250, 78, 500, 12), run.boss.hp / run.boss.max_hp, HUD_BOSS_COLOR)
    if run.boss_banner_timer > 0:
        draw_text(surface, "!! TOUCAN INCOMING !!", (SCREEN_WIDTH / 2, 150), 64, (255, 90, 90), center=True)


def card_rects(count):
    width, height, gap = 300, 220, 30
    total = count * width + (count - 1) * gap
    left = (SCREEN_WIDTH - total) / 2
    return [pygame.Rect(left + i * (width + gap), SCREEN_HEIGHT / 2 - height / 2, width, height) for i in range(count)]


def draw_level_up(surface, cards):
    dim_screen(surface)
    draw_text(surface, "LEVEL UP!  Choose one (1 / 2 / 3 or click)", (SCREEN_WIDTH / 2, 160), 42, center=True)
    mouse = pygame.mouse.get_pos()
    for i, (card, rect) in enumerate(zip(cards, card_rects(len(cards)))):
        color = CARD_HOVER_COLOR if rect.collidepoint(mouse) else CARD_COLOR
        pygame.draw.rect(surface, color, rect, border_radius=12)
        pygame.draw.rect(surface, CARD_BORDER_COLOR, rect, 2, border_radius=12)
        draw_text(surface, str(i + 1), (rect.x + 14, rect.y + 10), 28, (180, 180, 200))
        draw_text(surface, card["title"], (rect.centerx, rect.y + 50), 30, center=True)
        draw_text(surface, card.get("subtitle", ""), (rect.centerx, rect.y + 82), 22, (180, 200, 255), center=True)
        for j, line in enumerate(wrap_text(card["desc"], 24, rect.width - 30)):
            draw_text(surface, line, (rect.centerx, rect.y + 125 + j * 26), 24, center=True)


def draw_intro(surface, run):
    dim_screen(surface)
    draw_panel(surface, 760, 380)
    level, scaling = run.level, run.scaling
    title = level.get("city", run.city)
    if level.get("year"):
        title += f", {level['year']}"
    draw_text(surface, title, (SCREEN_WIDTH / 2, 230), 72, center=True)
    draw_text(surface, run.disease["name"], (SCREEN_WIDTH / 2, 295), 44, (255, 200, 120), center=True)

    facts = []
    if "cases" in level:
        facts.append(f"{level['cases']:,} reported cases")
    if "vaccine_coverage" in level:
        facts.append(f"{level['vaccine_coverage'] * 100:.0f}% vaccinated")
    if facts:
        draw_text(surface, "  ·  ".join(facts), (SCREEN_WIDTH / 2, 360), 32, center=True)
    effects = f"Cure rate: {scaling['cure_chance'] * 100:.0f}%   ·   Infected: x{scaling['enemy_mult']:.2f}"
    draw_text(surface, effects, (SCREEN_WIDTH / 2, 410), 32, (120, 255, 140), center=True)
    draw_text(surface, "Press any key to start", (SCREEN_WIDTH / 2, 500), 26, (180, 180, 200), center=True)


def draw_stat_sheet(surface, stats):
    rows = stats.sheet()
    line_height = 26
    panel = pygame.Rect(0, 0, 380, line_height * (len(rows) + 1) + 24)
    panel.topright = (SCREEN_WIDTH - 10, 100)
    pygame.draw.rect(surface, CARD_COLOR, panel, border_radius=10)
    pygame.draw.rect(surface, CARD_BORDER_COLOR, panel, 2, border_radius=10)
    y = panel.top + 12
    draw_text(surface, "Stats  (Tab)", (panel.left + 14, y), 26)
    for label, text in rows:
        y += line_height
        draw_text(surface, label, (panel.left + 14, y), 24)
        value = get_font(24).render(text, True, TEXT_COLOR)
        surface.blit(value, value.get_rect(topright=(panel.right - 14, y)))


def draw_pause(surface):
    dim_screen(surface)
    center_x = (SCREEN_WIDTH - 400) / 2
    draw_panel(surface, 520, 200, center_x=center_x)
    draw_text(surface, "Paused", (center_x, SCREEN_HEIGHT / 2 - 30), 72, center=True)
    draw_text(surface, "Esc / P to resume  ·  Q to quit", (center_x, SCREEN_HEIGHT / 2 + 30), 30, center=True)


def draw_end_screen(surface, run, title):
    dim_screen(surface)
    draw_panel(surface, 760, 280, SCREEN_HEIGHT / 2 - 10)
    player = run.player
    draw_text(surface, title, (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 80), 72, center=True)
    stats = f"Time {format_time(run.time)}   ·   Kills {player.kills}   ·   Level {player.level}"
    draw_text(surface, stats, (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2), 34, center=True)
    draw_text(surface, "R to play again  ·  Esc to quit", (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 60), 28,
              (180, 180, 200), center=True)
