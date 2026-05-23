import numpy as np
import control as ct
import matplotlib
matplotlib.use('TKAgg')
import matplotlib.pyplot as plt

m1=2  ; m2=3   ; k1=100  ; k2=200 ; d1=1  ; d2=5

A=np.array([[0, 1, 0, 0],
             [-(k1+k2)/m1 ,  -(d1+d2)/m1 , k2/m1 , d2/m1 ], 
             [0 , 0 ,  0 , 1], 
             [k2/m2,  d2/m2, -k2/m2, -d2/m2]])
B=np.array([[0],[0],[0],[1/m2]])
C=np.array([[1, 0, 0, 0]])
D=np.array([[0]])

sysStateSpace=ct.ss(A,B,C,D)
# print(sysStateSpace)

###############################################################################
#                   Double Mass-Spring-Damper in series
#            simulate the step response of the open-loop system 
###############################################################################
# '''
x0=np.zeros(shape=(4,1))

# define the time vector for simulation
startTime=0
numberSamples=1001
h=0.01
endTime=numberSamples*h
timeVector=np.linspace(startTime,endTime,numberSamples)
# define the control input vector for simulation
controlInputVector=10*np.ones(numberSamples)

returnSimulation = ct.forced_response(sysStateSpace,
                                      timeVector,
                                      controlInputVector,
                                      x0)
   
# returnSimulation.time
# returnSimulation.outputs
# returnSimulation.states 
# returnSimulation.inputs 

# plt.figure(figsize=(8,6))
# plt.plot(returnSimulation.time,returnSimulation.states[0,:], color='blue',linewidth=1.5)
# plt.title('State of First Mass', fontsize=14)
# plt.xlabel('time [s]', fontsize=14)
# plt.ylabel('State',fontsize=14)
# plt.tick_params(axis='both',which='major',labelsize=14)
# plt.grid(visible=True)
# plt.show()

# '''
###############################################################################
#            System Observability 
###############################################################################
'''
def observabilityMatrix(Ain,Cin):
    (r,n)=Cin.shape
    ObsMatrix=np.zeros(shape=(r*n,n))
    powerA=np.eye(n,n)
    for i in range(n):
        ObsMatrix[r*i:r*(i+1),:]=np.matmul(Cin,powerA)
        powerA=np.matmul(powerA,Ain)
    return ObsMatrix

obsM=observabilityMatrix(A,C)
# print(obsM)
# print(np.linalg.matrix_rank(obsM))
U,S,V=np.linalg.svd(obsM)
print(S)
# print(np.linalg.cond(obsM)) # first approach 
print(S.max()/S.min())  #second approach
'''
###############################################################################
#            State Observer Design By Using Pole Placement
###############################################################################
# '''
poles = np.array([-5+1j,-5-1j,-2,-3])
L_T = ct.place(A.transpose(), C.transpose(), poles)
L = L_T.transpose()

# Observer Equation z_dot = A*z + B*u + L*(y-C*z)
Ao = (A-np.matmul(L,C))
Bo = np.column_stack((B, L))
Co = np.eye(4)
Do = np.zeros(shape=(4,2))
# z_dot = Ao*z + Bo*np.array([[u], [y]])
observerStateSpace = ct.ss(Ao,Bo,Co,Do)

z0 = np.array([[0.4],[0.3],[-0.2],[0.2]])
inputObserver = np.row_stack((returnSimulation.inputs,
                              returnSimulation.outputs))

returnObserver = ct.forced_response(observerStateSpace,
                                      timeVector,
                                      inputObserver,
                                      z0)

statesObserver = returnObserver.states
statesSystem = returnSimulation.states
estimationError = statesSystem - statesObserver

stateNumber = 0
plotUptoTime = 500
plt.figure(figsize=(8,6))
plt.plot(statesObserver[stateNumber,0:plotUptoTime],
          label='Observed State', color='green',linewidth=1.5)
plt.plot(statesSystem[stateNumber,0:plotUptoTime],
          label='True State', color='blue',linewidth=1.5)
plt.plot(estimationError[stateNumber,0:plotUptoTime],
          label='Estimation error', color='red',linewidth=1.5)
plt.title('Observer Performance', fontsize=14)
plt.xlabel('Discrete time [s]', fontsize=14)
plt.ylabel('State',fontsize=14)
plt.legend()
plt.grid(visible=True)
plt.show()

# '''                                      