import sys
import pygame
import time
import math
import numpy as np
import random
import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt

class RocketEnv:
    def __init__(self, render=False):
        # Constants
        self.size = width, height = 800, 600
        self.bgColor = 132, 206, 249  # Light blue background
        self.render_mode = render
        if self.render_mode:
            try:
                pygame.init()
                self.screen = pygame.display.set_mode(self.size)
            except pygame.error:
                print("No display available, running without rendering.")
                self.render_mode = False
                return
            try:
                # Use convert_alpha() for better rendering of transparent backgrounds
                self.falcon_original = pygame.image.load("imgs/falcon9_2d_thrust.png").convert_alpha()
            except pygame.error:
                # Handle the case where the image isn't found
                print("Error: Could not load image 'imgs/falcon9_2d_thrust.png'.")
                self.falcon_original = None

            # --- Image Setup ---
            self.falconPPM = 7.86  # Pixels per meter
            self.falcon_scaled = None
            self.falconRect_scaled = None

            if self.falcon_original:
                falconRect_original = self.falcon_original.get_rect()
                falcon_width_m = falconRect_original.w / self.falconPPM
                falcon_height_m = falconRect_original.h / self.falconPPM
                scaled_width = int(falcon_width_m * 1)
                scaled_height = int(falcon_height_m * 1)
                self.falcon_scaled = pygame.transform.scale(self.falcon_original, (scaled_width, scaled_height))
                self.falconRect_scaled = self.falcon_scaled.get_rect()

            # --- Font Setup ---
            self.font = pygame.font.SysFont(None, 25)
            self.font_color_black = pygame.Color(0, 0, 0)
            self.font_color_white = pygame.Color(255, 255, 255)

        # Rocket parameters
        self.Raptor_thrust = 36 * 2.5 * 1000 * 1000
        self.dryMass = 1500 * 1000  # kg (Starship dry mass)
        self.propMass_initial = 3400 * 1000  # kg (Starship propellant mass)
        self.fuelConsumptionRate = 25714  # kg/s (estimated for Starship)

        # Physics constants
        self.G = 6.67430e-11  # Gravitational constant
        self.M_earth = 5.972e24  # Mass of Earth in kg
        self.R_earth = 6.371e6  # Radius of Earth in meters
        self.dragCoefficient = 0.2
        self.crossSectionalArea = math.pi * (4.5)**2
        self.airDensity = 1.225
        self.lever_arm = 20  # meters, approximate distance from COM to thrust point

        # Target position
        self.target_x = 0
        self.target_y = 1000  # meters above ground

        # Action and observation spaces
        self.action_space = {'thrust_angle': (-30, 30), 'thrust_multiplier': (0, 1)}
        self.observation_space = ['x', 'y', 'dx', 'dy', 'theta', 'dtheta', 'propMass', 'wind_magnitude', 'wind_direction']

        self.reset()

    def reset(self):
        # Initial state
        self.x = 0
        self.y_reset = -300 + 40
        self.y = self.y_reset
        self.dx = 0
        self.dy = 0
        self.theta = 0
        self.dtheta = 0
        self.propMass = self.propMass_initial
        self.currentRaptorThrust = self.Raptor_thrust
        self.manualThrustAngle = 0
        self.thrustMagnitudeMultiplier = 0
        self.has_launched = False
        self.wind_magnitude = 0
        self.wind_direction = 1
        self.wind_change_time = time.time() + random.uniform(5, 15)
        self.t = time.time()
        self.startTime = self.t
        return self._get_obs()

    def _get_obs(self):
        return np.array([
            self.x, self.y - self.y_reset, self.dx, self.dy, self.theta,
            self.dtheta, self.propMass / 1000, self.wind_magnitude, self.wind_direction
        ])

    def step(self, action):
        thrust_angle, thrust_multiplier = action
        self.manualThrustAngle = np.clip(thrust_angle, -30, 30)
        self.thrustMagnitudeMultiplier = np.clip(thrust_multiplier, 0, 1)

        newT = time.time()
        dt = newT - self.t
        self.t = newT

        # Update wind
        if self.t > self.wind_change_time:
            self.wind_magnitude = random.uniform(800000, 1000000)
            self.wind_direction = random.choice([-1, 1])
            self.wind_change_time = self.t + random.uniform(5, 15)

        # Update propellant mass
        if self.propMass > 0 and self.thrustMagnitudeMultiplier > 0.001:
            fuel_burnt = self.fuelConsumptionRate * self.thrustMagnitudeMultiplier * dt
            self.propMass -= fuel_burnt
            if self.propMass < 0:
                self.propMass = 0
            self.currentRaptorThrust = self.Raptor_thrust
        else:
            self.currentRaptorThrust = 0

        totalMass = self.dryMass + self.propMass
        momentInertia = (1/12) * totalMass * (47**2)

        c, s = np.cos(self.theta), np.sin(self.theta)
        rotMat = np.array(((c, -s), (s, c)))

        # Thrust
        thrustAngleDeg = self.manualThrustAngle
        thrustMag = self.thrustMagnitudeMultiplier * self.currentRaptorThrust
        thrust_direction = self.theta + thrustAngleDeg * math.pi / 180
        Fthrust = thrustMag * np.array([math.sin(thrust_direction), math.cos(thrust_direction)])
        thrustTorque = self.lever_arm * thrustMag * math.sin(thrustAngleDeg * math.pi / 180)

        # Gravity
        Fgravity = np.array([0, -self.G * self.M_earth * totalMass / (self.R_earth + self.y)**2])

        # Drag
        velocity = np.array([self.dx, self.dy])
        speed = np.linalg.norm(velocity)
        Fdrag = np.array([0, 0])
        if speed > 0.1 and self.y < 100000:
            velocity_unit = velocity / speed
            Fdrag_magnitude = 0.5 * self.airDensity * speed**2 * self.dragCoefficient * self.crossSectionalArea
            Fdrag = -Fdrag_magnitude * velocity_unit

        # Wind
        Fwind = np.array([self.wind_magnitude * self.wind_direction, 0])

        # Update state
        self.dtheta += thrustTorque / momentInertia * dt
        self.dx += (Fthrust[0] + Fgravity[0] + Fdrag[0] + Fwind[0]) / totalMass * dt
        self.dy += (Fthrust[1] + Fgravity[1] + Fdrag[1]) / totalMass * dt
        self.theta += self.dtheta * dt
        self.x += self.dx * dt
        self.y += self.dy * dt

        # Ground collision
        if self.y < self.y_reset:
            self.y = self.y_reset
            self.dy = 0
            self.dtheta = 0

        # Launch check
        if self.y > self.y_reset + 0.1:
            self.has_launched = True

        # Reward and done
        distance_to_target = np.sqrt((self.x - self.target_x)**2 + (self.y - self.target_y)**2)
        reward = -distance_to_target / 1000  # Normalize

        done = False
        if distance_to_target < 50:  # Reached target
            reward += 1000
            done = True
        elif self.has_launched and self.y <= self.y_reset:  # Landed after launch
            reward -= 100
            done = True
        elif self.propMass <= 0:  # Out of fuel
            reward -= 100
            done = True

        return self._get_obs(), reward, done, {}

    def render(self):
        if not self.render_mode:
            return
        self.screen.fill(self.bgColor)

        # Draw ground
        ground_height = 20
        ground_y = self.size[1] - ground_height
        pygame.draw.rect(self.screen, (139, 69, 19), (0, ground_y, self.size[0], ground_height))

        # Draw launch pad
        launch_pad_width = 100
        launch_pad_height = 15
        launch_pad_x = self.size[0] // 2 - launch_pad_width // 2
        launch_pad_y = ground_y - launch_pad_height + 15
        pygame.draw.rect(self.screen, 'red', (launch_pad_x, launch_pad_y, launch_pad_width, launch_pad_height))

        # Convert to screen coords
        screen_x = int(self.x * 1 - 0 * 1 + self.size[0] / 2)
        screen_y = int(-self.y * 1 - 0 * 1 + self.size[1] / 2)

        # Status text
        speed = np.linalg.norm([self.dx, self.dy])
        status_lines = [
            f"Position: ({self.x:.0f}, {self.y-self.y_reset:.0f}) m",
            f"Velocity: ({self.dx:.0f}, {self.dy:.0f}) m/s | Speed: {speed:.0f} m/s",
            f"Angle: {self.theta*180/math.pi:.0f}°",
            f"Fuel: {self.propMass/1000:.0f} / {self.propMass_initial/1000:.0f} tonnes",
            f"Thrust: {self.thrustMagnitudeMultiplier * self.currentRaptorThrust /1e6:.0f} MN (Multiplier: {self.thrustMagnitudeMultiplier:.2f})",
            f"Gimbal Angle: {self.manualThrustAngle:.1f}°",
            f"Wind: {self.wind_magnitude:.1f} m/s {'Right' if self.wind_direction > 0 else 'Left'}"
        ]
        for i, line in enumerate(status_lines):
            text = self.font.render(line, True, self.font_color_black)
            self.screen.blit(text, (10, 10 + i * 25))

        # Display controls
        control_lines = [
            "Controls:",
            "Left/Right: Gimbal +/-1°",
            "Up/Down: Throttle +/-1%",
            "R: Reset"
        ]
        for i, line in enumerate(control_lines):
            text = self.font.render(line, True, self.font_color_white)
            self.screen.blit(text, (self.size[0] - 200, 10 + i * 25))
        
        # Draw rocket
        if self.falcon_scaled:
            rotation_angle = -self.theta * 180 / math.pi
            rotatedFalcon = pygame.transform.rotate(self.falcon_scaled, rotation_angle)
            transformedRect = rotatedFalcon.get_rect(center=(screen_x, screen_y))
            self.screen.blit(rotatedFalcon, transformedRect)

        # Draw center
        pygame.draw.circle(self.screen, 'red', (screen_x, screen_y), 3)

        pygame.display.flip()
        pygame.time.wait(10)

