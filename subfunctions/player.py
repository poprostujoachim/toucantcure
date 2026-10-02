import pygame

from subfunctions.stats import PlayerStats


class Player(pygame.sprite.Sprite):
    def __init__(self, start_x, start_y, radius=20):
        super().__init__()
        self.pos = pygame.Vector2(start_x, start_y)
        self.radius = radius
        self.stats = PlayerStats()

    # Shortcuts so other code can write player.hp instead of player.stats.hp.
    @property
    def hp(self):
        return self.stats.hp

    @property
    def max_hp(self):
        return self.stats.max_hp.value

    @property
    def alive(self):
        return self.stats.alive

    def take_damage(self, amount):
        self.stats.take_damage(amount)

    def update(self, delta_time, keys, bounds):
        speed = self.stats.move_speed.value
        if keys[pygame.K_z]:
            self.pos.y -= speed * delta_time
        if keys[pygame.K_s]:
            self.pos.y += speed * delta_time
        if keys[pygame.K_q]:
            self.pos.x -= speed * delta_time
        if keys[pygame.K_d]:
            self.pos.x += speed * delta_time

        # bounds is the arena Rect, so stay inside it rather than the screen.
        self.pos.x = max(bounds.left + self.radius, min(self.pos.x, bounds.right - self.radius))
        self.pos.y = max(bounds.top + self.radius, min(self.pos.y, bounds.bottom - self.radius))

    def draw(self, surface):
        pygame.draw.circle(surface, "red", self.pos, self.radius)
