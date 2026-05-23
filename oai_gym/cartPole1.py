import numpy as np
import control as ct
import matplotlib
matplotlib.use('TKAgg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

m,M,g,L = 1,5,10,1
b = 0.2    # Damping

###############################
###    Derive Equations     ###
###############################
'''
import sympy as sp

g,m,l,t,s,F = sp.symbols('g m l t s F')

I = 1/12*m*l**2

th = sp.Function('th')(t)
x = sp.Function('x')(t)

# dth,dx,ddth,ddx = sp.symbols('dth dx ddth ddx') 
 
r = np.array([0.5*l*sp.sin(th)+x, -0.5*l*sp.cos(th)]) 
v = np.array([r[0].diff(t), r[1].diff(t)])

T = 1/2 * m * np.dot(v, v) + 1/2 * I * np.dot(th.diff(t), th.diff(t))  
V = m * g * r[1] 
L = T - V  
 
dL_dth = L.diff(th)
dL_ddth_dt = L.diff(th.diff(t)).diff(t)
dL_dx = L.diff(x)
dL_ddx_dt = L.diff(x.diff(t)).diff(t)

th_eqn = dL_dth - dL_ddth_dt
x_eqn = dL_dx - dL_ddx_dt - F

# replacements = [(th.diff(t).diff(t), ddth),
#                 (th.diff(t), dth),
#                 (x.diff(t).diff(t), ddx), 
#                 (x.diff(t), dx)
#                 ]

# th_eqn = th_eqn.subs(replacements)
# x_eqn = x_eqn.subs(replacements)

th_eqn = sp.simplify(th_eqn)
x_eqn = sp.simplify(x_eqn)

th_eqn = th_eqn.cancel()
x_eqn = x_eqn.cancel()

replacements = [(sp.cos(th),1),(sp.sin(th),th),((th.diff(t))**2,0)]

th_eqn = th_eqn.subs(replacements)
x_eqn = x_eqn.subs(replacements)

# x_eqn = x_eqn.subs(l,1).subs(g,10).subs(m,1)
# th_eqn = th_eqn.subs(l,1).subs(g,10).subs(m,1)

print(th_eqn)
print(x_eqn)
'''
###############################
###   Closed loop Response  ###
###   Inverted Equilibrium  ###
###############################

A=np.array([[0, 1, 0, 0],
             [(M+m)*g/(M*L), 0, 0, 0], 
             [0 , 0 ,  0 , 1], 
             [-m*g/M, 0, 0, 0]])
B=np.array([[0],[-1/(M*L)],[0],[1/M]])
C=np.array([[1, 0, 0, 0]])
D=np.array([[0]])

'''
closedpoles = np.array([-1+1j,-1-1j,-2+2j,-2-2j])
K = ct.acker(A, B, closedpoles)
Ac = (A - B*K)
closed_sys = ct.ss(Ac,B,C,D)

x0=np.array([[0.1],[0],[0.1],[0]])

numberSamples=101
h=0.1
endTime=numberSamples*h
timeVector=np.linspace(0,endTime,numberSamples)

controlInputVector=np.zeros(numberSamples)

returnSimulation = ct.forced_response(closed_sys,
                                      timeVector,
                                      controlInputVector,
                                      x0)

plt.figure(figsize=(8,6))
plt.plot(returnSimulation.time,returnSimulation.states[0,:], color='blue',linewidth=1.5)
plt.plot(returnSimulation.time,returnSimulation.states[2,:], color='red',linewidth=1.5)
plt.title('State of Cart-Pole System', fontsize=14)
plt.xlabel('time [s]', fontsize=14)
plt.ylabel('State',fontsize=14)
plt.tick_params(axis='both',which='major',labelsize=14)
plt.grid(visible=True)
plt.show()
'''
###############################
###    Swing Up Control     ###
###############################
# '''
sim_time = 5
dt = 0.1
loops = int( sim_time / dt )
tm = np.linspace(0, sim_time, loops+1)

th = np.zeros(loops+1)
dth = np.zeros(loops+1)
En = np.zeros(loops+1)
x = np.zeros(loops+1)
dx = np.zeros(loops+1)
Tperiod = 2
Fx = 10*np.sin(2*np.pi*tm/Tperiod)
Fx[25:] = -5

th[0] = 0*np.pi/3
dth[0] = 0

x[0] = 0
dx[0] = 0

plt.figure(figsize=(8,6))
plt.ion()
plt.show()

for i in range(loops):
    dth[i+1] = dth[i] + ( -(g/L)*th[i] - b*dth[i] + Fx[i]/M*L)*dt
    dx[i+1] = dx[i] + (g*th[i]/M + Fx[i]/M)*dt
    th[i+1] = th[i] + dth[i+1] *dt
    x[i+1] = x[i] + dx[i+1] *dt

    plt.subplot(2, 2, 1)
    plt.cla()
    plt.gca().add_patch(Rectangle((x[i]-0.5,-0.25),1,0.5,linewidth=1,edgecolor='r',facecolor='y'))
    plt.plot([x[i],x[i]+np.sin(th[i])],[0,-np.cos(th[i])], marker='o',color='g')
    plt.xlim(-3, 3)
    plt.ylim(-1.2, 1.2)
    plt.axhline(y=0, color='b',linewidth='1')
    plt.axvline(x=0, color='k',linewidth='0.5')
    plt.xlabel("x")
    plt.ylabel("y")

    plt.subplot(2, 2, 2)
    plt.plot(th[0:i],dth[0:i],'r')
    plt.ylabel('theta_dot')
    plt.xlabel('theta')
    plt.grid(True, which='both')
    plt.xlim(-1.5, 1.5)
    plt.ylim(-4, 4)
    plt.axhline(y=0, color='k',linewidth='1')
    plt.axvline(x=0, color='k',linewidth='1')

    plt.subplot(2, 2, 3)
    plt.plot(tm[0:i],x[0:i],'r', label='x')
    plt.plot(tm[0:i],dx[0:i],'--b', label=r'$v_x$')
    plt.ylabel('Cart Pos & Vel')
    plt.xlabel('Time')
    # plt.ylim(-1, 1)
    plt.grid(True, which='both')

    plt.subplot(2, 2, 4)
    plt.plot(tm[0:i],Fx[0:i],'g', label='Control')
    plt.ylabel('Control Input')
    plt.xlabel('Time')
    # plt.ylim(-0.012, 0.012)
    plt.grid(True, which='both')

    plt.draw()
    if i == loops-1:
        plt.savefig('cartpole1.png')
    plt.pause(dt)
# '''