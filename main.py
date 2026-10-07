import sys

from game.game import Game

if __name__ == "__main__":
    Game(admin="--admin" in sys.argv).run()
