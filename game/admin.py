import random

import pygame

from game.settings import ADMIN_SPAWN_DISTANCE, ENEMY_TYPES, MAX_ENEMIES, UI_COLORS
from game.ui import draw_panel, draw_text


class AdminPanel:
    def __init__(self, run):
        self.run = run
        self.buttons = [
            (self.pause_label, self.toggle_pause),
            (self.invincible_label, self.toggle_invincible),
            ("Level up", self.level_up),
            ("Heal", self.heal),
            ("Kill enemies", self.kill_enemies),
            ("Spawn boss", self.spawn_boss),
            ("Swarm", run.spawner.spawn_swarm),
        ] + [(f"+ {name}", lambda name=name: self.spawn(name)) for name in ENEMY_TYPES]
        self.rects = [pygame.Rect(10, 154 + i * 30, 160, 26) for i in range(len(self.buttons))]

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False
        for (_, action), rect in zip(self.buttons, self.rects):
            if rect.collidepoint(event.pos):
                action()
                return True
        return False

    def draw(self, surface):
        draw_text(surface, "ADMIN", (14, 128), 24, UI_COLORS["accent"], shadow=True)
        mouse = pygame.mouse.get_pos()
        for (label, _), rect in zip(self.buttons, self.rects):
            color = UI_COLORS["panel_hover"] if rect.collidepoint(mouse) else UI_COLORS["panel"]
            draw_panel(surface, rect, color=color, radius=6)
            draw_text(surface, label() if callable(label) else label, rect.center, 22, center=True)

    def pause_label(self):
        return "Resume" if self.run.state == "paused" else "Pause"

    def toggle_pause(self):
        if self.run.state == "paused":
            self.run.state = "playing"
        elif self.run.state == "playing":
            self.run.state = "paused"

    def invincible_label(self):
        return f"Invincible: {'ON' if self.run.player.invincible else 'OFF'}"

    def toggle_invincible(self):
        self.run.player.invincible = not self.run.player.invincible

    def level_up(self):
        self.run.player.level += 1
        self.run.pending_level_ups += 1
        self.run.open_level_up()

    def heal(self):
        self.run.player.heal(self.run.player.stats.max_hp.value)

    def kill_enemies(self):
        for enemy in self.run.enemies:
            if enemy is not self.run.boss:
                enemy.alive = False
                self.run.on_enemy_defeated(enemy)
        self.run.enemies = [e for e in self.run.enemies if e.alive]

    def spawn_boss(self):
        if self.run.boss is None or not self.run.boss.alive:
            self.run.spawn_boss(self.spawn_point())

    def spawn(self, type_name):
        if len(self.run.enemies) < MAX_ENEMIES:
            self.run.spawner.spawn(type_name, self.spawn_point())

    def spawn_point(self):
        offset = pygame.Vector2(ADMIN_SPAWN_DISTANCE, 0).rotate(random.uniform(0, 360))
        return self.run.arena.resolve(self.run.player.pos + offset, 30)
