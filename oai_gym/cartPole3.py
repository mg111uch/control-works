# Used "Grok-3" basic run and code didn't run on first try but moved.Then used Grok3 Think feature, it thought for 5 min, but still cannot solve it.
# Used "ChatGPT-4o" think run 5 times with updated promts but and code didn't run on first try.
# Used "Gemini 2.5 Pro-Exp" basic run and code didn't run on first try,not even moved.
# Used "Claude Sonnet 3.7" basic run and code didn't run on first try, after some tweak it ran but simulation is wrong, didn't do what is asked.

# PROMPT - Generate python code for energy based swing up control of a cart-pole system with downward position angle is pi and potential energy at the bottom is zero. Apply constraints on state variables.Use matplotlib to generate plots with subplot 1 showing cart-pole animation, subplot 2 showing phase plot, subplot 3 showing both cart position and velocity, subplot 4 showing control input. Make sure to animate all the subplots with Total simulation runtime of 10 seconds and then on repeat. Initial position of pole is downward and cart velocity is zero. Cart motion should slowly pump rotational energy to the swinging pole so that final position of pole is upright and then balance the pole at desired location using PD controller. Simulate system dynamics first without showing plots, then use simulated data to show realtime plots and animations.

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation

# Physical parameters
g = 9.81        # gravity (m/s^2)
L = 1.0         # pole length (m)
l = 0.5          #  Ccenter of mass
mp = 0.1         # pole mass (kg)
mc = 1.0         # cart mass (kg)
dt = 0.02       # time step (s)
t_max = 1.0    # simulation time (s)

# State constraints
x_max = 2.0     # max cart position (m)
x_dot_max = 1.0    # max cart velocity (m/s)
theta_dot_max = 15.0  # max angular velocity (rad/s)
F_max = 100.0    # maximum force (N)

E_ref = 2 * mp * g * l  # reference energy (potential energy at upright)
k_energy = 0.5      # Energy control gain

"Compute the derivatives of the state variables"
def cart_pole_dynamics(state, u):
    x, x_dot, theta, theta_dot = state
    F = np.clip(u, -F_max, F_max)
    
    st, ct = np.sin(theta), np.cos(theta)
    "Equations which compute theta_ddot first then use it to compute x_ddot"
    # temp = (u + mp * l * theta_dot**2 * st) / (mc + mp)
    # theta_ddot = (g * st - ct * temp) / (l * (4/3 - mp * ct**2 / (mc + mp)))
    # x_ddot = temp - mp * l * theta_ddot * ct / (mc + mp)

    "Equations which calculate x_ddot and theta_ddot separately"
    denom = mc + mp * st**2
    x_ddot = (F + mp * l * theta_dot**2 * st - mp * g * ct * st) / denom
    theta_ddot = (-F * ct - mp * l * theta_dot**2 * st * ct + (mc + mp) * g * st) / (l * denom)
    
    return np.array([x_dot, x_ddot, theta_dot, theta_ddot])

def control_law(state):
    x, x_dot, theta, theta_dot = state
    # PD control for balancing at theta = 0, x = 0
    if np.cos(theta) < 0.966:  # theta < 15 degree
        kp_x, kd_x = 50.0, 20.0 
        kp_theta, kd_theta = 100.0, 15.0
        F = -(kp_x * x + kd_x * x_dot + kp_theta * theta + kd_theta * theta_dot)
        return np.clip(F, -F_max, F_max)
    # Energy-based Swing-up control phase
    else:  
        # Kinetic energy of Cart + Pole ( but approximated as rotational only, ignoring the cart's motion.)
        E_kinetic = 0.5 * mp * (l * theta_dot)**2
        # Potential energy:is zero at θ = pi (hanging down)
        E_potential = mp * g * l * (1 - np.cos(theta))
        # Calculate the total energy of the pole (kinetic + potential).
        E = E_kinetic + E_potential
        E_error = E_ref - E
        # Control law
        F = k_energy * E_error * np.sign(theta_dot * np.cos(theta))
        return np.clip(F, -F_max, F_max)
           
def simulate():
    t = np.arange(0, t_max, dt)
    states = np.zeros((len(t), 4))
    controls = np.zeros(len(t))
    
    # Initial state: Pole hanging down with no initial velocity
    states[0] = [0, 0, np.pi/6, 0]  # [x, x_dot, theta, theta_dot]
    
    for i in range(len(t)-1):
        # Compute control input
        controls[i] = control_law(states[i])
        
        # Update state using Euler integration
        deriv = cart_pole_dynamics(states[i], controls[i])
        next_state = states[i] + deriv * dt
        
        # Apply state constraints
        next_state[0] = np.clip(next_state[0], -x_max, x_max)
        next_state[1] = np.clip(next_state[1], -x_dot_max, x_dot_max)
        # Wrap theta to [-π, π]
        next_state[2] = ((next_state[2] + np.pi) % (2 * np.pi)) - np.pi
        next_state[3] = np.clip(next_state[3], -theta_dot_max, theta_dot_max)
        
        states[i+1] = next_state
    
    # Control input for the last time step
    controls[-1] = control_law(states[-1])
    return t, states, controls

