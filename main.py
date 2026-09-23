import pygame

from game.player import Player 

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
ARENA_MARGIN = 40

BACKGROUND_COLOR = (25, 25, 35)
ARENA_BORDER_COLOR = (70, 70, 90)
TEXT_COLOR = (230, 230, 230)


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("TouCan'tCure")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 32)

    arena = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT).inflate(-2 * ARENA_MARGIN, -2 * ARENA_MARGIN)
    player = Player(*arena.center)

    running = True
    while running:
        # Cap dt so dragging the window doesn't teleport the player.
        dt = min(clock.tick(FPS) / 1000, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t and player.alive:
                    player.take_damage(10)  # test hit, no enemies yet
                    if not player.alive:
                        print("infected")
                elif event.key == pygame.K_r:
                    player = Player(*arena.center)

        if player.alive:
            player.update(dt, pygame.key.get_pressed(), arena)

        screen.fill(BACKGROUND_COLOR)
        pygame.draw.rect(screen, ARENA_BORDER_COLOR, arena, 2)
        player.draw(screen)

        hp_text = font.render(f"HP: {player.hp}/{player.max_hp}", True, TEXT_COLOR)
        screen.blit(hp_text, (10, 10))
        if not player.alive:
            dead_text = font.render("infected - press R to restart", True, TEXT_COLOR)
            screen.blit(dead_text, dead_text.get_rect(center=arena.center))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()