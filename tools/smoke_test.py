import argparse
import math
import os
import random
import sys
import tempfile
import time
import traceback

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from game import save
from game.game import Game
from game.settings import CITY_ORDER, MAX_ENEMIES, WEAPON_STATS
from game.weapons import make_weapon

DT = 1 / 60
DRAW_EVERY = 10
MENU_KEYS = [pygame.K_DOWN, pygame.K_DOWN, pygame.K_UP, pygame.K_RIGHT, pygame.K_LEFT]


def simulate_run(game, city, tier, minutes):
    game.start_run(city, tier)
    game.fade_timer = 0
    run = game.current_run
    run.player.stats.add("max_hp", flat=1_000_000)
    other_weapons = [name for name in WEAPON_STATS if name != "syringe"]
    weapon_time = minutes * 60 / (len(other_weapons) + 1)
    max_enemies = 0
    boss_seen = False
    started = time.perf_counter()

    for frame in range(int(minutes * 60 / DT)):
        if run.state == "intro":
            run.state = "playing"
        if run.state == "level_up":
            run.choose_card(0)
        if run.state in ("game_over", "victory"):
            break

        slot = int(run.time / weapon_time) - 1
        if 0 <= slot < len(other_weapons):
            name = other_weapons[slot]
            if len(run.player.weapons) < 2 or run.player.weapons[1].name != name:
                run.player.weapons[1:] = [make_weapon(name, run.player)]

        angle = run.time * 0.8
        run.update(DT, move_override=pygame.Vector2(math.cos(angle), math.sin(angle)))
        if frame % 300 == 0:
            run.player.try_dash()
        if frame % DRAW_EVERY == 0:
            game.draw()

        normal_enemies = sum(1 for e in run.enemies if e is not run.boss)
        max_enemies = max(max_enemies, normal_enemies)
        boss_seen = boss_seen or run.boss is not None
        if normal_enemies > MAX_ENEMIES:
            raise RuntimeError(f"{normal_enemies} enemies alive (max {MAX_ENEMIES})")
        for enemy in run.enemies:
            if not run.arena.inner_rect.collidepoint(enemy.pos):
                raise RuntimeError(f"an enemy left the map at {enemy.pos}")

    player = run.player
    print(f"{city:<11} {run.time / 60:.1f} min in {time.perf_counter() - started:.1f} s · state {run.state} · "
          f"kills {player.kills} · level {player.level} · wave {run.spawner.wave_number} · "
          f"max enemies {max_enemies} · boss spawned {boss_seen}")
    return run


def check_menus(game, run):
    game.show_results(run)
    game.show_text("Test", ["A paragraph of text for the text screen."], "title")
    for state in list(game.screens):
        game.change_state(state)
        screen = game.screens[state]
        for key in MENU_KEYS:
            screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode="", scancode=0))
            if game.state != state:
                game.change_state(state)
        game.update(DT)
        game.draw()
    print(f"menus OK: {', '.join(game.screens)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--minutes", type=float, default=None)
    parser.add_argument("--city", default="Leiden")
    parser.add_argument("--tier", type=int, default=1)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    random.seed(args.seed)
    cities = CITY_ORDER if args.city == "all" else [args.city]
    minutes = args.minutes or (1 if args.city == "all" else 6)

    save.SAVE_PATH = os.path.join(tempfile.mkdtemp(), "save.json")
    try:
        game = Game()
        run = None
        for city in cities:
            run = simulate_run(game, city, args.tier, minutes)
        check_menus(game, run)
    except Exception:
        traceback.print_exc()
        print("FAIL")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
