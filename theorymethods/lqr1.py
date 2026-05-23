import numpy as np
import control as ct
import matplotlib
matplotlib.use('TKAgg')
import matplotlib.pyplot as plt
# from numpy.linalg import matrix_power,inv
# from scipy.signal import ss2tf

def plottingFunction(xAxisVector,yAxisVector,titleString,stringXaxis,stringYaxis):
    plt.figure(figsize=(8,6))
    plt.plot(xAxisVector,yAxisVector, color='blue',linewidth=1.5)
    plt.title(titleString, fontsize=14)
    plt.xlabel(stringXaxis, fontsize=14)
    plt.ylabel(stringYaxis,fontsize=14)
    plt.tick_params(axis='both',which='major',labelsize=14)
    plt.grid(visible=True)
    plt.show()

A = np.array([[-1,-2,-0.5],[0.2,-0.4,-0.6],[0,-0.1,0.4]])
B = np.array([[1],[-1],[0]])
C = np.array([[1,3,4]])
D = np.array([0])
# Mcx = np.array([B, np.matmul(A,B), np.matmul(matrix_power(A,2),B)])
# Mcx = Mcx.reshape(3,3).transpose()

# tf = ss2tf(A,B,C,D)

# A_ = np.array([[-1,-0.18,0.39],[1,0,0],[0,1,0]])
# B_ = np.array([[1],[0],[0]])
# C_ = np.array([[-2,1.2,0.21]])
# K_ = np.array([2,2.57,1.14])
# Mcz = np.array([B_, np.matmul(A_,B_), np.matmul(matrix_power(A_,2),B_)])
# Mcz = Mcz.reshape(3,3).transpose()

# Mcx_inv = inv(Mcx)
# T = Mcz.dot(Mcx_inv)

# poles = [-0.5,-1,-1.5]
# Pc = matrix_power(A,3) + 3*matrix_power(A,2) + 2.75*A + 0.75*np.eye(3)

# K_canonical = K_.dot(T)
# K_ackermann = np.array([0,0,1]).dot(Mcx_inv).dot(Pc)
# K_ct_acker = ct.acker(A, B, poles)

'''         Linear Quadratic Regulator
  K(Gain) is given by [Q.inv() * B.T * S]
  S is the parameter P in the solution of Algebric Riccati eqn ARE
  ARE is obtained by using Pontryagin Maximum Principle
  E are the EigenValues of the closed loop system, i.e. poles
  Choose q and r as inverse of the square of max value for x and u
'''
q = 1/(1**2)
r = 1/(0.3**2)
Q = q * np.eye(3)      
R = r * np.array([[1]])
K,S,E = ct.lqr(A,B,Q,R)
print('K(Gain): ',K)
print('EigenValues: ',E)        # w, v = np.linalg.eig(Acl)
Acl = (A - B*K)

sysStateSpace = ct.ss(Acl,B,C,D)

timeVector=np.linspace(0,20,100)
timeReturned, systemOutput = ct.step_response(sysStateSpace,timeVector)

stepInfoData = ct.step_info(sysStateSpace)
# print(stepInfoData)

# ct.damp(sysStateSpace, doprint=True)    # Compute natural frequencies, damping ratios
ct.pzmap(sysStateSpace)     # Pole-zero map 
# ct.sisotool(sysStateSpace)     # Generates the Bode and Root locus plots

plottingFunction(timeReturned,systemOutput,
                 titleString='Step Response',
                 stringXaxis='time [s]' , 
                 stringYaxis='Output')




