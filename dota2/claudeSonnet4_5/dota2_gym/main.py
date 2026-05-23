#!/usr/bin/env python3
"""
Dota2 Gym - Main Entry Point
"""
import sys
import argparse
import pygame
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engine.config_loader import ConfigLoader
from engine.model.game_model import GameModel
from view.main_menu import MainMenu
from view.dota2_view.dota2_view import Dota2View
from controller.human_controller import HumanController

def run_menu(config):
    """Run main menu"""
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Dota2 Gym - Main Menu")
    
    menu = MainMenu(screen, config)
    result = menu.run()
    
    pygame.quit()
    
    # If menu returns 'start', launch the game
    if result == 'start':
        run_local_mode(config)


def run_local_mode(config):
    """Run local 1v1 game"""
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Dota2 Gym - Shadow Fiend 1v1")
    
    # Initialize game
    game_model = GameModel(config)
    game_model.initialize_game()
    
    view = Dota2View(screen, game_model)
    
    controller = HumanController(game_model, view)  # Pass view!

    clock = pygame.time.Clock()
    running = True
    tick_count = 0
    dt = 1.0 / config['game']['tick_rate']
    
    print("=" * 50)
    print("GAME STARTED")
    print("=" * 50)
    print("Controls:")
    print("  - Right-click to move")
    print("  - Left-click on enemy to attack")
    print("  - Drag box to select multiple units")
    print("  - Middle-click drag to pan camera")
    print("  - Q/W/E = Shadowraze (Near/Medium/Far)")
    print("  - R = Requiem of Souls")
    print("  - Z-N or 3-8 = Use items (slots 1-6)")
    print("  - F2 = Toggle shop")
    print("  - F3 = Courier deliver")
    print("  - SPACE = Stop")
    print("  - ESC = Pause menu")
    print("=" * 50)
    
    while running:
         # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                result = controller.handle_event(event)
                if result == 'quit':
                    running = False
        
        # Update game logic (only if not paused)
        if not view.paused:
            game_model.tick()
            tick_count += 1
            
            # Debug output every 10 seconds
            if tick_count % 150 == 0:
                print(f"[Tick {tick_count}] Time: {game_model.game_time:.1f}s")
            
            # Check game end
            if game_model.game_ended:
                print(f"\nGame Over! Winner: {'Radiant' if game_model.winner == 0 else 'Dire'}")
                pygame.time.wait(3000)  # Show for 3 seconds
                running = False
        
        # Render
        view.render(dt)
        pygame.display.flip()

        # Maintain 15 FPS
        dt_ms = clock.tick(config['game']['tick_rate'])
        dt = dt_ms / 1000.0
        
        # Check game end
        if game_model.game_ended:
            print(f"\nGame Over! Winner: {'Radiant' if game_model.winner == 0 else 'Dire'}")
            pygame.time.wait(3000)  # Show for 3 seconds
            running = False
    
    pygame.quit()
    print(f"\nGame ended after {tick_count} ticks ({game_model.game_time:.1f}s)")


def run_headless_mode(config, ticks=1000):
    """Run headless mode for testing (max speed)"""
    print(f"Running {ticks} ticks in headless mode...")
    
    game_model = GameModel(config)
    game_model.initialize_game()
    
    import time
    start_time = time.time()
    
    for i in range(ticks):
        game_model.tick()
        
        if (i + 1) % 1000 == 0:
            elapsed = time.time() - start_time
            tps = (i + 1) / elapsed
            print(f"  Tick {i + 1}/{ticks} - {tps:.0f} ticks/sec")
    
    elapsed = time.time() - start_time
    tps = ticks / elapsed
    print(f"\\n✓ Completed {ticks} ticks in {elapsed:.2f}s")
    print(f"  Performance: {tps:.0f} ticks/sec")
    print(f"  Game time: {game_model.game_time:.1f}s")


def main():
    parser = argparse.ArgumentParser(
        description='Dota2 Gym - Shadow Fiend 1v1 Training Environment',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--mode', 
        type=str, 
        default='menu',
        choices=['menu', 'local', 'headless'],
        help='Game mode (default: menu)'
    )
    parser.add_argument(
        '--ticks', 
        type=int, 
        default=1000,
        help='Number of ticks for headless mode'
    )
    parser.add_argument(
        '--no-fow', 
        action='store_true',
        help='Disable fog of war'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config_loader = ConfigLoader()
    config = config_loader.load_game_config('config/game_config.yaml')
    
    # Apply command line overrides
    if args.no_fow:
        config['fog_of_war']['enabled'] = False
    
    # Run selected mode
    try:
        if args.mode == 'menu':
            run_menu(config)
        elif args.mode == 'local':
            run_local_mode(config)
        elif args.mode == 'headless':
            run_headless_mode(config, args.ticks)
    
    except KeyboardInterrupt:
        print("\\n\\nShutdown requested... exiting")
    except Exception as e:
        print(f"\\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())