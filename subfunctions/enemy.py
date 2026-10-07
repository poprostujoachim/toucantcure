import os
import random

import pygame

ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')

FRAME_COUNT = 4
ANIMATION_FPS = 8


# Enemy projectiles are their own sprite so we can track their lifetime, movement,
# and collision separately from the enemy itself.
class EnemyProjectile(pygame.sprite.Sprite):
    def __init__(self, start_x, start_y, target_pos, speed=220, radius=6, damage=10, lifetime=3.0):
        super().__init__()
        self.pos = pygame.Vector2(start_x, start_y)
        self.radius = radius
        self.damage = damage
        self.speed = speed
        self.lifetime = lifetime
        self.age = 0.0

        direction = target_pos - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
        self.velocity = direction * speed

    def update(self, delta_time):
        self.pos += self.velocity * delta_time
        self.age += delta_time
        return self.age >= self.lifetime  # True when the projectile has expired and should be removed.

    def draw(self, surface):
        pygame.draw.circle(surface, "orange", (round(self.pos.x), round(self.pos.y)), self.radius)


def load_enemy_frames(size, sprite='duck_bird.png'):
    """Cut the sprite sheet into frames scaled to size, falling back to a blue circle."""
    try:
        sheet = pygame.image.load(os.path.join(ASSETS_DIR, sprite)).convert_alpha()
    except (pygame.error, FileNotFoundError):
        fallback = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(fallback, "blue", (size // 2, size // 2), size // 2)
        return [fallback]

    frame_width = sheet.get_width() // FRAME_COUNT
    frame_height = sheet.get_height()

    frames = []
    for i in range(FRAME_COUNT):
        frame = sheet.subsurface((i * frame_width, 0, frame_width, frame_height))
        frames.append(pygame.transform.scale(frame, (size, size)))
    return frames


class Enemy(pygame.sprite.Sprite):
    ATTACK_STYLES = ("projectile", "contact")
    SPRITES = {"projectile": "duck_bird.png", "contact": "duck_bacteria.png"}

    def __init__(self, start_x, start_y, speed=200, radius=20, attack_style="projectile", contact_damage=15,
                 max_hp=30, sprite=None):
        super().__init__()
        if attack_style not in self.ATTACK_STYLES:
            raise ValueError(f"attack_style must be one of {self.ATTACK_STYLES}")

        self.pos = pygame.Vector2(start_x, start_y)
        self.speed = speed
        self.radius = radius
        self.attack_style = attack_style
        self.max_hp = max_hp
        self.hp = max_hp
        self.frames = load_enemy_frames(radius * 2, sprite or self.SPRITES[attack_style])
        self.animation_time = 0  

        self.projectile_cooldown = 0.0
        self.projectile_damage = 10
        self.projectile_speed = 220

        self.contact_damage = contact_damage
        self.contact_cooldown = 0.0  # Time left before this enemy can hurt the player again by touching.
        self.contact_interval = 0.75  # Seconds between touch hits while the enemy stays on the player.

    @property
    def alive(self):
        return self.hp > 0

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)

    def fire_projectile(self, target_pos):
        return EnemyProjectile(
            self.pos.x,
            self.pos.y,
            target_pos,
            speed=self.projectile_speed,
            radius=6,
            damage=self.projectile_damage
        )

    def update(self, target_pos, delta_time):
        direction = target_pos - self.pos
        distance = direction.length()

        if distance > 0:
            direction = direction.normalize()
            self.pos += direction * self.speed * delta_time

        self.animation_time += delta_time
        self.projectile_cooldown = max(0.0, self.projectile_cooldown - delta_time)
        self.contact_cooldown = max(0.0, self.contact_cooldown - delta_time)

        projectiles = []  # Store any projectiles created this frame.
        if (self.attack_style == "projectile" and distance <= 500 and self.projectile_cooldown <= 0):  
            self.projectile_cooldown = 1.25
            projectiles.append(self.fire_projectile(target_pos))
        return projectiles

    def contact_hit(self, target_pos, target_radius):
        if self.attack_style != "contact" or self.contact_cooldown > 0:
            return 0
        if (target_pos - self.pos).length() > self.radius + target_radius:
            return 0
        self.contact_cooldown = self.contact_interval
        return self.contact_damage

    def draw(self, surface):
        frame_index = int(self.animation_time * ANIMATION_FPS) % len(self.frames)
        texture = self.frames[frame_index]
        surface.blit(texture, texture.get_rect(center=(round(self.pos.x), round(self.pos.y))))


SWARM_SIZE = (3, 8)
SWARM_SPREAD = 60 

def spawn_swarm(center_x, center_y, count=None, rng=random):
    """Create a group of swarmers scattered around (center_x, center_y)."""
    if count is None:
        count = rng.randint(*SWARM_SIZE)
    swarm = []
    for _ in range(count):
        offset = pygame.Vector2(rng.uniform(0, SWARM_SPREAD), 0).rotate(rng.uniform(0, 360))
        swarm.append(Enemy(
            center_x + offset.x,
            center_y + offset.y,
            speed=220,
            attack_style="contact",
            max_hp=10,
            sprite="duck_parasite.png",
        ))
    return swarm
