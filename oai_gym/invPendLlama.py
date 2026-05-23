
import pygame
import math
import numpy as np
from control import lqr

# Window dimensions
WIDTH, HEIGHT = 800, 600

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)

# Pendulum properties
PENDULUM_LENGTH = 200
PENDULUM_MASS = 10
GRAVITY = 10

# LQR parameters
Q = np.array([[1.0, 0.0], [0.0, 1.0]])  # State weight matrix
R = np.array([0.1])  # Control weight matrix

# System dynamics matrices
A = np.array([[0.0, 1.0], [GRAVITY / PENDULUM_LENGTH, 0.0]])
B = np.array([[0.0], [1.0 / PENDULUM_LENGTH]])

class Pendulum:
    def __init__(self):
        self.angle = math.pi   # Initial angle
        self.angular_velocity = 0.0

    def update(self, torque):
        angular_acceleration = (-GRAVITY / PENDULUM_LENGTH) * np.sin([self.angle]) + torque / PENDULUM_LENGTH
        self.angular_velocity += angular_acceleration[0]
        self.angle += self.angular_velocity

        # Damping to prevent oscillations
        self.angular_velocity *= 0.95

    def draw(self, screen, x, y):
        pendulum_x = x + PENDULUM_LENGTH * np.sin([self.angle])[0]
        pendulum_y = y - PENDULUM_LENGTH * np.cos([self.angle])[0]

        pygame.draw.line(screen, RED, (x, y), (int(pendulum_x), int(pendulum_y)), 2)
        pygame.draw.circle(screen, RED, (int(pendulum_x), int(pendulum_y)), PENDULUM_MASS)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    pendulum = Pendulum()

    # Compute LQR gains
    K = lqr(A, B, Q, R)[0]  # [[ 3.58747549 38.01302666]]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(WHITE)

        # State vector
        x = np.array([pendulum.angle - math.pi / 2, pendulum.angular_velocity])
        
        # Compute control input using LQR gains
        torque = -np.dot(K, x)

        torq_limits = 0.01
        # Limit torque to prevent excessive swinging
        torque = max(-torq_limits, min(torq_limits, torque))

        pendulum.update(torque)
        pendulum.draw(screen, WIDTH // 2, HEIGHT // 2)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()


