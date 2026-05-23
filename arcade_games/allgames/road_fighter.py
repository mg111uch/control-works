import pygame
import random
import sys
import time
import os

# Get the full path of the current script
script_path = __file__

# Extract the filename from the path
script_filename = os.path.basename(script_path)

# Optionally, get the filename without the extension
script_name_without_extension = os.path.splitext(script_filename)[0]

model_save_path = f'policy_model/{script_name_without_extension}.pth'

# Check for training mode
if len(sys.argv) > 1 and sys.argv[1] == 'train':
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    import copy
    import time
    import torch
    import torch.nn as nn
    import numpy as np
    # Ensure reproducibility
    seed = 42
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
    print("Using Genetic Algorithm (Neuroevolution) for training Road Fighter")

# Usage: python road_fighter.py
# The game will prompt for manual or AI play mode.
# For training: python road_fighter.py train

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400

# Road length in pixels
ROAD_LENGTH = 60000

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (135, 206, 235)
YELLOW = (255, 255, 0)
GREEN = (0, 128, 0)
GRAY = (128, 128, 128)
RED = (255, 0, 0)

# Road properties
ROAD_LEFT = 150
ROAD_RIGHT = 450
ROAD_WIDTH = 300

# Car properties
CAR_WIDTH = 40
CAR_HEIGHT = 60
CAR_X = SCREEN_WIDTH // 2
CAR_Y = SCREEN_HEIGHT - CAR_HEIGHT - 10
STEERING_SPEED = 3

# Obstacle properties
OBSTACLE_WIDTH = 40
OBSTACLE_HEIGHT = 60
OBSTACLE_SPEED = 3
OBSTACLE_TYPES = ['car', 'truck']

# Font
FONT = pygame.font.SysFont(None, 36)

# Screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Road Fighter")

clock = pygame.time.Clock()

# Define PolicyNet for training
if len(sys.argv) > 1 and sys.argv[1] == 'train':
    class PolicyNet(nn.Module):
        def __init__(self):
            super(PolicyNet, self).__init__()
            self.fc1 = nn.Linear(3, 64)
            self.fc2 = nn.Linear(64, 32)
            self.fc3 = nn.Linear(32, 2)

        def forward(self, x):
            x = torch.relu(self.fc1(x))
            x = torch.relu(self.fc2(x))
            x = self.fc3(x)
            return x

class Car:
    def __init__(self):
        self.x = CAR_X
        self.y = CAR_Y
        self.speed = 0
        self.gear = 'low'
        self.max_speed_low = 5
        self.max_speed_high = 10
        self.acceleration_low = 0.2
        self.acceleration_high = 0.1
        self.brake_deceleration = 0.5

    def move_left(self):
        self.x -= STEERING_SPEED
        if self.x < ROAD_LEFT:
            self.x = ROAD_LEFT

    def move_right(self):
        self.x += STEERING_SPEED
        if self.x + CAR_WIDTH > ROAD_RIGHT:
            self.x = ROAD_RIGHT - CAR_WIDTH

    def accelerate(self):
        if self.gear == 'low':
            self.speed = min(self.speed + self.acceleration_low, self.max_speed_low)
        else:
            self.speed = min(self.speed + self.acceleration_high, self.max_speed_high)

    def brake(self):
        self.speed = max(self.speed - self.brake_deceleration, 0)

    def shift_gear(self):
        if self.gear == 'low':
            self.gear = 'high'
        elif self.gear == 'high':
            self.gear = 'low'
            self.speed = min(self.speed, self.max_speed_low)

    def update(self):
        self.y -= self.speed
        if self.y < -CAR_HEIGHT:
            self.y = SCREEN_HEIGHT

    def draw(self):
        pygame.draw.rect(screen, RED, (self.x, self.y, CAR_WIDTH, CAR_HEIGHT))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, CAR_WIDTH, CAR_HEIGHT)

class Obstacle:
    def __init__(self, x):
        self.x = x
        self.y = -OBSTACLE_HEIGHT
        self.type = random.choice(OBSTACLE_TYPES)
        if self.type == 'truck':
            self.width = 50
            self.height = 80
        else:
            self.width = OBSTACLE_WIDTH
            self.height = OBSTACLE_HEIGHT

    def update(self, car_speed):
        self.y += OBSTACLE_SPEED + car_speed

    def draw(self):
        color = GREEN if self.type == 'car' else BLUE
        pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def off_screen(self):
        return self.y > SCREEN_HEIGHT

