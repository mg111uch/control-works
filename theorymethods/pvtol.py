import numpy as np
import control as ct
from control.matlab import *    # MATLAB-like functions
import matplotlib
matplotlib.use('TKAgg')
import matplotlib.pyplot as plt

m = 4                         # mass of aircraft
J = 0.0475                    # inertia around pitch axis
r = 0.25                      # distance to center of force
g = 9.8                       # gravitational constant
c = 0.05                      # damping factor (estimated)

# State space dynamics
xe = [0, 0, 0, 0, 0, 0]         # equilibrium point of interest
ue = [0, m*g]                   # (note these are lists, not matrices)

# Dynamics matrix (use matrix type so that * works for multiplication)
# Note that we write A and B here in full generality in case we want
# to test different xe and ue.
A = np.matrix(
   [[ 0,    0,    0,    1,    0,    0],
    [ 0,    0,    0,    0,    1,    0],
    [ 0,    0,    0,    0,    0,    1],
    [ 0, 0, (-ue[0]*np.sin(xe[2]) - ue[1]*np.cos(xe[2]))/m, -c/m, 0, 0],
    [ 0, 0, (ue[0]*np.cos(xe[2]) - ue[1]*np.sin(xe[2]))/m, 0, -c/m, 0],
    [ 0,    0,    0,    0,    0,    0 ]])

# Input matrix
B = np.matrix(
   [[0, 0], [0, 0], [0, 0],
    [np.cos(xe[2])/m, -np.sin(xe[2])/m],
    [np.sin(xe[2])/m,  np.cos(xe[2])/m],
    [r/J, 0]])

# Output matrix
C = np.matrix([[1, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0]])
D = np.matrix([[0, 0], [0, 0]])

Qx1 = np.diag([1, 1, 1, 1, 1, 1])
Qu1a = np.diag([1, 1])
(K, X, E) = ct.lqr(A, B, Qx1, Qu1a)
K1a = np.matrix(K)

# Our input to the system will only be (x_d, y_d), so we need to
# multiply it by this matrix to turn it into z_d.
Xd = np.matrix([[1,0,0,0,0,0],
             [0,1,0,0,0,0]]).T

H = ct.ss(A-B*K,B*K*Xd,C,D)

# Step response for the first input
x,t = step(H,input=0,output=0,T=np.linspace(0,10,100))
# Step response for the second input
y,t = step(H,input=1,output=1,T=np.linspace(0,10,100))

plt.figure(figsize=(8,6))
plt.plot(t,x,'-',t,y,'--')
plt.plot([0, 10], [1, 1], 'k-')
plt.ylabel('Position')
plt.xlabel('Time (s)')
plt.title('Step Response for Inputs')
plt.legend(('Yx', 'Yy'), loc='lower right')
plt.show()

# print(K1a)