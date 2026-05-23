from gekko import GEKKO
import numpy as np
import matplotlib
matplotlib.use('TKAgg')
import matplotlib.pyplot as plt
import random, math, time

m = GEKKO(remote=False)
loops = 100
m.time = np.linspace(0, 10, loops)

tm = np.zeros(loops)

# Measured values
x_m = np.zeros(loops) 
z_m = np.zeros(loops) 
θ_x_m = np.zeros(loops) 
vx_m = np.zeros(loops) 
vz_m = np.zeros(loops) 
w_x_m = np.zeros(loops) 

Throttle_s = np.zeros(loops) 
Gimbalx_s = np.zeros(loops)

# Set point values
x_sp = np.zeros(loops) 
x_sp[2:] = 100.0
x_sp[4:] = 200.0
z_sp = np.zeros(loops) 
z_sp[2:] = 100.0
z_sp[4:] = 200.0
# θ_x_sp = np.zeros(loops)
# vx_sp = np.zeros(loops)
# vz_sp = np.zeros(loops)
# w_x_sp = np.zeros(loops)

# Constants
g = m.Const(value=9.8)
mass = m.Const(value=5000*1000)
L = m.Const(value=8.0)  # Length of Rocket
Thrust = m.Const(value=36*2.5*1000*1000)

# Manipulated variable
Throttle_limits = [0.4, 1.0]
Throttle = m.MV(value=0.5, lb=Throttle_limits[0], ub=Throttle_limits[1])
# EngineOn = m.MV(value=0, lb=0, ub=1, integer=True)
Gimbal_limits = [-7.0*math.pi/180.0,7.0*math.pi/180.0]
Gimbalx = m.MV(value=0, lb=Gimbal_limits[0], ub=Gimbal_limits[1])  # Angle from linear thrust in x direction

Throttle.STATUS = 1  # use to control 
Throttle.FSTATUS = 0 # no feedback measurement
Gimbalx.STATUS = 1  # use to control 
Gimbalx.FSTATUS = 0 # no feedback measurement
# EngineOn.FSTATUS = 0

# Controlled variable
x = m.CV(value=0)
z = m.CV(value=0)
θ_x = m.CV(value=0) 
vx = m.CV(value=0)
vz = m.CV(value=0)
w_x = m.CV(value=0)

x.STATUS = 0
x.FSTATUS = 1
z.STATUS = 0
z.FSTATUS = 1
θ_x.STATUS = 0
θ_x.FSTATUS = 1
vx.STATUS = 0
vx.FSTATUS = 1
vz.STATUS = 0  
vz.FSTATUS = 1
w_x.STATUS = 0
w_x.FSTATUS = 1

# Intermediates
Thrustx_i = m.Intermediate(Thrust*Throttle*m.sin(Gimbalx))# Throttle with respect to coordinate fixed to rocket.
Thrustz_i = m.Intermediate(Thrust*Throttle*(m.cos(Gimbalx)))#+m.cos(Gimbaly))/2.0)
I_rocket = m.Intermediate((1.0/12.0)*mass*L**2)  
d = m.Intermediate(L-I_rocket)  # Distance from moment of inertia
tau_x = m.Intermediate(Thrustx_i*d) 
Thrustz = m.Intermediate(Thrustz_i*m.cos(θ_x)-Thrustx_i*m.sin(θ_x))
Thrustx = m.Intermediate(Thrustz_i*m.sin(θ_x)+Thrustx_i*m.sin(θ_x))

# Equations
m.Equation(z.dt() == vz)
m.Equation(x.dt() == vx)
m.Equation(θ_x.dt() == w_x)
m.Equation(vz.dt() == -g + Thrustz/mass)  # Replace Thrustz_i with Thrustz (currently broke)
m.Equation(vx.dt() == 0 + Thrustx/mass)  # abs/v = the direction of the velocity
m.Equation(w_x.dt()*I_rocket == tau_x)

# Global Options
m.options.IMODE   = 6 # MPC
m.options.CV_TYPE = 1 # Objective type
m.options.NODES   = 3 # Collocation nodes
m.options.SOLVER  = 1 # 1=APOPT, 3=IPOPT 

plt.figure(num=2, figsize=(8,6))
plt.ion()
plt.show()

start_time = time.time()
prev_time = start_time