class GameEnv:
    def __init__(self):
        self.reset()

    def reset(self):
        self.car = Car()
        self.obstacles = []
        self.score = 0
        self.done = False
        self.start_time = time.time()
        self.progress = 0
        return self.get_state()

    def get_state(self):
        next_obs = None
        for obs in self.obstacles:
            if obs.y < self.car.y:
                next_obs = obs
                break
        
        if next_obs:
            obs_x_norm = (next_obs.x - ROAD_LEFT) / ROAD_WIDTH
            obs_y_norm = next_obs.y / SCREEN_HEIGHT
        else:
            obs_x_norm = 0.5
            obs_y_norm = 1.0
        
        car_x_norm = (self.car.x - ROAD_LEFT) / ROAD_WIDTH
        
        return [car_x_norm, obs_x_norm, obs_y_norm]

    def step(self, action):
        reward = 0.1

        if action == 1:
            self.car.move_right()
        else:
            self.car.move_left()

        self.car.accelerate()  # AI accelerates like in the game
        self.progress += self.car.speed

        if self.progress >= ROAD_LENGTH:
            self.done = True
            elapsed = time.time() - self.start_time
            self.score = int(10000 / elapsed) if elapsed > 0 else 0
            reward = self.score
            return self.get_state(), reward, self.done

        if random.random() < 0.01:
            x = random.randint(ROAD_LEFT, ROAD_RIGHT - OBSTACLE_WIDTH)
            self.obstacles.append(Obstacle(x))

        for obs in self.obstacles[:]:
            obs.update(self.car.speed)
            if obs.off_screen():
                self.obstacles.remove(obs)
                self.score += 1
                reward += 20.0

        car_rect = self.car.get_rect()
        for obs in self.obstacles:
            if car_rect.colliderect(obs.get_rect()):
                self.done = True
                reward = -1.0

        # Reward for staying centered
        center_x = ROAD_LEFT + ROAD_WIDTH / 2
        distance = abs(self.car.x - center_x)
        max_distance = ROAD_WIDTH / 2
        center_reward = 1.0 - (distance / max_distance)
        reward += center_reward * 0.1

        return self.get_state(), reward, self.done

def draw_score(score):
    text = FONT.render(f"Score: {score}", True, BLACK)
    screen.blit(text, (10, 10))

def draw_time(elapsed):
    time_text = f"Time: {elapsed:.2f}s"
    text = FONT.render(time_text, True, BLACK)
    screen.blit(text, (10, 40))

def draw_gear(car):
    gear_text = f"Gear: {car.gear.capitalize()}"
    text = FONT.render(gear_text, True, BLACK)
    screen.blit(text, (SCREEN_WIDTH - 150, 10))

