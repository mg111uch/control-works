import mujoco
import mujoco.viewer
import numpy as np
import time

# --- 1. Define the MuJoCo Model (XML String) ---
# This XML defines a simple inverted pendulum on a ground plane.
PENDULUM_XML = """
<mujoco model="inverted_pendulum">
  <compiler inertiafromgeom="true" angle="degree" coordinate="local"/>
  <default>
    <joint limited="true" range="-90 90"/>
    <geom density="1000"/>
  </default>
  <worldbody>
    <geom name="ground" type="plane" size="0 0 0.1" rgba=".9 .9 .9 1"/>
    
    <!-- Base -->
    <body name="base" pos="0 0 0.1">
        <geom name="base_geom" type="box" size="0.05 0.05 0.05" rgba="0 0.5 0 1"/>
        
        <!-- Pole (Pendulum) -->
        <body name="pole" pos="0 0 0.5">
          <joint name="hinge" type="hinge" axis="0 1 0" pos="0 0 0" damping="0.1"/>
          <geom name="pole_geom" type="capsule" size=".02 .4" pos="0 0 0.4" rgba="0.8 0 0 1"/>
        </body>
    </body>
  </worldbody>
  
  <!-- Actuators (for applying control forces/torque to the joint) -->
  <actuator>
    <motor name="torque" joint="hinge" gear="100"/>
  </actuator>
</mujoco>
"""

# --- 2. Load the Model and Data ---
# Load the model from the XML string
model = mujoco.MjModel.from_xml_string(PENDULUM_XML)
# Create the data structure for the simulation state
data = mujoco.MjData(model)

# --- 3. Define a Control Function (Simple Balance Controller) ---
# For a basic test, we can apply a small control torque to keep the pendulum up
def controller(model, data):
    """
    A simple PD controller to apply torque based on the joint angle and velocity.
    """
    # 1. Get the address (index) of the joint's QPOS (position) and DOF (velocity)
    
    # Correct attribute for QPOS (Position)
    qpos_addr = model.joint('hinge').qposadr
    
    # Correct attribute for QVEL (Velocity) -> Use dofadr (Degree of Freedom Address)
    qvel_addr = model.joint('hinge').dofadr 
    
    # 2. Use the address to retrieve the current angle and angular velocity
    angle = data.qpos[qpos_addr]
    velocity = data.qvel[qvel_addr]
    
    # Simple Proportional-Derivative (PD) control
    Kp = -100  
    Kd = -10  
    
    # Calculate the desired control torque (actuator force)
    control_torque = Kp * angle + Kd * velocity
    
    # Set the actuator control input (ctrl array).
    data.ctrl[0] = control_torque

# --- 4. Launch the Viewer and Run the Simulation ---
print("Running MuJoCo simulation. Close the viewer window to exit.")

# The mujoco.viewer.launch() function runs the simulation loop.
# It automatically handles rendering, user input, and physics stepping.
with mujoco.viewer.launch_passive(model, data) as viewer:
    
    # The viewer loop will continue until the window is closed
    while viewer.is_running():
        
        # Call the controller function to update the control forces
        controller(model, data)
        
        # Step the simulation forward by one time step
        mujoco.mj_step(model, data)
        
        # Update the viewer (essential for seeing the new frame)
        viewer.sync()
        
        # Optional: Add a small delay for smoother visualization
        time.sleep(model.opt.timestep)

print("Simulation finished.")