ticks = 6
for i in range(1,ticks+1):#loops):
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

    ###############################
    ### MPC CONTROLLER          ###
    ###############################
    noise = (1+0.01*random.random())
    x_m[i] =  noise   # x_Measured     
    z_m[i] =  noise   # z_Measured   
    θ_x_m[i] =  noise # θ_x_Measured 
    vx_m[i] =  noise   # x_Measured     
    vz_m[i] =  noise   # z_Measured   
    w_x_m[i] =  noise # θ_x_Measured 
      
    x.MEAS = x_m[i]
    z.MEAS = z_m[i]
    θ_x.MEAS = θ_x_m[i]
    vx.MEAS = vx_m[i]
    vz.MEAS = vz_m[i]
    w_x.MEAS = w_x_m[i]
        
    DT = 10    # input setpoint with deadband +/- DT
    x.SPHI = x_sp[i] + DT
    x.SPLO = x_sp[i] - DT
    z.SPHI = z_sp[i] + DT
    z.SPLO = z_sp[i] - DT
    # θ_x.SPHI = θ_x_sp[i] + DT
    # θ_x.SPLO = θ_x_sp[i] - DT
    # vx.SPHI = vx_sp[i] + DT
    # vx.SPLO = vx_sp[i] - DT
    # vz.SPHI = vz_sp[i] + DT
    # vz.SPLO = vz_sp[i] - DT
    # w_x.SPHI = w_x_sp[i] + DT
    # w_x.SPLO = w_x_sp[i] - DT

    print('Hello1') 
    m.solve(Remote=False)    
    print('Hello2') 

    if (m.options.APPSTATUS==1):        
        Throttle_s[i] = Throttle.NEWVAL  
        Gimbalx_s[i] = Gimbalx.NEWVAL  
    else:        
        Throttle_s[i] = 0 
        Gimbalx_s[i] = 0       

    ###############################
    ###        PLOTS            ###
    ###############################
    plt.clf()

    plt.subplot2grid((15,2),(0,0), rowspan=3)
    plt.plot(tm[0:i], z_sp[0:i],'r', label=r'$z_s$')
    plt.plot(tm[0:i], z_m[0:i],'b', label=r'$z_m$')
    plt.ylabel('Altitude '+r'$(m)$')
    plt.legend(loc='best')

    plt.subplot2grid((15,2),(4,0), rowspan=3)
    plt.plot(tm[0:i], vz_m[0:i], 'b', label=r'$v_z$')
    plt.ylabel('Fall velocity '+r'$(\frac{m}{s})$')
    plt.legend(loc='best')

    plt.subplot2grid((15,2),(8,0), rowspan=3)
    plt.plot(tm[0:i], x_sp[0:i], 'r', label=r'$x_s$')
    plt.plot(tm[0:i], x_m[0:i], 'b', label=r'$x_m$')
    plt.ylabel('Position '+r'$(m)$')
    plt.legend(loc='best')
    
    plt.subplot2grid((15,2),(12,0), rowspan=3)
    plt.plot(tm[0:i], vx_m[0:i], 'b', label=r'$v_x$')
    plt.ylabel('Velocity '+r'$(\frac{m}{s})$')
    plt.legend(loc='best')


    plt.subplot2grid((15,2),(0,1), rowspan=3)
    plt.plot(tm[0:i], w_x_m[0:i], 'b', label=r'$\omega_x$')
    plt.legend(loc='best')
    plt.ylabel('Rot vel '+ r'$(\frac{rotations}{sec})$')

    plt.subplot2grid((15,2),(4,1), rowspan=3)
    plt.plot(tm[0:i], θ_x_m[0:i], 'b', label=r'$θ_x$')
    plt.legend(loc='best')
    plt.ylabel('Angle '+r'$(rad)$')

    plt.subplot2grid((15,2),(8,1), rowspan=3)
    plt.plot(tm[0:i], Gimbalx_s[0:i], 'g--', label=r'$Gimbal_X$')
    plt.legend(loc='best')
    plt.grid(visible=True)
    plt.ylim(Gimbal_limits[0],Gimbal_limits[1])
    plt.ylabel('Gimbal '+r'$(rad)$')
    plt.xlabel('Time')

    plt.subplot2grid((15,2),(12,1), rowspan=3)
    plt.plot(tm[0:i], Throttle_s[0:i], 'k--', label=r'$Thrust$')
    # plt.plot(tm[0:i], EngineOn[0:i], 'r--')
    plt.legend(loc='best')
    plt.grid(visible=True)
    plt.ylim(Throttle_limits[0], Throttle_limits[1])
    plt.ylabel('Throttle')
    plt.xlabel('Time')

    plt.subplots_adjust(top=0.95,wspace=0.3)
    plt.draw()
    if i == ticks:
        plt.savefig('control2D_Fig.png')
    plt.pause(1)
