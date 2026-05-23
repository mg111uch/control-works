from model import getModel
# from time import sleep
import numpy as np
import time

class EstimatorController:
  def __init__(self):

    self.mhe = getModel(name='mhe')
    self.mpc = getModel(name='mpc')

    # stepTime = 5 # seconds per time step
    m = self.mpc

    m.x.STATUS = 0
    m.x.FSTATUS = 1
    # m.z.STATUS = 1
    m.z.FSTATUS = 1

    # Velocity
    m.vx.STATUS = 0
    m.vz.STATUS = 0  # 
    m.vx.FSTATUS = 1
    m.vz.FSTATUS = 1  # Receive measurement from simulation

    m.liftAuthority.FSTATUS = 0 
    m.dragAuthority.FSTATUS = 0 
    
    ## Manipulated variables for controller
    m.Throttle.FSTATUS = 0 # Do not receive measurements
    m.Throttle.STATUS = 1 # Adjust for controller
    # m.EngineOn.STATUS = 1
    m.EngineOn.FSTATUS = 0
    m.Yaw.FSTATUS = 0
    m.Yaw.STATUS = 1

    m.options.CV_TYPE = 2
    m.options.NODES = 3
    m.options.SOLVER = 1
    m.options.IMODE = 6
    m.options.MAX_ITER = 500

    # Since there's no estimator active yet, the estimated parameters will be the same
    
    # This will change each time the controller solves
    m.finalMask = m.Param()

    m.Obj( (m.vx**2 + m.x**2) * m.finalMask  )
    # m.Obj( (m.vy**2 + m.y**2) * m.finalMask  )
    # m.Obj(m.x**2 + m.y**2)
    m.Obj( (m.vz**2 + (m.z-25)**2) * m.finalMask )
    m.Obj( (m.sqrt(m.z**2)-m.z)**2 )
    
    self.hasAddedAdditionalZObjective = False
    self.isInTerminalGuidance = False

  def setMPCVars(self, v):

    simTime = v[0]

    # Assume the rocket will land at t = 70 seconds.
    timeHorizon = 78 - simTime # time horizon
    if timeHorizon < 0:
      raise ValueError("Controller is finished, gravity shall rule forever")
    if timeHorizon < 35:
      stepTime = 1
    else:
      stepTime = 2

    nt = int(timeHorizon/stepTime)+1 #number of time points for each cycle

    m = self.mpc
    m.time = np.linspace(0,timeHorizon,nt)

    # If the rocket is close to the ground, disable Yaw and Pitch. We want it to land upright, and it's too late to make adjustments anyway.
    if v[3] < 200:
      m.Yaw.STATUS = 0
      m.Yaw.VALUE = 0

    # Initialize the MPC
    m.x.VALUE = v[1]
    m.z.VALUE = v[2]
    m.vx.VALUE = v[3]
    m.vz.VALUE = v[4]
    m.propMass.VALUE = v[5]

    _finalMask = np.zeros(m.time.size)
    _finalMask[-1] = 1
    m.finalMask.VALUE = _finalMask

    # Assume the engine turns on at t = 46 seconds
    engineOnTime = 40
    _engineOn = map(lambda x: 1 if x + simTime > engineOnTime else 0, m.time)
    m.EngineOn.VALUE = np.array(list(_engineOn))

    # If close to the ground, increase the weight of the z objective term.
    if simTime > 55 and not self.hasAddedAdditionalZObjective:
      self.hasAddedAdditionalZObjective = True
      m.Obj( (m.vz**2 * 100 + (m.z-25)**2 * 10) * m.finalMask)
      
    # If very close to the ground, just land it, don't try to hit the target
    if simTime > 68 and not self.isInTerminalGuidance:
      self.isInTerminalGuidance = True
      # m.Obj( -(m.x**2) * m.finalMask  )
      # m.Obj( -(m.y**2) * m.finalMask  )

  def runMPC(self, firstRun=False):
    m=self.mpc

    if firstRun:
      m.options.MAX_TIME = 60
      m.options.COLDSTART = 1
      m.options.RTOL = 0.1
      m.options.OTOL = 0.1
      m.solve()
    else:
      m.options.MAX_TIME = 5
      m.options.RTOL = 1e-3
      m.options.OTOL = 1e-3
    
    m.solve(disp=firstRun)

    print ('Controller objective: {:10.4f} Final position (x, z) (vx, vz): ({:10.4f}, {:10.4f}) ({:10.4f}, {:10.4f})'.format(m.options.OBJFCNVAL, m.x.VALUE[-1], m.z.VALUE[-1], m.vx.VALUE[-1], m.vz.VALUE[-1]))

    retVal = np.array((
      m.time,
      m.Throttle,
      m.EngineOn,
      m.Yaw
    ))
    return retVal

  