import random

import pygame

from game.assets import load_frames
from game.settings import (DART_SIZE, EFFECT_TIME, IV_BAG_SIZE, LIGHTNING_COLOR, LIGHTNING_TIME, MAX_WEAPON_LEVEL,
                           SLASH_TIME, SPLASH_COLOR, SPRAY_COLOR, SWING_COLOR, SYRINGE_AIM_ASSIST, WEAPON_STATS)


def nearest_enemy(enemies, pos, max_dist, exclude=()):
    best, best_dist_sq = None, max_dist ** 2
    for enemy in enemies:
        if not enemy.alive or enemy in exclude:
            continue
        dist_sq = enemy.pos.distance_squared_to(pos)
        if dist_sq < best_dist_sq:
            best, best_dist_sq = enemy, dist_sq
    return best


def enemies_in_cone(enemies, origin, direction, radius, angle_deg):
    hits = []
    for enemy in enemies:
        if not enemy.alive:
            continue
        offset = enemy.pos - origin
        dist_sq = offset.length_squared()
        if dist_sq > (radius + enemy.radius) ** 2:
            continue
        angle = (direction.angle_to(offset) + 180) % 360 - 180
        if angle_deg >= 360 or dist_sq < 1 or abs(angle) <= angle_deg / 2:
            hits.append(enemy)
    return hits


def arc_points(origin, direction, radius, angle_deg, steps=12):
    start = -angle_deg / 2
    return [origin + direction.rotate(start + angle_deg * i / steps) * radius for i in range(steps + 1)]


class Weapon:
    name = "base"

    def __init__(self, player):
        self.player = player
        self.level = 1
        self.timer = 0.0
        self.bonus = {}
        self.info = WEAPON_STATS[self.name]

    @property
    def display_name(self):
        return self.info["display_name"]

    def stat(self, key):
        value = self.info["base"].get(key, 0)
        for level in range(2, self.level + 1):
            value += self.info["upgrades"][level].get(key, 0)
        return value + self.bonus.get(key, 0)

    def hit(self, enemy, key="damage", knockback_from=None):
        damage, crit = self.player.stats.roll_damage(self.stat(key))
        enemy.take_damage(damage, knockback_from, crit)

    def cooldown(self, key="cooldown"):
        return self.player.stats.cooldown(self.stat(key))

    def projectile_speed(self, key="speed"):
        return self.player.stats.projectile_velocity(self.stat(key))

    def update(self, dt, run):
        self.timer -= dt
        if self.timer <= 0 and self.fire(run):
            self.timer = self.cooldown()

    def fire(self, run):
        return True

    def upgrade(self):
        self.level = min(MAX_WEAPON_LEVEL, self.level + 1)

    def draw(self, surface, camera):
        pass


class Syringe(Weapon):
    name = "syringe"

    def fire(self, run):
        count = int(self.stat("count") + self.player.stats.extra_projectiles.value)
        spread = self.stat("spread")
        aim = self.aim_direction(run)
        first_angle = -spread * (count - 1) / 2
        for i in range(count):
            direction = aim.rotate(first_angle + i * spread)
            run.projectiles.append(Dart(self, self.player.pos, direction))
        return True

    def aim_direction(self, run):
        facing = self.player.facing
        reach = self.stat("speed") * self.stat("lifetime")
        in_front = enemies_in_cone(run.enemies, self.player.pos, facing, reach, SYRINGE_AIM_ASSIST * 2)
        if not in_front:
            return facing
        target = min(in_front, key=lambda e: e.pos.distance_squared_to(self.player.pos))
        to_target = target.pos - self.player.pos
        return to_target.normalize() if to_target.length_squared() > 0 else facing


class SanitizingSpray(Weapon):
    name = "spray"

    def fire(self, run):
        origin, facing = self.player.pos, self.player.facing
        radius, angle = self.stat("radius"), self.stat("angle")
        for enemy in enemies_in_cone(run.enemies, origin, facing, radius, angle):
            self.hit(enemy, knockback_from=origin)
        run.effects.append(ArcEffect(origin, facing, radius, angle, SPRAY_COLOR, EFFECT_TIME, filled=True))
        return True


class Defibrillator(Weapon):
    name = "defibrillator"

    def fire(self, run):
        target = nearest_enemy(run.enemies, self.player.pos, self.stat("range"))
        if target is None:
            return False
        hit = []
        points = [pygame.Vector2(self.player.pos)]
        while target is not None and len(hit) < self.stat("chains"):
            self.hit(target)
            hit.append(target)
            points.append(pygame.Vector2(target.pos))
            target = nearest_enemy(run.enemies, target.pos, self.stat("chain_range"), exclude=hit)
        run.effects.append(LightningEffect(points))
        return True


class IVBag(Weapon):
    name = "iv_bag"

    def __init__(self, player):
        super().__init__(player)
        self.bag_timer = 0.0

    def update(self, dt, run):
        self.bag_timer -= dt
        if self.bag_timer <= 0:
            target = nearest_enemy(run.enemies, self.player.pos, self.stat("bag_range"))
            if target is not None:
                self.throw_bag(run, target)
                self.bag_timer = self.cooldown("bag_cooldown")
        super().update(dt, run)

    def throw_bag(self, run, target):
        direction = target.pos - self.player.pos
        if direction.length_squared() == 0:
            direction = pygame.Vector2(self.player.facing)
        run.projectiles.append(IVBagProjectile(self.player.pos, direction.normalize(), self.projectile_speed("bag_speed"),
                                               self))

    def fire(self, run):
        origin, facing = self.player.pos, self.player.facing
        radius, angle = self.stat("swing_radius"), self.stat("swing_angle")
        for enemy in enemies_in_cone(run.enemies, origin, facing, radius, angle):
            self.hit(enemy, knockback_from=origin)
        run.effects.append(ArcEffect(origin, facing, radius, angle, SWING_COLOR, EFFECT_TIME, filled=False))
        return True


