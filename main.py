import pygame

from subfunctions.generation import generate_terrain
from subfunctions.enemy import Enemy
from subfunctions.player import Player

WIDTH, HEIGHT = 1280, 720
FPS = 24


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    background_surface = generate_terrain(WIDTH, HEIGHT)
    player = Player(WIDTH / 2, HEIGHT / 2)
    enemy = Enemy(100, 100)

    running = True
    dt = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        player.update(keys, dt, (WIDTH, HEIGHT))
        enemy.update(player.pos, dt)

        screen.blit(background_surface, (0, 0))
        enemy.draw(screen)
        player.draw(screen)

        pygame.display.flip()

        dt = clock.tick(FPS) / 1000

    pygame.quit()


if __name__ == '__main__':
    main()
