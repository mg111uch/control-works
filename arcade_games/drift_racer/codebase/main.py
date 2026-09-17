"""
Drift King 2D - Main Entry Point

A racing game with drifting mechanics, refactored into MVC architecture.

USAGE:
------
1. Run game with menu (select track):
   python main.py

2. Run game with specific track:
   python main.py --track oval

3. Run in headless mode (for testing):
   python main.py --headless

4. List available tracks:
   python main.py --list-tracks

5. Play a fresh procedural track (new layout every launch):
   python main.py --random-track [--shape spline] [--seed 7]

CONTROLS:
---------
UP:    Accelerate
DOWN:  Brake
LEFT:  Turn left
RIGHT: Turn right
SPACE: Drift
R:     Restart game
"""

import os
import sys
import argparse
from typing import Optional, List, Dict

# Change to script directory for relative imports
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def show_track_menu(screen_width: int = 800, screen_height: int = 600) -> Optional[str]:
    """
    Show the track selection menu.
    
    Args:
        screen_width: Width of the menu window
        screen_height: Height of the menu window
        
    Returns:
        Selected track name or None if quit
    """
    import pygame
    from controllers.track_loader import TrackLoader
    from views.menu_renderer import MenuRenderer
    
    # Set window position before initializing pygame
    os.environ['SDL_VIDEO_WINDOW_POS'] = '0,0'
    
    # Initialize pygame display
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Drift King 2D - Select Track")
    
    # Load tracks
    loader = TrackLoader()
    tracks = loader.list_available_tracks()
    
    if not tracks:
        print("No tracks found!")
        pygame.quit()
        return None
    
    # Get track info for display
    track_info = []
    for track_name in tracks:
        info = loader.get_track_info(track_name)
        track_info.append({'name': info['name'], 'difficulty': info['difficulty']})
    
    # Initialize menu renderer
    menu_renderer = MenuRenderer(screen)
    
    # Menu loop
    selected_index = 0
    clock = pygame.time.Clock()
    running = True
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_index = (selected_index - 1) % len(track_info)
                elif event.key == pygame.K_DOWN:
                    selected_index = (selected_index + 1) % len(track_info)
                elif event.key == pygame.K_RETURN:
                    # Start game with selected track
                    pygame.quit()
                    return tracks[selected_index]
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return None
        
        # Render menu
        menu_renderer.render(track_info, selected_index, screen_width, screen_height)
        
        # Cap at 60 FPS
        clock.tick(60)


def list_tracks():
    """List all available tracks."""
    from controllers.track_loader import TrackLoader
    loader = TrackLoader()
    tracks = loader.list_available_tracks()
    
    if tracks:
        print("Available tracks:")
        for track in tracks:
            info = loader.get_track_info(track)
            print(f"  - {info['name']} ({info['difficulty']})")
    else:
        print("No tracks found in 'tracks' directory")


def make_random_track(shape=None, seed=None):
    """Generate a fresh procedural track (no file saved)."""
    import json
    import random
    import tempfile
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'training'))
    import gen_track
    from models.track import Track
    seed = seed if seed is not None else random.randint(0, 999999)
    data, report = gen_track.generate(seed, 1, shape=shape)
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        path = f.name
    track = Track(path)
    os.unlink(path)
    print(f"Generated '{track.name}' (seed={seed}): "
          f"{len(track.checkpoints)} checkpoints, {report}")
    return track


def run_game(track_name: str = None, headless: bool = False,
             screen: 'pygame.Surface' = None, track_obj=None):
    """Run the game with specified track."""
    from controllers.track_loader import TrackLoader
    from controllers.game_controller import GameController

    # Load track
    loader = TrackLoader()
    if track_obj is not None:
        track = track_obj
    elif track_name:
        track = loader.load_track(track_name)
    else:
        track = loader.load_default_track()
    
    print(f"Loading track: {track.name}")
    
    # Create and run game controller
    controller = GameController(track, headless=headless, screen=screen)
    controller.run()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Drift King 2D - Racing Game with Drifting'
    )
    parser.add_argument(
        '--track', 
        type=str, 
        default=None,
        help='Track name to load (without .json extension)'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run in headless mode (no display)'
    )
    parser.add_argument(
        '--list-tracks',
        action='store_true',
        help='List available tracks and exit'
    )
    parser.add_argument(
        '--menu',
        action='store_true',
        help='Show track selection menu'
    )
    parser.add_argument(
        '--random-track',
        action='store_true',
        help='Generate a fresh procedural track instead of loading one'
    )
    parser.add_argument(
        '--shape',
        type=str,
        choices=['ellipse', 'rect', 'stadium', 'spline'],
        default=None,
        help='Shape family for --random-track (default: random mix)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Seed for --random-track (default: new random track every launch)'
    )
    
    args = parser.parse_args()
    
    if args.list_tracks:
        list_tracks()
    else:
        track_obj = None
        if args.random_track:
            track_obj = make_random_track(shape=args.shape, seed=args.seed)
            args.track = None
        # Show menu if no track specified (default behavior)
        if args.track is None and track_obj is None and not args.headless:
            selected_track = show_track_menu()
            if selected_track is None:
                return  # User quit
            args.track = selected_track
        
        run_game(args.track, args.headless, track_obj=track_obj)


if __name__ == "__main__":
    main()
