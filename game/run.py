import random

import pygame

from game.admin import AdminPanel
from game.boss import Boss
from game.pickups import HealthPickup, XPGem
from game.player import Player
from game.settings import (BOSS_BANNER_TIME, BOSS_SPAWN_TIME, CARD_COUNT, DEBUG, HEART_DROP_CHANCE, INTRO_TIME,
                           KEY_DASH, KEY_STAT_SHEET, MAX_PICKUPS, MAX_WEAPON_LEVEL, MAX_WEAPONS, PLACEHOLDER_HEAL,
                           SCREEN_HEIGHT, SCREEN_WIDTH, STARTING_CITY, STARTING_WEAPON, TEST_UPGRADES, WEAPON_STATS)
from game.ui import (card_rects, draw_end_screen, draw_hud, draw_intro, draw_level_up, draw_pause,
                     draw_player_hp_bar, draw_stat_sheet)
from game.waves import WaveSpawner, disease_info, level_scaling, load_level
from game.weapons import make_weapon
from game.world import Arena

CARD_KEYS = [pygame.K_1, pygame.K_2, pygame.K_3]


def build_card_pool(run):
    player = run.player
    cards = []
    for weapon in player.weapons:
        if weapon.level < MAX_WEAPON_LEVEL:
            next_level = weapon.level + 1
            cards.append({"kind": "weapon_upgrade", "title": weapon.display_name,
                          "subtitle": f"Lv {weapon.level} -> {next_level}",
                          "desc": weapon.info["upgrades"][next_level]["desc"], "apply": weapon.upgrade})

    owned = [weapon.name for weapon in player.weapons]
    if len(player.weapons) < MAX_WEAPONS:
        for name, info in WEAPON_STATS.items():
            if name not in owned:
                cards.append({"kind": "new_weapon", "title": info["display_name"], "subtitle": "NEW weapon",
                              "desc": info["desc"],
                              "apply": lambda name=name: player.weapons.append(make_weapon(name, player))})

    for name, flat, percent, title in random.sample(TEST_UPGRADES, 2):
        cards.append({"kind": "stat", "title": title, "subtitle": "Stat", "desc": upgrade_text(name, flat, percent),
                      "apply": lambda name=name, flat=flat, percent=percent: player.stats.add(name, flat, percent)})
    cards.append({"kind": "stat", "title": "First Aid", "subtitle": "Stat",
                  "desc": f"Heal {PLACEHOLDER_HEAL} HP", "apply": lambda: player.heal(PLACEHOLDER_HEAL)})
    return cards


def upgrade_text(name, flat, percent):
    label = name.replace("_", " ")
    if percent:
        return f"+{percent * 100:.0f}% {label}"
    if flat < 1:
        return f"+{flat * 100:.0f}% {label}"
    return f"+{flat:g} {label}"


