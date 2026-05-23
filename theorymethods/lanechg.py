import numpy as np
import control as ct
import control.optimal as opt
import matplotlib
matplotlib.use('TKAgg')
import matplotlib.pyplot as plt
import math
import time
import random

# Optimal control problem
# Perform a "lane change" manuever over the course of 10 seconds.

def vehicle_update(t, x, u, params):
    # Get the parameters for the model
    l = params.get('wheelbase', 3.)         # vehicle wheelbase
    phimax = params.get('maxsteer', 0.5)    # max steering angle (rad)

    # Saturate the steering input (use min/max instead of clip for speed)
    phi = max(-phimax, min(u[1], phimax))

    # Return the derivative of the state
    return np.array([
        math.cos(x[2]) * u[0],            # xdot = cos(theta) v
        math.sin(x[2]) * u[0],            # ydot = sin(theta) v
        (u[0] / l) * math.tan(phi)        # thdot = v/l tan(phi)
    ])

def vehicle_output(t, x, u, params):
    return x                            # return x, y, theta (full state)

# Define the vehicle steering dynamics as an input/output system
vehicle = ct.NonlinearIOSystem(
    vehicle_update, vehicle_output, states=3, name='vehicle',
    inputs=('v', 'phi'),
    outputs=('x', 'y', 'theta'))

# Initial and final conditions
x0 = np.array([0., -2., 0.]); u0 = np.array([10., 0.])
xf = np.array([100., 2., 0.]); uf = np.array([10., 0.])
# Tf = 10
# Define the time horizon (and spacing) for the optimization
# timepts = np.linspace(0, Tf, 20, endpoint=True)

Q = np.diag([0, 0, 0.1])          # don't turn too sharply
R = np.diag([1, 1])               # keep inputs small
P = np.diag([1000, 1000, 1000])   # get close to final point
traj_cost = opt.quadratic_cost(vehicle, Q, R, x0=xf, u0=uf)
term_cost = opt.quadratic_cost(vehicle, P, 0, x0=xf)

traj_constraints = [ opt.input_range_constraint(vehicle, [8, -0.1], [12, 0.1]) ]

# Horizon
T = 2
horizon_timepts = np.linspace(0, T, 5)

ocp = opt.OptimalControlProblem(
    vehicle, 
    horizon_timepts,
    integral_cost = traj_cost,
    trajectory_constraints = traj_constraints,
    terminal_cost = term_cost,
    terminal_constraints = None
)

x = x0  
xx = []
yy = []
tt = []
vv = []
phi = []
last_time = 0

plt.figure(figsize=(8,6))
plt.ion()
plt.show()  

ticks = 17

for t in range(1,ticks+1):# np.linspace(0, Tf-T, 6, endpoint=True):
    start_time = time.process_time()
    # Compute the optimal trajectory over the horizon
    # if xf[0]*0.95 < soln.states[0][-1] < xf[0]*1.05 and xf[1]*0.95 < soln.states[1][-1] < xf[1]*1.05:
    #     pass
    # else:
    traj = ocp.compute_trajectory(x)   
    # Simulate the system for the update period
    t_eval = np.linspace(0, traj.time[1], 5)
    soln = ct.input_output_response(vehicle, t_eval, traj.inputs, x)
    # Compute time
    print("* Total time = %5g seconds\n" % (time.process_time() - start_time)) 

    # print('traj.time :',traj.time)
    # print('traj.states :',traj.states[0])
    # print('soln.time :',soln.time)
    # print('last_time :',last_time)
    # print('soln.states :',soln.states[0])

    for i in [0,1,2,3]:
        xx.append(soln.states[0][i])
        yy.append(soln.states[1][i])
        tt.append(last_time + soln.time[i])
        vv.append(soln.inputs[0][i])
        phi.append(soln.inputs[1][i])

    # print('xx :',xx)
    # print('tt :',tt)
    # Update the state for the next iteration
    x = soln.states[:,-1]
    # Random Disturbance Noise
    x = x*(1+0.01*random.random())

    last_time = last_time + soln.time[-1]

    plt.subplot(3, 1, 1)
    plt.plot(x0[0], x0[1], 'ro', xf[0], xf[1], 'ro')
    plt.plot(traj.states[0], traj.states[1], '--r')
    plt.plot(xx, yy, 'b')
    plt.xlabel("x [m]")
    plt.ylabel("y [m]")

    plt.subplot(3, 1, 2)
    plt.plot(tt, vv, 'g')
    plt.axis([0, 10, 5, 15])
    plt.xlabel("t [sec]")
    plt.ylabel("velocity [m/s]")

    plt.subplot(3, 1, 3)
    plt.plot(tt, phi, 'k')
    plt.axis([0, 10, -0.15, 0.15])
    plt.xlabel("t [sec]")
    plt.ylabel("steering [rad/s]")

    plt.suptitle("Lane change manuever")
    plt.tight_layout()
    plt.draw()
    if t == ticks:
        plt.savefig('lanechange.png')
    plt.pause(0.5)
    
