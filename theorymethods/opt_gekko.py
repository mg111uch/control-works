from gekko import GEKKO 
import numpy as np 
import matplotlib
matplotlib.use('TKAgg')
import matplotlib.pyplot as plt
  
m = GEKKO(remote=False)
# m = GEKKO()

m.time = np.linspace(0,7,71)

mass1 = m.Param(value=10)
mass2 = m.Param(value=1)

final = np.zeros(np.size(m.time))
for i in range(np.size(m.time)):
    if m.time[i] >= 6.2:
        final[i] = 1
    else:  
        final[i] = 0
final = m.Param(value=final)

u = m.Var(value=0)

theta = m.Var(value=0)
q = m.Var(value=0)

y = m.Var(value=-1)
v = m.Var(value=0)

m.Equations([y.dt() == v,
             v.dt() == mass2/(mass1+mass2) * theta + u,
             theta.dt() == q,
             q.dt() == -theta - u])

m.Obj(final * (y**2 + v**2 + theta**2 + q**2))
m.Obj(0.001 * u**2)

m.options.IMODE = 6 

m.solve()

plt.figure()
plt.subplot(4,1,1)
plt.plot(m.time,u.value,'r-',lw=2)
plt.ylabel('Force')
plt.legend(['u'],loc='best')
plt.subplot(4,1,2)
plt.plot(m.time,v.value,'b--',lw=2)
plt.legend(['v'],loc='best')
plt.ylabel('Velocity')
plt.subplot(4,1,3)
plt.plot(m.time,y.value,'g:',lw=2)
plt.legend(['y'],loc='best')
plt.ylabel('Position')
plt.subplot(4,1,4)
plt.plot(m.time,theta.value,'m-',lw=2)
plt.plot(m.time,q.value,'k.-',lw=2)
plt.legend([r'$\theta$','q'],loc='best')
plt.ylabel('Angle')
plt.xlabel('Time')
plt.show()