class Run:
    def __init__(self, game, city=STARTING_CITY, tier=1):
        self.game = game
        self.city = city
        self.tier = tier
        self.state = "intro"
        self.intro_timer = INTRO_TIME
        self.time = 0.0

        self.level = load_level(city)
        self.disease = disease_info(self.level)
        self.scaling = level_scaling(self.level)
        self.hp_mult = 1.0

        self.arena = Arena()
        self.player = Player(self, (self.arena.width / 2, self.arena.height / 2))
        self.player.stats.cure_chance.base = self.scaling["cure_chance"]
        self.player.weapons.append(make_weapon(STARTING_WEAPON, self.player))

        self.enemies = []
        self.projectiles = []
        self.enemy_projectiles = []
        self.pickups = []
        self.effects = []
        self.spawner = WaveSpawner(self, self.level, self.scaling)
        self.boss = None
        self.boss_banner_timer = 0.0
        self.pending_level_ups = 0
        self.cards = []
        self.show_stats = False

        self.camera = pygame.Vector2(0, 0)
        self.update_camera()

        # admin mode: starts paused, no waves, no automatic boss
        self.admin = AdminPanel(self) if game.admin else None
        if self.admin is not None:
            self.state = "paused"

    def handle_event(self, event):
        if self.admin is not None and self.admin.handle_event(event):
            return
        if self.state == "level_up" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(card_rects(len(self.cards))):
                if rect.collidepoint(event.pos):
                    self.choose_card(i)
                    return
        if event.type != pygame.KEYDOWN:
            return
        if event.key == KEY_STAT_SHEET:
            self.show_stats = not self.show_stats
            return

        if self.state == "intro":
            self.state = "playing"
        elif self.state == "playing":
            if event.key == KEY_DASH:
                self.player.try_dash()
            elif event.key in (pygame.K_ESCAPE, pygame.K_p):
                self.state = "paused"
            elif DEBUG:
                self.debug_keys(event.key)
        elif self.state == "paused":
            if event.key in (pygame.K_ESCAPE, pygame.K_p):
                self.state = "playing"
            elif event.key == pygame.K_q:
                self.game.running = False
        elif self.state == "level_up":
            if event.key in CARD_KEYS and CARD_KEYS.index(event.key) < len(self.cards):
                self.choose_card(CARD_KEYS.index(event.key))
        elif self.state in ("game_over", "victory"):
            if event.key == pygame.K_r:
                self.game.start_run(self.city, self.tier)
            elif event.key == pygame.K_ESCAPE:
                self.game.running = False

    def debug_keys(self, key):
        if key == pygame.K_F1:
            self.player.take_damage(10)
        elif key == pygame.K_F2:
            self.player.add_xp(self.player.xp_to_next())
        elif key == pygame.K_F3 and self.boss is None:
            self.time = max(self.time, BOSS_SPAWN_TIME - 3)
        elif key == pygame.K_F4:
            name, flat, percent, _ = random.choice(TEST_UPGRADES)
            self.player.stats.add(name, flat, percent)
            print("upgrade:", upgrade_text(name, flat, percent))

    def update(self, dt, move_override=None):
        if self.state == "intro":
            self.intro_timer -= dt
            if self.intro_timer <= 0:
                self.state = "playing"
            return
        if self.state != "playing":
            return

        self.time += dt
        self.player.update(dt, pygame.key.get_pressed(), move_override)
        if self.admin is None:
            self.spawner.update(dt)
        self.update_boss(dt)
        for enemy in self.enemies:
            enemy.update(dt)
        for projectile in self.projectiles + self.enemy_projectiles:
            projectile.update(dt, self)
        for pickup in self.pickups:
            pickup.update(dt, self.player)
        for effect in self.effects:
            effect.update(dt)

        for enemy in self.enemies:
            if not enemy.alive:
                self.on_enemy_defeated(enemy)
        self.enemies = [e for e in self.enemies if e.alive]
        self.projectiles = [p for p in self.projectiles if p.alive]
        self.enemy_projectiles = [p for p in self.enemy_projectiles if p.alive]
        self.pickups = [p for p in self.pickups if p.alive]
        self.effects = [e for e in self.effects if e.alive]

        if not self.player.alive:
            self.state = "game_over"
        elif self.boss is not None and not self.boss.alive:
            self.state = "victory"
        elif self.pending_level_ups > 0:
            self.open_level_up()
        self.update_camera()

    def update_boss(self, dt):
        self.boss_banner_timer = max(0.0, self.boss_banner_timer - dt)
        if self.boss is None and self.time >= BOSS_SPAWN_TIME and self.admin is None:
            self.spawn_boss(self.spawner.random_spawn_point())

    def spawn_boss(self, pos):
        self.boss = Boss(self, pos, hp_mult=self.hp_mult)
        self.enemies.append(self.boss)
        self.boss_banner_timer = BOSS_BANNER_TIME

    def on_enemy_defeated(self, enemy):
        self.player.kills += 1
        self.drop_gem(enemy.pos, enemy.xp)
        if self.player.stats.lucky(HEART_DROP_CHANCE):
            self.pickups.append(HealthPickup(enemy.pos))

    def drop_gem(self, pos, value):
        if len(self.pickups) >= MAX_PICKUPS:
            old_gem = next((p for p in self.pickups if isinstance(p, XPGem)), None)
            if old_gem is not None:
                old_gem.add_value(value)
                return
        self.pickups.append(XPGem(pos, value))

    def update_camera(self):
        target = self.player.pos
        self.camera.x = max(0, min(target.x - SCREEN_WIDTH / 2, self.arena.width - SCREEN_WIDTH))
        self.camera.y = max(0, min(target.y - SCREEN_HEIGHT / 2, self.arena.height - SCREEN_HEIGHT))

    def open_level_up(self):
        pool = build_card_pool(self)
        self.cards = random.sample(pool, min(CARD_COUNT, len(pool)))
        self.state = "level_up"

    def choose_card(self, index):
        self.cards[index]["apply"]()
        self.pending_level_ups -= 1
        if self.pending_level_ups > 0:
            self.open_level_up()
        else:
            self.cards = []
            self.state = "playing"

    def draw(self, surface):
        self.arena.draw(surface, self.camera)
        for pickup in self.pickups:
            pickup.draw(surface, self.camera)

        view = pygame.Rect(self.camera, (SCREEN_WIDTH, SCREEN_HEIGHT)).inflate(200, 200)
        visible = [self.player] + [e for e in self.enemies if view.collidepoint(e.pos)]
        for thing in sorted(visible, key=lambda t: t.pos.y):
            thing.draw(surface, self.camera)
        for projectile in self.projectiles + self.enemy_projectiles:
            projectile.draw(surface, self.camera)
        for effect in self.effects:
            effect.draw(surface, self.camera)

        draw_player_hp_bar(surface, self.player, self.camera)
        draw_hud(surface, self)
        if self.state == "intro":
            draw_intro(surface, self)
        elif self.state == "level_up":
            draw_level_up(surface, self.cards)
        elif self.state == "paused":
            draw_pause(surface)
        if self.show_stats or self.state == "paused":
            draw_stat_sheet(surface, self.player.stats)
        elif self.state == "game_over":
            draw_end_screen(surface, self, "Marcus fainted...")
        elif self.state == "victory":
            draw_end_screen(surface, self, f"{self.level.get('city', self.city)} cured!")
        if self.admin is not None:
            self.admin.draw(surface)
