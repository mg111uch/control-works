import vpython as vp
import numpy as np

m,g,l = 1,10,1
d = 0.1 
th = np.pi/3
dth = 0 
dt = 0.01

_axisX = vp.cylinder(pos=vp.vec(-2, 0, 0), axis=vp.vec(4, 0, 0),color=vp.color.red,radius=0.01)
_axisY = vp.cylinder(pos=vp.vec(0, 0, 0), axis=vp.vec(0, 1, 0),color=vp.color.green,radius=0.01)
_axisZ = vp.cylinder(pos=vp.vec(0, 0, 0), axis=vp.vec(0, 0, 1),color=vp.color.blue,radius=0.01)

bar = vp.box( pos=vp.vec(l/2,0,0),size=vp.vec(l,d,d), color=vp.color.red )
bar.rotate( angle=-np.pi/2+th, axis=vp.vec(0,0,1), origin=vp.vec(0, 0, bar.pos.z) )

while True:
    vp.rate(1/dt)

    dth += - (g/l)*th*dt
    th += dth*dt
    
    bar.axis = l*vp.vec(vp.sin(th), -vp.cos(th), 0)
    bar.pos = 0.5*l**2*vp.hat(bar.axis)