class PolicyNetwork(nn.Module):
    def __init__(self, input_dim, hidden_dim, action_dim):
        super(PolicyNetwork, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.mean_head = nn.Linear(hidden_dim, action_dim)
        self.log_std = nn.Parameter(torch.zeros(action_dim))

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        mean = self.mean_head(x)
        std = torch.exp(self.log_std)
        return mean, std

    def sample(self, x):
        mean, std = self.forward(x)
        dist = torch.distributions.Normal(mean, std)
        action = dist.sample()
        log_prob = dist.log_prob(action).sum(dim=-1)
        return action, log_prob
    
def train():
    env = RocketEnv(render=False)
    input_dim = len(env.observation_space)
    hidden_dim = 128
    output_dim = 2  # thrust_angle, thrust_multiplier

    policy = PolicyNetwork(input_dim, hidden_dim, output_dim)
    optimizer = optim.Adam(policy.parameters(), lr=1e-3)

    num_episodes = 1000
    max_steps = 1000
    gamma = 0.99

    rewards_history = []
    episode_times = []

    for episode in range(num_episodes):
        start_time = time.time()
        obs = env.reset()
        log_probs = []
        rewards = []
        done = False
        step = 0

        while not done and step < max_steps:
            obs_tensor = torch.tensor(obs, dtype=torch.float32)
            action, log_prob = policy.sample(obs_tensor)

            # Scale actions
            thrust_angle = action[0].item() * 30  # -30 to 30
            thrust_multiplier = torch.sigmoid(action[1]).item()  # 0 to 1

            action_clipped = [thrust_angle, thrust_multiplier]

            next_obs, reward, done, _ = env.step(action_clipped)

            log_probs.append(log_prob)
            rewards.append(reward)

            obs = next_obs
            step += 1

        # Compute returns
        returns = []
        G = 0
        for r in reversed(rewards):
            G = r + gamma * G
            returns.insert(0, G)

        returns = torch.tensor(returns, dtype=torch.float32)
        returns = (returns - returns.mean()) / (returns.std() + 1e-8)

        # Loss
        policy_loss = []
        for log_prob, R in zip(log_probs, returns):
            policy_loss.append(-log_prob * R)
        policy_loss = torch.stack(policy_loss).sum()

        optimizer.zero_grad()
        policy_loss.backward()
        optimizer.step()

        end_time = time.time()
        episode_time = end_time - start_time
        episode_times.append(episode_time)

        episode_reward = sum(rewards)
        rewards_history.append(episode_reward)
        print(f"Episode {episode}, Reward: {episode_reward:.2f}")

        # Estimate remaining time
        if len(episode_times) >= 2:
            avg_time_per_episode = (episode_times[-1] + episode_times[-2]) / 2
            remaining_episodes = num_episodes - episode - 1
            estimated_time = avg_time_per_episode * remaining_episodes
            print(f"Estimated time to completion: {estimated_time:.2f} seconds")
        else:
            print("")

        # Move cursor up to overwrite
        if episode < num_episodes - 1:
            lines_to_move = 2 if len(episode_times) >= 2 else 1
            sys.stdout.write(f"\033[{lines_to_move}A")
            sys.stdout.flush()

    # Plot rewards
    plt.plot(rewards_history)
    plt.xlabel('Episode')
    plt.ylabel('Total Reward')
    plt.show()

    # Save model
    torch.save(policy.state_dict(), 'rocket_policy.pth')

# For standalone run
if __name__ == "__main__":
    mode = input("Choose mode: 1 for Manual control, 2 for Auto (trained model), 3 for Train model: ")
    if mode == '3':
        print("Training the model... This may take some time.")
        train()
        print("Training complete. Switching to auto mode with the trained model.")
        mode = '2'
    env = RocketEnv(render=True)
    policy = None
    if mode == '2':
        input_dim = len(env.observation_space)
        hidden_dim = 128
        action_dim = 2
        policy = PolicyNetwork(input_dim, hidden_dim, action_dim)
        try:
            policy.load_state_dict(torch.load('rocket_policy.pth'))
            policy.eval()
            print("Model loaded successfully.")
        except FileNotFoundError:
            print("Model file 'rocket_policy.pth' not found. Switching to manual mode.")
            mode = '1'

    manual_angle = 0
    manual_thrust = 0
    obs = env.reset()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        keys = pygame.key.get_pressed()

        if mode == '1':
            angle_change = 0
            thrust_change = 0
            if keys[pygame.K_LEFT]:
                angle_change += 0.1
            if keys[pygame.K_RIGHT]:
                angle_change -= 0.1
            if keys[pygame.K_UP]:
                thrust_change += 0.01
            if keys[pygame.K_DOWN]:
                thrust_change -= 0.01
            manual_angle += angle_change
            manual_thrust += thrust_change
            manual_angle = np.clip(manual_angle, -30, 30)
            manual_thrust = np.clip(manual_thrust, 0, 1)
            action_clipped = [manual_angle, manual_thrust]
        else:
            obs_tensor = torch.tensor(obs, dtype=torch.float32)
            action, _ = policy.sample(obs_tensor)
            thrust_angle = action[0].item() * 30
            thrust_multiplier = torch.sigmoid(action[1]).item()
            action_clipped = [thrust_angle, thrust_multiplier]

        if keys[pygame.K_r]:
            env.reset()
            obs = env.reset()
            manual_angle = 0
            manual_thrust = 0

        obs, reward, done, info = env.step(action_clipped)
        env.render()
        if done:
            env.reset()
            obs = env.reset()
            manual_angle = 0
            manual_thrust = 0
