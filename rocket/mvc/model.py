from time import sleep
from gekko import GEKKO
import numpy as np


def getModel(name):

  m = GEKKO(name=name, remote=False)
  # m.options.NODES = 3
  # Do not set IMODE here, as the same model might be used for MPC and MHE

  m.g = m.Const(value=9.80665)
  drymass = m.Const(value=1800*1000)
  Raptor_burn_rate =  m.Const(value=650)
  engines_fired = m.Const(value=36)

  m.Throttle = m.MV(value=0.0, lb=0.4, ub=1.0)
  m.EngineOn = m.MV(value=0, lb=0, ub=1, integer=True)
  m.Yaw = m.MV(value=0, lb=-45, ub=45)

  m.propMass = m.CV(value=3100*1000)

  m.RaptorThrustSL = m.Const(2.5*1000*1000)     # N, per engine
  m.RaptorThrustVac = m.Const(3*1000*1000)    # N, per engine

  m.windx = m.FV(value=0)

  m.x = m.CV(value=0)
  m.z = m.CV(value=0)

  m.vx = m.CV(value=0)
  m.vz = m.CV(value=0)

  m.liftAuthority = m.FV(value=240)
  m.dragAuthority = m.FV(value=1.5)
  Ifactorempirical = m.FV(value=251.0)

  vRelAir2 = m.Intermediate((m.vx-m.windx)**2  + m.vz**2)
  vRelAirMag = m.Intermediate( m.sqrt(vRelAir2) )
  vRelAirNormx = m.Intermediate((m.vx-m.windx) / vRelAirMag)
  vRelAirNormz = m.Intermediate(m.vz / vRelAirMag)

  ρ = m.Intermediate( 1.2205611857638659 * m.exp(-0.00009107790874911096 * m.z + -1.8783521651107734e-9 * m.z**2 ))  # Density of Air
  press = m.Intermediate( 101325 * m.exp(-0.00011890154532889426 * m.z + -1.4298587512183478e-9 * m.z**2 )) # Pressure of air

  dynPress = m.Intermediate(0.5 * ρ * vRelAir2)

  I_rocket = m.Intermediate( Ifactorempirical*(m.propMass+drymass) )  # Moment of inertia

  pointingErrorX = m.Intermediate((m.vx-m.windx) / m.sqrt(vRelAir2) + m.Yaw*np.pi/180)
  Liftx = m.Intermediate(-pointingErrorX * m.liftAuthority * dynPress)

  m.AOA = m.Intermediate( m.sqrt(pointingErrorX**2 ) )
  dragArea = m.Intermediate(10.8 + 163.5 * m.AOA)
  dragForce = m.Intermediate(dynPress * dragArea * m.dragAuthority)

  Dragx = m.Intermediate( -dragForce * vRelAirNormx)
  Dragz = m.Intermediate( -dragForce * vRelAirNormz)

  m.Thrust = m.Intermediate(m.Throttle * m.EngineOn * (m.RaptorThrustSL * press / 101325 + m.RaptorThrustVac * (1 - press / 101325)))
  Thrustx = m.Intermediate(1 * m.Thrust * m.Yaw*np.pi/180)
  Thrustz = m.Intermediate(1 * m.Thrust * m.sqrt(1 - (m.Yaw*np.pi/180)**2 ))

  m.Equation(m.z.dt() == m.vz)
  m.Equation(m.x.dt() == m.vx)

  m.Equation(m.vx.dt() ==  0 + (Dragx + Thrustx + Liftx) / (m.propMass+drymass))
  m.Equation(m.vz.dt() == -m.g + (Dragz + Thrustz) / (m.propMass+drymass))

  m.Equation(m.propMass.dt() == - Raptor_burn_rate * engines_fired * m.Thrust) 

  return m