def draw_mini_map(progress):
    mini_x = 520
    mini_y = 50
    mini_w = 50
    mini_h = 300
    pygame.draw.rect(screen, BLACK, (mini_x, mini_y, mini_w, mini_h), 2)
    # start line
    pygame.draw.line(screen, GREEN, (mini_x, mini_y + mini_h - 5), (mini_x + mini_w, mini_y + mini_h - 5), 3)
    # finish line
    pygame.draw.line(screen, RED, (mini_x, mini_y + 5), (mini_x + mini_w, mini_y + 5), 3)
    # car
    progress_ratio = min(1, (progress // 1000) / 60)
    car_y = mini_y + mini_h - progress_ratio * mini_h
    pygame.draw.circle(screen, RED, (mini_x + mini_w//2, int(car_y)), 5)

def get_state(car, obstacles):
    next_obs = None
    for obs in obstacles:
        if obs.y < car.y:
            next_obs = obs
            break
    
    if next_obs:
        obs_x_norm = (next_obs.x - ROAD_LEFT) / ROAD_WIDTH
        obs_y_norm = next_obs.y / SCREEN_HEIGHT
    else:
        obs_x_norm = 0.5
        obs_y_norm = 1.0
    
    car_x_norm = (car.x - ROAD_LEFT) / ROAD_WIDTH
    
    return [car_x_norm, obs_x_norm, obs_y_norm]

def game_over_screen(elapsed, score):
    screen.fill(BLUE)
    text = FONT.render("Finish!", True, BLACK)
    screen.blit(text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 50))
    time_text = FONT.render(f"Time: {elapsed:.2f}s", True, BLACK)
    screen.blit(time_text, (SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT // 2))
    score_text = FONT.render(f"Score: {score}", True, BLACK)
    screen.blit(score_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2 + 30))
    restart_text = FONT.render("Press SPACE to restart", True, BLACK)
    screen.blit(restart_text, (SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 80))
    pygame.display.flip()

def evaluate(model, env):
    """Run one episode with the given model and return metrics."""
    state = env.reset()
    total_reward = 0
    steps = 0
    done = False
    
    while not done:
        # Pump events to keep the window responsive (if visible)
        pygame.event.pump()
        
        state_tensor = torch.tensor(state, dtype=torch.float32)
        with torch.no_grad():
            logits = model(state_tensor)
            # Action 1 if logits[1] > logits[0] (equivalent to probs[1] > 0.5)
            action = torch.argmax(logits).item()
        
        next_state, reward, done = env.step(action)
        total_reward += reward
        steps += 1
        state = next_state
        
        # Safety break to prevent infinite loops if the model is perfect
        if steps > 5000:
            break
            
    return env.score, total_reward, steps

def mutate(model, noise_std=0.02):
    """Create a mutant copy of the model by adding Gaussian noise to weights."""
    new_model = copy.deepcopy(model)
    with torch.no_grad():
        for param in new_model.parameters():
            noise = torch.randn_like(param) * noise_std
            param.add_(noise)
    return new_model

def train():
    start_time = time.time()
    
    # Genetic Algorithm Parameters
    POP_SIZE = 20
    GENERATIONS = 50  # 20 * 50 = 1000 episodes total
    MUTATION_RATE = 0.02
    ELITISM = 2  # Keep the top 2 unchanged
    
    env = GameEnv()
    
    # Initialize population with random weights
    population = [PolicyNet() for _ in range(POP_SIZE)]
    
    best_overall_score = 0
    
    for gen in range(GENERATIONS):
        gen_results = []
        
        # Evaluate all agents in the population
        for i, agent in enumerate(population):
            score, reward, steps = evaluate(agent, env)
            gen_results.append({
                'agent': agent,
                'score': score,
                'reward': reward,
                'steps': steps
            })
        
        # Sort by Score (primary) and Reward (secondary)
        # Higher is better
        gen_results.sort(key=lambda x: (x['score'], x['reward']), reverse=True)
        
        best_agent_info = gen_results[0]
        current_best_score = best_agent_info['score']
        
        print(f"Gen {gen+1}/{GENERATIONS} | "
              f"Best Score: {current_best_score} | "
              f"Reward: {best_agent_info['reward']:.2f} | "
              f"Steps: {best_agent_info['steps']}")
        
        # Save best model if it improves
        if current_best_score >= best_overall_score:
            best_overall_score = current_best_score
            torch.save(best_agent_info['agent'].state_dict(), model_save_path)

            if best_overall_score >= 100:
                print(f"Target score of 100 reached! Stopping early.")
                break
        
        # Create next generation
        new_pop = []
        
        # 1. Elitism: Keep best models
        for i in range(ELITISM):
            new_pop.append(gen_results[i]['agent'])
            
        # 2. Selection & Mutation
        # Select parents from the top 50% of the population
        survivors = gen_results[:POP_SIZE//2]
        
        while len(new_pop) < POP_SIZE:
            # Pick a random parent from survivors
            parent = random.choice(survivors)['agent']
            # Create a mutated child
            child = mutate(parent, noise_std=MUTATION_RATE)
            new_pop.append(child)
            
        population = new_pop

    print(f"\nTraining completed in {time.time() - start_time:.2f} seconds")
    print(f"Best score achieved: {best_overall_score}")
    print(f"Model saved")

def show_menu():
    screen.fill(BLUE)
    title = FONT.render("Road Fighter", True, BLACK)
    screen.blit(title, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 180))
    manual_text = FONT.render("Press M for Manual Play", True, BLACK)
    screen.blit(manual_text, (SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 - 150))
    ai_text = FONT.render("Press A for AI Play", True, BLACK)
    screen.blit(ai_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 120))
    controls_title = FONT.render("Controls:", True, BLACK)
    screen.blit(controls_title, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2 - 60))
    steer_text = FONT.render("Left/Right: Steer", True, BLACK)
    screen.blit(steer_text, (SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT // 2 - 30))
    accel_text = FONT.render("Up: Accelerate", True, BLACK)
    screen.blit(accel_text, (SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT // 2 ))
    brake_text = FONT.render("Down: Brake", True, BLACK)
    screen.blit(brake_text, (SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2 + 30))
    gear_text = FONT.render("Shift: Change Gear", True, BLACK)
    screen.blit(gear_text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 + 60))
    restart_text = FONT.render("SPACE: Restart", True, BLACK)
    screen.blit(restart_text, (SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT // 2 + 90))
    pygame.display.flip()

def main():
    ai_mode = False
    model = None

    show_menu()
    menu_running = True
    while menu_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    ai_mode = False
                    menu_running = False
                elif event.key == pygame.K_a:
                    if os.path.exists(model_save_path):
                        import torch
                        import torch.nn as nn
                        class PolicyNet(nn.Module):
                            def __init__(self):
                                super(PolicyNet, self).__init__()
                                self.fc1 = nn.Linear(3, 64)  # Changed to 3 inputs
                                self.fc2 = nn.Linear(64, 32)
                                self.fc3 = nn.Linear(32, 2)
                            def forward(self, x):
                                x = torch.relu(self.fc1(x))
                                x = torch.relu(self.fc2(x))
                                x = self.fc3(x)
                                return x
                        model = PolicyNet()
                        model.load_state_dict(torch.load(model_save_path))
                        model.eval()
                        ai_mode = True
                        menu_running = False
                    else:
                        error_text = FONT.render("No trained model found!", True, BLACK)
                        screen.blit(error_text, (SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 + 50))
                        pygame.display.flip()
                        pygame.time.wait(2000)
                        show_menu()

    car = Car()
    obstacles = []
    score = 0
    running = True
    game_over = False
    start_time = time.time()
    elapsed = 0
    progress = 0

    while running:
        screen.fill(BLUE)
        pygame.draw.rect(screen, GRAY, (ROAD_LEFT, 0, ROAD_WIDTH, SCREEN_HEIGHT))

        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if game_over:
                        # Restart
                        car = Car()
                        obstacles = []
                        score = 0
                        game_over = False
                        start_time = time.time()
                        elapsed = 0
                        progress = 0
                elif event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                    if not game_over and not ai_mode:
                        car.shift_gear()

        if not game_over:
            if not ai_mode:
                if keys[pygame.K_LEFT]:
                    car.move_left()
                if keys[pygame.K_RIGHT]:
                    car.move_right()
                if keys[pygame.K_UP]:
                    car.accelerate()
                if keys[pygame.K_DOWN]:
                    car.brake()
            else:
                s = get_state(car, obstacles)
                state_tensor = torch.tensor(s, dtype=torch.float32)
                logits = model(state_tensor)
                probs = torch.softmax(logits, dim=0)
                action = 1 if probs[1] > 0.5 else 0
                if action == 1:
                    car.move_right()
                else:
                    car.move_left()
                car.accelerate()  # AI always accelerates

            progress += car.speed

            if progress >= ROAD_LENGTH and not game_over:
                elapsed = time.time() - start_time
                score = int(10000 / elapsed) if elapsed > 0 else 0
                game_over = True

            if random.random() < 0.01:
                x = random.randint(ROAD_LEFT, ROAD_RIGHT - OBSTACLE_WIDTH)
                obstacles.append(Obstacle(x))

            for obs in obstacles[:]:
                obs.update(car.speed)
                if obs.off_screen():
                    obstacles.remove(obs)
                    score += 1

            car_rect = car.get_rect()
            for obs in obstacles:
                if car_rect.colliderect(obs.get_rect()):
                    game_over = True

            car.draw()
            for obs in obstacles:
                obs.draw()
            draw_score(score)
            draw_time(time.time() - start_time)
            draw_gear(car)
            draw_mini_map(progress)

        else:
            game_over_screen(elapsed, score)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    # Run python 'road_fighter.py train' to start training in headless mode
    if len(sys.argv) > 1 and sys.argv[1] == 'train':
        train()
    else:
        main()