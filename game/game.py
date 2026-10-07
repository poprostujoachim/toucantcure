import pygame

from game.run import Run
from game.settings import BACKGROUND_COLOR, FPS, MAX_DT, SCREEN_HEIGHT, SCREEN_WIDTH, STARTING_CITY, TITLE


class Game:
    def __init__(self, admin=False):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.admin = admin
        self.current_run = None
        self.start_run()

    def start_run(self, city=STARTING_CITY, tier=1):
        self.current_run = Run(self, city, tier)

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000, MAX_DT)
            self.handle_events()
            self.current_run.update(dt)
            self.draw()
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                self.current_run.handle_event(event)

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        self.current_run.draw(self.screen)
        pygame.display.flip()
