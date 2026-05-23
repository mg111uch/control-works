"""
Input controller for Drift King 2D.
Handles keyboard input and converts to game actions.
"""

import pygame
from typing import Dict, Tuple


class InputController:
    """Handles keyboard input for game control."""
    
    # Action constants
    ACTION_NO_OP = 0
    ACTION_ACCELERATE = 1
    ACTION_TURN_LEFT = 2
    ACTION_TURN_RIGHT = 3
    ACTION_DRIFT = 4
    ACTION_ACCEL_LEFT = 5  # Accelerate + Turn left
    ACTION_ACCEL_RIGHT = 6  # Accelerate + Turn right
    ACTION_BRAKE = 7
    ACTION_ACCEL_BRAKE = 8  # Engine brake
    
    def __init__(self):
        """Initialize input controller."""
        pass
    
    def get_action(self) -> int:
        """
        Get current action based on keyboard input.
        
        Returns:
            Action code (0-8)
        """
        keys = pygame.key.get_pressed()
        
        # Map keys to actions (Updated for brake - DOWN arrow)
        if keys[pygame.K_UP]:
            if keys[pygame.K_DOWN]:  # Engine brake
                return self.ACTION_ACCEL_BRAKE
            elif keys[pygame.K_LEFT]:
                return self.ACTION_ACCEL_LEFT
            elif keys[pygame.K_RIGHT]:
                return self.ACTION_ACCEL_RIGHT
            else:
                return self.ACTION_ACCELERATE
        elif keys[pygame.K_LEFT]:
            return self.ACTION_TURN_LEFT
        elif keys[pygame.K_RIGHT]:
            return self.ACTION_TURN_RIGHT
        elif keys[pygame.K_SPACE]:
            return self.ACTION_DRIFT
        elif keys[pygame.K_DOWN]:
            return self.ACTION_BRAKE
        else:
            return self.ACTION_NO_OP
    
    def decode_action(self, action: int) -> Tuple[bool, bool, bool, bool, bool]:
        """
        Decode action code into individual control flags.
        
        Args:
            action: Action code (0-8)
            
        Returns:
            Tuple of (accelerate, turn_left, turn_right, drift, brake)
        """
        accelerate = action in [1, 5, 6, 8]
        turn_left = action in [2, 5]
        turn_right = action in [3, 6]
        drift = action == 4
        brake = action in [7, 8]
        
        return accelerate, turn_left, turn_right, drift, brake
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle pygame event.
        
        Args:
            event: Pygame event to handle
            
        Returns:
            True if event was handled
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                return True  # Reset signal
        
        return False
