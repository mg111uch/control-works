import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('TKAgg')
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler

from gekko import GEKKO

filename = 'tclab_dyn_data2.csv'
data = pd.read_csv(filename)

# ------------Temperature Estimation from Energy Balance ---------------------------------

m = GEKKO(remote=False)

n = 60*10+1  # Number of second time points (10min)
m.time = np.linspace(0,n-1,n) # Time vector

# Parameters
# Percent Heater (0-100%)
Q1d = np.zeros(n)
Q1d[10:200] = 80
Q1d[200:280] = 20
Q1d[280:400] = 70
Q1d[400:] = 50
Q1 = m.Param(value = Q1d)

Q2d = np.zeros(n)
Q2d[120:320] = 100
Q2d[320:520] = 10
Q2d[520:] = 80
Q2 = m.Param(value = Q2d)

T0 = m.Param(value=19.0+273.15)     # Initial temperature
Ta = m.Param(value=19.0+273.15)     # K
U =  m.Param(value=10.0)            # W/m^2-K
mass = m.Param(value=4.0/1000.0)    # kg
Cp = m.Param(value=0.5*1000.0)      # J/kg-K    
A = m.Param(value=10.0/100.0**2)    # Area not between heaters in m^2
As = m.Param(value=2.0/100.0**2)    # Area between heaters in m^2
alpha1 = m.Param(value=0.01)        # W / % heater
alpha2 = m.Param(value=0.005)      # W / % heater
eps = m.Param(value=0.9)            # Emissivity
sigma = m.Const(5.67e-8)            # Stefan-Boltzman

# Temperature states as GEKKO variables
T1 = m.Var(value=T0)
T2 = m.Var(value=T0)        

# Between two heaters
Q_C12 = m.Intermediate(U*As*(T2-T1)) # Convective
Q_R12 = m.Intermediate(eps*sigma*As*(T2**4-T1**4)) # Radiative

m.Equation(T1.dt() == (1.0/(mass*Cp))*(U*A*(Ta-T1) \
                    + eps * sigma * A * (Ta**4 - T1**4) \
                    + Q_C12 + Q_R12 \
                    + alpha1*Q1))

m.Equation(T2.dt() == (1.0/(mass*Cp))*(U*A*(Ta-T2) \
                    + eps * sigma * A * (Ta**4 - T2**4) \
                    - Q_C12 - Q_R12 \
                    + alpha2*Q2))

m.options.IMODE = 4
m.solve()

T1_eb = T1.value
T2_eb = T2.value

# --------------Temperature Prediction by Neural Network ---------------------------

# -------------------------------------
# scale data
# -------------------------------------
s = MinMaxScaler(feature_range=(0,1))
sc_train = s.fit_transform(data)

# partition into inputs and outputs
xs = sc_train[:,0:2] # 2 heaters
ys = sc_train[:,2:4] # 2 temperatures

# -------------------------------------
# build neural network
# -------------------------------------
nin = 2  # inputs
n1 = 2   # hidden layer 1 (linear)
n2 = 2   # hidden layer 2 (nonlinear)
n3 = 2   # hidden layer 3 (linear)
nout = 2 # outputs

# Initialize gekko models
train = GEKKO(remote=False)
dyn   = GEKKO(remote=False)
model = [train,dyn]

for m in model:
    # use APOPT solver
    m.options.SOLVER = 1

    # input(s)
    m.inpt = [m.Param() for i in range(nin)]

    # layer 1 (linear)
    m.w1 = m.Array(m.FV, (nout,nin,n1))
    m.l1 = [[m.Intermediate(sum([m.w1[k,j,i]*m.inpt[j] \
            for j in range(nin)])) for i in range(n1)] \
            for k in range(nout)]

    # layer 2 (tanh)
    m.w2 = m.Array(m.FV, (nout,n1,n2))
    m.l2 = [[m.Intermediate(sum([m.tanh(m.w2[k,j,i]*m.l1[k][j]) \
            for j in range(n1)])) for i in range(n2)] \
            for k in range(nout)]

    # layer 3 (linear)
    m.w3 = m.Array(m.FV, (nout,n2,n3))
    m.l3 = [[m.Intermediate(sum([m.w3[k,j,i]*m.l2[k][j] \
            for j in range(n2)])) for i in range(n3)] \
            for k in range(nout)]

    # outputs
    m.outpt = [m.CV() for i in range(nout)]
    m.Equations([m.outpt[k]==sum([m.l3[k][i] for i in range(n3)]) \
                 for k in range(nout)])

    # flatten matrices
    m.w1 = m.w1.flatten()
    m.w2 = m.w2.flatten()
    m.w3 = m.w3.flatten()

