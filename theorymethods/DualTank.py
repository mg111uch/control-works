import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# System parameters
A1, A2 = 1.0, 1.0  # Tank areas (m^2)
R1, R2 = 0.5, 0.5  # Outlet resistances (s/m^2)
c = 0.1  # Coupling coefficient (m^2/s)
u_max = 0.2  # Max inflow (m^3/s)
h_ref = np.array([0.5, 0.5])  # Desired heights (m)
Kp = 0.8  # Proportional gain
rho = 1000  # Water density (kg/m^3)
g = 9.81  # Gravity (m/s^2)

# Simulation parameters
dt = 0.1  # Time step (s)
t_span = 10.0  # Simulation time (s)
t = np.arange(0, t_span, dt)
N = len(t)
h1, h2 = np.zeros(N), np.zeros(N)  # Tank heights
u1, u2 = np.zeros(N), np.zeros(N)  # Control inputs
energy = np.zeros(N)  # System energy
h1[0], h2[0] = 0.3, 0.4  # Initial heights

"""
Continuity equations:

Tank 1: A1(dh1/dt) = u1 - h1/R1 - c(h1 - h2)
Tank 2: A2(dh2/dt) = u2 - h2/R2 + c(h1 - h2)

State Spacce form: dh/dt = Ah +Bu
"""
# State-space model
A = np.array([[-1/(A1*R1) - c/A1, c/A1], [c/A2, -1/(A2*R2) - c/A2]])
B = np.array([[1/A1, 0], [0, 1/A2]])

# Control law
def control(h, h_ref):
    error = h - h_ref
    u = -Kp * error
    return np.clip(u, 0, u_max)

# Simulation loop
for i in range(N-1):
    h = np.array([h1[i], h2[i]])
    u = control(h, h_ref)
    u1[i], u2[i] = u[0], u[1]
    dh = A @ h + B @ u
    h1[i+1] = h1[i] + dh[0] * dt
    h2[i+1] = h2[i] + dh[1] * dt
    # Energy: Potential energy = rho * g * (A1 * h1^2 / 2 + A2 * h2^2 / 2)
    energy[i] = rho * g * (A1 * h1[i]**2 / 2 + A2 * h2[i]**2 / 2)
energy[-1] = rho * g * (A1 * h1[-1]**2 / 2 + A2 * h2[-1]**2 / 2)

# Setup figure with 4 subplots
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 8))
fig.suptitle('Dual Tank System Simulation')

# Subplot 1: Tank animation (simplified as bars)
ax1.set_xlim(-0.5, 1.5)
ax1.set_ylim(0, 0.8)
ax1.set_xticks([0, 1], ['Tank 1', 'Tank 2'])
ax1.set_ylabel('Height (m)')
ax1.set_title('Tank Levels Animation')
bar1 = ax1.bar(0, h1[0], color='b', width=0.4)
bar2 = ax1.bar(1, h2[0], color='r', width=0.4)

# Subplot 2: Tank levels
ax2.set_xlim(0, t_span)
ax2.set_ylim(0, 0.8)
ax2.set_xlabel('Time (s)')
ax2.set_ylabel('Height (m)')
ax2.set_title('Tank Heights')
ax2.grid(True)
line1, = ax2.plot([], [], 'b-', label='Tank 1')
line2, = ax2.plot([], [], 'r-', label='Tank 2')
ax2.legend()

# Subplot 3: System energy
ax3.set_xlim(0, t_span)
ax3.set_ylim(0, max(energy) * 1.2)
ax3.set_xlabel('Time (s)')
ax3.set_ylabel('Energy (J)')
ax3.set_title('System Energy')
ax3.grid(True)
line_energy, = ax3.plot([], [], 'g-', label='Energy')
ax3.legend()

# Subplot 4: Control inputs
ax4.set_xlim(0, t_span)
ax4.set_ylim(0, u_max * 1.2)
ax4.set_xlabel('Time (s)')
ax4.set_ylabel('Inflow (m^3/s)')
ax4.set_title('Control Inputs')
ax4.grid(True)
line_u1, = ax4.plot([], [], 'b-', label='u1')
line_u2, = ax4.plot([], [], 'r-', label='u2')
ax4.legend()

# Animation function
def animate(i):
    # Subplot 1: Update tank bars
    bar1[0].set_height(h1[i])
    bar2[0].set_height(h2[i])
    
    # Subplot 2: Update tank levels
    line1.set_data(t[:i], h1[:i])
    line2.set_data(t[:i], h2[:i])
    
    # Subplot 3: Update energy
    line_energy.set_data(t[:i], energy[:i])
    
    # Subplot 4: Update control inputs
    line_u1.set_data(t[:i], u1[:i])
    line_u2.set_data(t[:i], u2[:i])
    
    return bar1, bar2, line1, line2, line_energy, line_u1, line_u2

# Run animation
ani = FuncAnimation(fig, animate, frames=N, interval=dt*1000, blit=False)
plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.show()