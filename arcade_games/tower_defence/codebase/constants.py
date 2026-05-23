"""
Game Constants and Configuration
"""

# Screen settings
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400
CELL_SIZE = 40

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (135, 206, 235)
YELLOW = (255, 255, 0)
GREEN = (0, 128, 0)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)

# Game mechanics
PATH_Y = 200
ENEMY_SPEED = 2
TOWER_RANGE = 100
BULLET_SPEED = 5

# Tower types configuration
TOWER_TYPES = {
    'artillery': {
        'name': 'Artillery',
        'cost': 50,
        'cooldown': 1.0,
        'range': 100,
        'color': GREEN,
        'bullet_color': YELLOW,
        'bullet_size': 2,
        'damage': 5
    },
    'cannon': {
        'name': 'Cannon',
        'cost': 100,
        'cooldown': 2.0,
        'range': 120,
        'color': BLUE,
        'bullet_color': BLACK,
        'bullet_size': 6,
        'damage': 10
    },
    'laser': {
        'name': 'Laser',
        'cost': 200,
        'cooldown': 1.5,
        'range': 150,
        'color': RED,
        'bullet_color': PURPLE,
        'bullet_size': 4,
        'damage': 15
    }
}

# Game settings
STARTING_MONEY = 150
KILL_REWARD = 15
WAVE_BONUS = 50
WAVE_COOLDOWN = 3
SPAWN_DELAY = 1.5
TOWER_RADIUS = 15
ENEMY_RADIUS = 10
PATH_WIDTH = 30