# -------------------------------------
# fit parameter weights
# -------------------------------------
m = train
for i in range(nin):
    m.inpt[i].value=xs[:,i]
for i in range(nout):
    m.outpt[i].value = ys[:,i]
    m.outpt[i].FSTATUS = 1
for i in range(len(m.w1)):
    m.w1[i].FSTATUS=1
    m.w1[i].STATUS=1
    m.w1[i].MEAS=1.0
for i in range(len(m.w2)):
    m.w2[i].STATUS=1
    m.w2[i].FSTATUS=1
    m.w2[i].MEAS=0.5
for i in range(len(m.w3)):
    m.w3[i].FSTATUS=1
    m.w3[i].STATUS=1
    m.w3[i].MEAS=1.0
m.options.IMODE = 2
m.options.EV_TYPE = 2

# solve for weights to minimize loss (objective)
m.solve(disp=True)

# -------------------------------------
# generate dynamic predictions
# -------------------------------------
m = dyn
n = 60*10+1 
m.time = np.linspace(0,n-1,n)
# load neural network parameters
for i in range(len(m.w1)):
    m.w1[i].MEAS=train.w1[i].NEWVAL
    m.w1[i].FSTATUS = 1
for i in range(len(m.w2)):
    m.w2[i].MEAS=train.w2[i].NEWVAL
    m.w2[i].FSTATUS = 1
for i in range(len(m.w3)):
    m.w3[i].MEAS=train.w3[i].NEWVAL
    m.w3[i].FSTATUS = 1

# scaled inputs
m.inpt[0].value = Q1d * s.scale_[0] + s.min_[0]
m.inpt[1].value = Q2d * s.scale_[1] + s.min_[1]

# define Temperature output
Q0 = 0   # initial heater
T0 = 19  # ambient temperature
# scaled steady state ouput
T1_ss = m.Var(value=T0)
T2_ss = m.Var(value=T0)
m.Equation(T1_ss == (m.outpt[0]-s.min_[2])/s.scale_[2])
m.Equation(T2_ss == (m.outpt[1]-s.min_[3])/s.scale_[3])
# dynamic prediction
T1 = m.Var(value=T0)
T2 = m.Var(value=T0)
# time constant
tau = m.Param(value=120) # determine in a later exercise
# additional model equation for dynamics
m.Equation(tau*T1.dt()==-(T1-T0)+(T1_ss-T0))
m.Equation(tau*T2.dt()==-(T2-T0)+(T2_ss-T0))

# solve dynamic simulation
m.options.IMODE=4
m.solve()

#plot results
plt.figure()

plt.subplot(2,1,1)
plt.plot(m.time,Q1.value,'r-',label='Heater 1')
plt.plot(m.time,Q2.value,'b--',label='Heater 2')
plt.ylabel('Heater (%)')
plt.legend(loc='best')

plt.subplot(2,1,2)
plt.plot(m.time,np.array(T1_eb)-273.15,'r-',label='T1 EnB')
plt.plot(m.time,np.array(T2_eb)-273.15,'b--',label='T1 EnB')
plt.plot(data['Time'],data['T1'],'r.',label='T1 Mea')
plt.plot(data['Time'],data['T2'],'b.',label='T2 Mea')
plt.plot(m.time,T1.value,'k-',label='T1 Pre')
plt.plot(m.time,T2.value,'k--',label='T2 Pre')
plt.ylabel('Temperature (degC)')
plt.legend(loc='best')

plt.xlabel('Time (sec)')
plt.savefig('tclab_dyn_combined.png')
plt.show()