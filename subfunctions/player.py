import pygame


class Player(pygame.sprite.Sprite):
    def __init__(self, start_x, start_y, speed=300, radius=20):
        super().__init__()
        self.pos = pygame.Vector2(start_x, start_y)
        self.speed = speed
        self.radius = radius

    def update(self, keys, delta_time, bounds):
        if keys[pygame.K_z]:
            self.pos.y -= self.speed * delta_time
        if keys[pygame.K_s]:
            self.pos.y += self.speed * delta_time
        if keys[pygame.K_q]:
            self.pos.x -= self.speed * delta_time
        if keys[pygame.K_d]:
            self.pos.x += self.speed * delta_time

        width, height = bounds
        self.pos.x = max(self.radius, min(self.pos.x, width - self.radius))
        self.pos.y = max(self.radius, min(self.pos.y, height - self.radius))

    def draw(self, surface):
        pygame.draw.circle(surface, "red", self.pos, self.radius)
