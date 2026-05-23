"""
Shared constants for Drift King 2D.
Contains colors, physics constants, and game settings.
"""

# Screen dimensions
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (135, 206, 235)
YELLOW = (255, 255, 0)
GREEN = (0, 128, 0)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
TRACK_COLOR = (80, 80, 80)
BORDER_COLOR = WHITE
GLOW_COLORS = [(255, 100, 100), (255, 200, 100), (255, 255, 100)]

# Car physics constants
CAR_WIDTH = 25
CAR_HEIGHT = 15
ACCELERATION = 0.05
FRICTION = 0.98
DRIFT_FRICTION = 0.94
TURN_SPEED = 1.5
BRAKE_FRICTION = 0.85

# Track constants
TRACK_WIDTH = 70
CENTER_X = SCREEN_WIDTH // 2
CENTER_Y = SCREEN_HEIGHT // 2
LOOP_RADIUS_X = 120
LOOP_RADIUS_Y = 150
LEFT_CENTER_X = CENTER_X - 100
RIGHT_CENTER_X = CENTER_X + 100

# Game settings
TOTAL_LAPS = 10
START_LINE_OFFSET = -150

# Default track path
DEFAULT_TRACKS_DIR = "tracks"
DEFAULT_TRACK_FILE = "figure8.json"
