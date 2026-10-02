"""Player stats.

Every stat is a base value plus bonuses. Shop items and level-ups only ever add
bonuses (through PlayerStats.add), never touch the base, so the stat sheet can
always show where a number came from.

The one rule: formulas live in this file and nowhere else. Everything outside
reads `.value` (or one of the helpers below) and never does its own maths on a
stat, otherwise the stat sheet stops telling the truth.
"""
import random

# Armor uses diminishing returns: 25 armor = 20% less damage, 100 = 50%,
# 300 = 75%, and it can never reach 100%.
ARMOR_SCALE = 100

# Attacks can never fire faster than this, however much attack speed you stack.
MIN_COOLDOWN = 0.05


class Stat:
    """A base value plus flat and percent bonuses."""

    def __init__(self, base, minimum=None, maximum=None):
        self.base = base
        self.flat = 0        # +20 max hp
        self.percent = 0.0   # 0.10 = +10%, percent bonuses add together
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
        self.max_hp = Stat(100, minimum=1)
        self.move_speed = Stat(300, minimum=50)          # pixels per second
        self.armor = Stat(0, minimum=0)                  # see damage_taken()
        self.crit_rate = Stat(0.05, minimum=0, maximum=1)  # 0.05 = 5% chance
        self.crit_damage = Stat(1.5, minimum=1)          # crits deal x1.5
        self.luck = Stat(1.0, minimum=0)                 # 1.0 = normal luck
        self.pickup_range = Stat(50, minimum=0)          # pixels
        self.xp_gain = Stat(1.0, minimum=0)              # the Crown
        self.projectile_speed = Stat(1.0, minimum=0.1)   # multiplier on a weapon's speed
        self.attack_speed = Stat(1.0, minimum=0.1)       # 2.0 = attacks twice as often
        self.damage = Stat(1.0, minimum=0)               # the Spinach

        # Current hp is not a stat: it goes up and down during a run.
        self.hp = self.max_hp.value

    def add(self, name, flat=0, percent=0.0):
        """Give a bonus to one stat. This is what the shop and level-ups call.

        A typo'd stat name raises an error instead of silently doing nothing.
        """
        stat = getattr(self, name, None)
        if not isinstance(stat, Stat):
            raise KeyError(f"{name} is not a stat")
        old_max_hp = self.max_hp.value
        stat.flat += flat
        stat.percent += percent
        # Raising max hp also heals by the same amount, like picking up a heart.
        if stat is self.max_hp:
            self.hp = min(self.max_hp.value, self.hp + self.max_hp.value - old_max_hp)

    # --- formulas ---------------------------------------------------------

    def damage_taken(self, amount):
        """How much of an incoming hit actually lands after armor."""
        return amount * ARMOR_SCALE / (ARMOR_SCALE + self.armor.value)

    def roll_damage(self, weapon_damage, rng=random):
        """Damage one hit deals. Returns (damage, was_it_a_crit)."""
        damage = weapon_damage * self.damage.value
        is_crit = rng.random() < self.crit_rate.value
        if is_crit:
            damage *= self.crit_damage.value
        return damage, is_crit

    def cooldown(self, weapon_cooldown):
        """Seconds between attacks for a weapon, after attack speed."""
        return max(MIN_COOLDOWN, weapon_cooldown / self.attack_speed.value)

    def projectile_velocity(self, weapon_speed):
        return weapon_speed * self.projectile_speed.value

    def xp_from(self, amount):
        return amount * self.xp_gain.value

    def lucky(self, chance, rng=random):
        """Roll a chance boosted by luck. Use it for drops and rare upgrades."""
        return rng.random() < min(1.0, chance * self.luck.value)

    # --- hp ---------------------------------------------------------------

    def take_damage(self, amount):
        self.hp = max(0, self.hp - self.damage_taken(amount))

    def heal(self, amount):
        self.hp = min(self.max_hp.value, self.hp + amount)

    @property
    def alive(self):
        return self.hp > 0

    # --- stat sheet -------------------------------------------------------

    def sheet(self):
        """(label, text) rows for the stat sheet screen."""
        def pct(stat):
            return f"{stat.value * 100:.0f}%"

        return [
            ("HP", f"{self.hp:.0f} / {self.max_hp.value:.0f}"),
            ("Move speed", f"{self.move_speed.value:.0f}"),
            ("Armor", f"{self.armor.value:.0f}  (-{(1 - self.damage_taken(1)) * 100:.0f}% damage)"),
            ("Damage", pct(self.damage)),
            ("Crit rate", pct(self.crit_rate)),
            ("Crit damage", f"x{self.crit_damage.value:.2f}"),
            ("Attack speed", pct(self.attack_speed)),
            ("Projectile speed", pct(self.projectile_speed)),
            ("Pickup range", f"{self.pickup_range.value:.0f}"),
            ("XP gain", pct(self.xp_gain)),
            ("Luck", pct(self.luck)),
        ]