class Scalpel(Weapon):
    name = "scalpel"

    def fire(self, run):
        origin, facing = self.player.pos, self.player.facing
        radius, angle = self.stat("range"), self.stat("angle")
        hits = enemies_in_cone(run.enemies, origin, facing, radius, angle)
        if not hits:
            return False
        for enemy in hits:
            self.hit(enemy, knockback_from=origin)
        run.effects.append(ArcEffect(origin, facing, radius, min(angle, 359), SWING_COLOR, SLASH_TIME, filled=False))
        return True


WEAPON_CLASSES = {
    "syringe": Syringe,
    "spray": SanitizingSpray,
    "defibrillator": Defibrillator,
    "iv_bag": IVBag,
    "scalpel": Scalpel,
}


def make_weapon(name, player):
    return WEAPON_CLASSES[name](player)


class Dart:
    def __init__(self, weapon, pos, direction):
        self.weapon = weapon
        self.pos = pygame.Vector2(pos)
        self.velocity = direction * weapon.projectile_speed()
        self.pierce = int(weapon.stat("pierce"))
        self.lifetime = weapon.stat("lifetime")
        self.radius = 8
        self.already_hit = set()
        self.alive = True
        image = load_frames("dart.png", 1, DART_SIZE, fallback_color="lightblue")[0]
        _, angle = self.velocity.as_polar()
        self.image = pygame.transform.rotate(image, -angle)

    def update(self, dt, run):
        self.pos += self.velocity * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False
            return
        for enemy in run.enemies:
            if enemy.alive and enemy not in self.already_hit and \
                    self.pos.distance_squared_to(enemy.pos) < (self.radius + enemy.radius) ** 2:
                self.weapon.hit(enemy, knockback_from=self.pos - self.velocity.normalize() * 10)
                self.already_hit.add(enemy)
                self.pierce -= 1
                if self.pierce <= 0:
                    self.alive = False
                    return

    def draw(self, surface, camera):
        surface.blit(self.image, self.image.get_rect(center=self.pos - camera))


class IVBagProjectile:
    def __init__(self, pos, direction, speed, weapon):
        self.pos = pygame.Vector2(pos)
        self.velocity = direction * speed
        self.lifetime = weapon.stat("bag_lifetime")
        self.weapon = weapon
        self.radius = 9
        self.alive = True

    def update(self, dt, run):
        self.pos += self.velocity * dt
        self.lifetime -= dt
        touching = any(e.alive and self.pos.distance_squared_to(e.pos) < (self.radius + e.radius) ** 2
                       for e in run.enemies)
        if touching or self.lifetime <= 0:
            self.splash(run)

    def splash(self, run):
        weapon = self.weapon
        radius = weapon.stat("splash_radius")
        for enemy in enemies_in_cone(run.enemies, self.pos, pygame.Vector2(1, 0), radius, 360):
            weapon.hit(enemy, "bag_damage")
            enemy.slow(weapon.stat("slow"), weapon.stat("slow_time"))
        run.effects.append(CircleEffect(self.pos, radius, SPLASH_COLOR, EFFECT_TIME * 2))
        self.alive = False

    def draw(self, surface, camera):
        rect = pygame.Rect((0, 0), IV_BAG_SIZE)
        rect.center = self.pos - camera
        pygame.draw.rect(surface, SPLASH_COLOR, rect, border_radius=4)
        pygame.draw.rect(surface, "white", rect, 2, border_radius=4)


class ArcEffect:
    def __init__(self, origin, direction, radius, angle, color, lifetime, filled):
        self.origin = pygame.Vector2(origin)
        self.lifetime = self.time_left = lifetime
        self.alive = True
        size = int(radius * 2 + 8)
        center = pygame.Vector2(size / 2, size / 2)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        points = arc_points(center, direction, radius, angle)
        if filled:
            pygame.draw.polygon(self.image, (*color, 110), [center] + points)
        else:
            pygame.draw.lines(self.image, (*color, 220), False, points, 4)

    def update(self, dt):
        self.time_left -= dt
        self.alive = self.time_left > 0

    def draw(self, surface, camera):
        self.image.set_alpha(int(255 * self.time_left / self.lifetime))
        surface.blit(self.image, self.image.get_rect(center=self.origin - camera))


class CircleEffect:
    def __init__(self, pos, radius, color, lifetime):
        self.pos = pygame.Vector2(pos)
        self.lifetime = self.time_left = lifetime
        self.alive = True
        size = int(radius * 2)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (*color, 90), (size / 2, size / 2), radius)
        pygame.draw.circle(self.image, (*color, 200), (size / 2, size / 2), radius, 3)

    def update(self, dt):
        self.time_left -= dt
        self.alive = self.time_left > 0

    def draw(self, surface, camera):
        self.image.set_alpha(int(255 * self.time_left / self.lifetime))
        surface.blit(self.image, self.image.get_rect(center=self.pos - camera))


class LightningEffect:
    def __init__(self, points):
        self.time_left = LIGHTNING_TIME
        self.alive = True
        self.points = [points[0]]
        for start, end in zip(points, points[1:]):
            for i in range(1, 4):
                middle = start.lerp(end, i / 4)
                self.points.append(middle + (random.uniform(-10, 10), random.uniform(-10, 10)))
            self.points.append(end)

    def update(self, dt):
        self.time_left -= dt
        self.alive = self.time_left > 0

    def draw(self, surface, camera):
        screen_points = [p - camera for p in self.points]
        pygame.draw.lines(surface, LIGHTNING_COLOR, False, screen_points, 4)
        pygame.draw.lines(surface, "white", False, screen_points, 1)
