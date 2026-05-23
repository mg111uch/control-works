import numpy as np
import random
import time
import pandas as pd
import matplotlib
matplotlib.use('TKAgg')
import matplotlib.pyplot as plt

from gekko import GEKKO

filename = 'tclab_dyn_data2.csv'

df = pd.read_csv(filename)

# Run time in minutes
run_time = 5.0
# Number of cycles
loops = int(60.0*run_time)
tm = np.zeros(loops)

# Temperature (K)
T1 = np.ones(loops) * df['T1'][1] # temperature (degC)
Tsp1 = np.ones(loops) * 30.0 # set point (degC)
Tsp1[100:] = 40.0
Tsp1[200:] = 35.0

# T2 = np.ones(loops) * df['T2'][1] # temperature (degC)
# Tsp2 = np.ones(loops) * 23.0 # set point (degC)

Q1s = np.ones(loops) * 0.0
# Q2s = np.ones(loops) * 0.0

#########################################################
# Initialize Model
#########################################################
m = GEKKO(name='tclab-mpc',remote=False)

# 30 second time horizon
m.time = np.linspace(0,30,31)

# Parameters
Q1_ss = m.Param(value=0)
TC1_ss = m.Param(value=23)
Kp = m.Param(value=0.4)
tau = m.Param(value=160.0)

# Manipulated variable
Q1 = m.MV(value=0)
Q1.STATUS = 1  # use to control temperature
Q1.FSTATUS = 0 # no feedback measurement
Q1.LOWER = 0.0
Q1.UPPER = 100.0
Q1.DMAX = 50.0
Q1.COST = 0.0
Q1.DCOST = 1.0e-4

# Controlled variable
TC1 = m.CV(value=TC1_ss.value)
TC1.STATUS = 1     # minimize error with setpoint range
TC1.FSTATUS = 1    # receive measurement
TC1.TR_INIT = 2    # reference trajectory
TC1.TAU = 10       # time constant for response

# Equation
m.Equation(tau * TC1.dt() + (TC1-TC1_ss) == Kp * (Q1-Q1_ss))  

# Global Options
m.options.IMODE   = 6 # MPC
m.options.CV_TYPE = 1 # Objective type
m.options.NODES   = 3 # Collocation nodes
m.options.SOLVER  = 1 # 1=APOPT, 3=IPOPT
##################################################################

# Create plot
plt.figure()
plt.ion()
plt.show()

# Main Loop
start_time = time.time()
prev_time = start_time
for i in range(1,loops):
    '''
    # Sleep time
    sleep_max = 1.0
    sleep = sleep_max - (time.time() - prev_time)
    if sleep>=0.01:
        time.sleep(sleep)
    else:
        time.sleep(0.01)
    '''
    # Record time and change in time
    t = time.time()
    dt = t - prev_time
    prev_time = t
    tm[i] = t - start_time

    # Read temperatures in Kelvin
    T1[i] = df['T1'][i]
    # T2[i] = a.T2

    ###############################
    ### MPC CONTROLLER          ###
    ###############################
    TC1.MEAS = T1[i]
    # input setpoint with deadband +/- DT
    DT = 0.1
    TC1.SPHI = Tsp1[i] + DT
    TC1.SPLO = Tsp1[i] - DT
    # solve MPC
    m.solve(disp=False)    
    # test for successful solution
    if (m.options.APPSTATUS==1):
        # retrieve the first Q value
        Q1s[i] = Q1.NEWVAL
    else:
        # not successful, set heater to zero
        Q1s[i] = 0        

    # Plot
    plt.clf()
    ax=plt.subplot(2,1,1)
    ax.grid()
    plt.plot(tm[0:i],T1[0:i],'ro',label=r'$T_1$')
    plt.plot(tm[0:i],Tsp1[0:i],'b-',label=r'$T_1 Setpoint$')
    plt.ylabel('Temperature (degC)')
    plt.legend(loc='best')
    ax=plt.subplot(2,1,2)
    ax.grid()
    plt.plot(tm[0:i],Q1s[0:i],'r-',lw=3,label=r'$Q_1$')
    # plt.plot(tm[0:i],Q2s[0:i],'b:',lw=3,label=r'$Q_2$')
    plt.ylabel('Heaters')
    plt.xlabel('Time (sec)')
    plt.legend(loc='best')
    plt.draw()
    plt.pause(0.05)