import argparse
import math
import os
import random
import sys
import time
import traceback

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from game.game import Game
from game.settings import MAX_ENEMIES, WEAPON_STATS
from game.weapons import make_weapon

DT = 1 / 60
DRAW_EVERY = 10


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--minutes", type=float, default=6)
    parser.add_argument("--city", default="Leiden")
    parser.add_argument("--tier", type=int, default=1)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    random.seed(args.seed)

    game = Game()
    game.start_run(args.city, args.tier)
    run = game.current_run
    run.player.stats.add("max_hp", flat=1_000_000)

    other_weapons = [name for name in WEAPON_STATS if name != "syringe"]
    weapon_time = args.minutes * 60 / (len(other_weapons) + 1)

    frames = int(args.minutes * 60 / DT)
    max_enemies = 0
    boss_seen = False
    started = time.perf_counter()
    try:
        for frame in range(frames):
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
                print(f"FAIL: {normal_enemies} enemies alive (max {MAX_ENEMIES})")
                return 1
    except Exception:
        traceback.print_exc()
        print("FAIL: crashed")
        return 1

    player = run.player
    print(f"city {args.city}, simulated {run.time / 60:.1f} min in {time.perf_counter() - started:.1f} s real time")
    print(f"state {run.state}, kills {player.kills}, level {player.level}, wave {run.spawner.wave_number}")
    print(f"weapons: {', '.join(f'{w.display_name} Lv {w.level}' for w in player.weapons)}")
    print(f"max enemies alive {max_enemies}, boss spawned {boss_seen}, boss killed {run.state == 'victory'}")
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
