"""
Tower Defense Game
Main entry point - uses modular MVC with ECS architecture
"""

import pygame
from controller import GameController


def main():
    """Main entry point"""
    # Initialize pygame
    pygame.init()
    
    # Create screen
    screen = pygame.display.set_mode((600, 400))
    pygame.display.set_caption("Tower Defence")
    
    # Create and run game controller
    controller = GameController(screen, pygame)
    controller.run()


if __name__ == "__main__":
    main()
