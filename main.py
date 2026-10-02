import random

import pygame

from subfunctions.player import Player

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
ARENA_MARGIN = 40

BACKGROUND_COLOR = (25, 25, 35)
ARENA_BORDER_COLOR = (70, 70, 90)
TEXT_COLOR = (230, 230, 230)
SHEET_COLOR = (15, 15, 25)

# Test upgrades for the U key until the shop and level-ups exist.
TEST_UPGRADES = [
    ("max_hp", {"flat": 20}),
    ("move_speed", {"percent": 0.10}),
    ("armor", {"flat": 10}),
    ("crit_rate", {"flat": 0.05}),
    ("crit_damage", {"flat": 0.25}),
    ("luck", {"percent": 0.10}),
    ("pickup_range", {"percent": 0.25}),
    ("xp_gain", {"percent": 0.10}),
    ("projectile_speed", {"percent": 0.10}),
    ("attack_speed", {"percent": 0.10}),
    ("damage", {"percent": 0.10}),
]


def draw_stat_sheet(screen, font, stats):
    rows = stats.sheet()
    line_height = font.get_linesize()
    panel = pygame.Rect(0, 0, 420, line_height * (len(rows) + 1) + 20)
    panel.topright = (SCREEN_WIDTH - 10, 10)
    pygame.draw.rect(screen, SHEET_COLOR, panel)
    pygame.draw.rect(screen, ARENA_BORDER_COLOR, panel, 2)

    y = panel.top + 10
    screen.blit(font.render("Stats", True, TEXT_COLOR), (panel.left + 12, y))
    for label, text in rows:
        y += line_height
        screen.blit(font.render(label, True, TEXT_COLOR), (panel.left + 12, y))
        value = font.render(text, True, TEXT_COLOR)
        screen.blit(value, value.get_rect(topright=(panel.right - 12, y)))


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("TouCan'tCure")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 32)

    arena = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT).inflate(-2 * ARENA_MARGIN, -2 * ARENA_MARGIN)
    player = Player(*arena.center)
    show_stats = False

    running = True
    while running:
        # Cap dt so dragging the window doesn't teleport the player.
        dt = min(clock.tick(FPS) / 1000, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t and player.alive:
                    player.take_damage(10)  # test hit, no enemies yet
                    if not player.alive:
                        print("infected")
                elif event.key == pygame.K_r:
                    player = Player(*arena.center)
                elif event.key == pygame.K_TAB:
                    show_stats = not show_stats
                elif event.key == pygame.K_u:
                    name, bonus = random.choice(TEST_UPGRADES)
                    player.stats.add(name, **bonus)  # test upgrade, no shop yet
                    print("upgrade:", name, bonus)

        if player.alive:
            player.update(dt, pygame.key.get_pressed(), arena)

        screen.fill(BACKGROUND_COLOR)
        pygame.draw.rect(screen, ARENA_BORDER_COLOR, arena, 2)
        player.draw(screen)

        hp_text = font.render(f"HP: {player.hp:.0f}/{player.max_hp:.0f}", True, TEXT_COLOR)
        screen.blit(hp_text, (10, 10))
        if not player.alive:
            dead_text = font.render("infected - press R to restart", True, TEXT_COLOR)
            screen.blit(dead_text, dead_text.get_rect(center=arena.center))
        if show_stats:
            draw_stat_sheet(screen, font, player.stats)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
