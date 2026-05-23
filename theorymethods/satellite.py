import numpy as np
import control as ct
import math

m = 100
r = 300000
R = 6370000
G = 6.673e-11
M = 5.98e24
k = G*M # 4e14
w = math.sqrt(k/((R+r)**3))  # 1.1596e-3 (rad/s)
v = w * (R+r)   # 7.7348e3    ground velocity (m/s)

A = np.array([[0, 0, 1, 0],
              [0, 0, 0, 1],
              [3*w**2, 0, 0, 2*(r+R)*w],
              [0, 0, -2*w/(r+R), 0]])

Bu = np.array([[0,0], [0,0], [1/m,0], [0,1/(m*r)]])
Bw = np.array([[0,0], [0,0], [1/m,0], [0,1/(m*r)]])

# noise variances
W = 0.1*np.eye(2)

Q = np.eye(4)
R = 1*np.eye(1)

B = Bu[:,1].reshape(-1,1)

K,S,E = ct.lqr(A,B,Q,R)
Ac = A - B*K
print(K)