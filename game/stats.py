import random

from game.settings import ARMOR_SCALE, MIN_COOLDOWN, PLAYER_STATS


class Stat:
    def __init__(self, base, minimum=None, maximum=None):
        self.base = base
        self.flat = 0
        self.percent = 0.0
        self.minimum = minimum
        self.maximum = maximum

    @property
    def value(self):
        value = (self.base + self.flat) * (1 + self.percent)
        if self.minimum is not None:
            value = max(self.minimum, value)
        if self.maximum is not None:
            value = min(self.maximum, value)
        return value


class PlayerStats:
    def __init__(self):
        for name, (base, minimum, maximum) in PLAYER_STATS.items():
            setattr(self, name, Stat(base, minimum, maximum))

        self.hp = self.max_hp.value

    def add(self, name, flat=0, percent=0.0):
        stat = getattr(self, name, None)
        if not isinstance(stat, Stat):
            raise KeyError(f"{name} is not a stat")
        old_max_hp = self.max_hp.value
        stat.flat += flat
        stat.percent += percent

        if stat is self.max_hp:
            self.hp = min(self.max_hp.value, self.hp + self.max_hp.value - old_max_hp)

    def damage_taken(self, amount):
        return amount * ARMOR_SCALE / (ARMOR_SCALE + self.armor.value)

    def roll_damage(self, weapon_damage, rng=random):
        damage = weapon_damage * self.damage.value
        is_crit = rng.random() < self.crit_rate.value
        if is_crit:
            damage *= self.crit_damage.value
        return damage, is_crit

    def cooldown(self, weapon_cooldown):
        return max(MIN_COOLDOWN, weapon_cooldown / self.attack_speed.value)

    def projectile_velocity(self, weapon_speed):
        return weapon_speed * self.projectile_speed.value

    def xp_from(self, amount):
        return amount * self.xp_gain.value

    def lucky(self, chance, rng=random):
        return rng.random() < min(1.0, chance * self.luck.value)

    def dodged(self, rng=random):
        return rng.random() < self.dodge_chance.value

    def cured(self, rng=random):
        return rng.random() < self.cure_chance.value

    def take_damage(self, amount):
        self.hp = max(0, self.hp - self.damage_taken(amount))

    def heal(self, amount):
        self.hp = min(self.max_hp.value, self.hp + amount)

    @property
    def alive(self):
        return self.hp > 0

    def sheet(self):
        def pct(stat):
            return f"{stat.value * 100:.0f}%"

        return [
            ("HP", f"{self.hp:.0f} / {self.max_hp.value:.0f}"),
            ("Move speed", f"{self.move_speed.value:.0f}"),
            ("Armor", f"{self.armor.value:.0f}  (-{(1 - self.damage_taken(1)) * 100:.0f}% damage)"),
            ("Regen", f"{self.regen.value:.1f} HP/s"),
            ("Dodge", pct(self.dodge_chance)),
            ("Cure rate", pct(self.cure_chance)),
            ("Damage", pct(self.damage)),
            ("Crit rate", pct(self.crit_rate)),
            ("Crit damage", f"x{self.crit_damage.value:.2f}"),
            ("Attack speed", pct(self.attack_speed)),
            ("Projectile speed", pct(self.projectile_speed)),
            ("Pickup range", f"{self.pickup_range.value:.0f}"),
            ("XP gain", pct(self.xp_gain)),
            ("Luck", pct(self.luck)),
        ]