# Plotting and animation
def create_plots_and_animation(t, states, controls):

    fig1 = plt.figure(figsize=(12, 8))

    # Subplot 1: Cart-Pole Animation
    ax1 = fig1.add_subplot(221)
    ax1.set_title("{ Cart-Pole Animation } - { Pole Phase (θ vs θ̇d) }")
    ax1.set_xlim(-x_max-0.5, x_max+0.5)
    ax1.set_ylim(-L-0.5, L+0.5)
    ax1.set_aspect('equal')
    ax1.set_xlabel('Position [m]')
    ax1.set_ylabel('Height [m]')
    ax1.axhline(y=0, color='k',linewidth='1')
    ax1.axvline(x=0, color='k',linewidth='0.5')
    # cart_width = 0.4
    # cart_height = 0.2
    # cart_patch = plt.Rectangle((0, 0), cart_width, cart_height, fc='blue')
    # ax1.add_patch(cart_patch)
    cart, = ax1.plot([], [], 's', c='orange', markersize=20, label='Cart')
    pole, = ax1.plot([], [], lw=5, c='brown')
    time_text = ax1.text(0.05, 0.9, '', transform=ax1.transAxes)

    ax12 = ax1.twinx()
    ax12.set_ylim(-15, 15)
    phase_line, = ax12.plot([], [], 'b-', lw=1, label='Phase')  # Trajectory line
    phase_marker, = ax12.plot([], [], 'ro', markersize=3)    # Current point

    # Subplot 2: Phase Plot (θ vs θ̇)
    ax2 = fig1.add_subplot(222)
    ax2.set_title('System Energy')
    ax2.set_ylabel('Energy ( Joules )')
    ax2.set_xlabel('Time (s)')
    KE_line, = ax2.plot([], [], 'b-', lw=1.5, label='Kinetic')
    PE_line, = ax2.plot([], [], 'r-', lw=1.5, label='Potential')
    TE_line, = ax2.plot([], [], 'g-', lw=1.5, label='Total')
    ax2.set_xlim(0, t_max)
    ax2.set_ylim(-1, 5)
    ax2.legend(loc='upper right')
    ax2.grid(True)    

    # Subplot 3: Cart Position and Velocity
    ax3 = fig1.add_subplot(223)
    ax3.set_title("Cart Position & Velocity")
    ax3.set_xlim(0, t_max)
    ax3.set_ylim(-10, 10)
    ax3.set_xlabel('Time (s)')
    pos_line, = ax3.plot([], [], 'g-', lw=1.5, label='Position x')
    vel_line, = ax3.plot([], [], 'm-', lw=1.5, label='Velocity $\\dot{x}$')
    ax3.legend(loc='upper right')
    ax3.grid(True)

    # Subplot 4: Control Input vs Time
    ax4 = fig1.add_subplot(224)
    ax4.set_title("Control Input (Force)")
    ax4.set_xlabel('Time (s)')
    ax4.set_ylabel('Force F (N)')
    ax4.set_xlim(0, t_max)
    ax4.set_ylim(-F_max*1.2, F_max*1.2)
    control_line, = ax4.plot([], [], 'k-', lw=1.5)
    ax4.grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Adjust layout to prevent title overlap
    
    def animate(i):
        """Update animation frame."""
        x = states[i, 0]
        theta = states[i, 2]
        
        cart.set_data([x], [0])
        
        pole_x = [x, x + L * np.sin(theta)]
        pole_y = [0,  L * np.cos(theta)]
        pole.set_data(pole_x, pole_y)

        time_text.set_text(f'time = {t[i]:.1f}s')

        KE = 0.5 * mp * l**2 * np.square(states[:i+1,3])
        PE = mp * g * l * (1 - np.cos(states[:i+1,2]))

        KE_line.set_data(t[:i+1], KE[:i+1])
        PE_line.set_data(t[:i+1], PE[:i+1])
        TE_line.set_data(t[:i+1], KE+PE)
        
        scale_phase = np.pi # To fit phase plot in cart pole animation
        phase_line.set_data(states[:i+1,2]/scale_phase, states[:i+1,3])
        phase_marker.set_data(states[i,2]/scale_phase, states[i,3])

        pos_line.set_data(t[:i+1], states[:i+1,0])
        vel_line.set_data(t[:i+1], states[:i+1,1])

        control_line.set_data(t[:i+1], controls[:i+1])

        return cart, pole, time_text, KE_line, PE_line, TE_line, phase_line, phase_marker, pos_line, vel_line, control_line
    
    anim = animation.FuncAnimation(fig1, animate,
                                 frames=len(t), interval=dt*1000,
                                 blit=True, repeat=True)
    
    plt.show()

# Run simulation and create visualization
t, states, controls = simulate()
create_plots_and_animation(t, states, controls)