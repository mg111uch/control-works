import asyncio
import json
import math
import time
import numpy as np
import torch
import torch.nn as nn
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

# --- Physics Constants & Classes (Same as before) ---
W, H = 1200, 800
DT = 0.1  # 10Hz Physics
G = 6.67430e-11
M_EARTH = 5.972e24
R_EARTH = 6.371e6
ATMOSPHERE_HEIGHT = 100000.0
AIR_DENSITY_SEA = 1.225

BOOSTER_DRY_MASS = 200000
BOOSTER_FUEL_MASS = 3400000
SHIP_DRY_MASS = 120000
SHIP_FUEL_MASS = 1200000
RAPTOR_THRUST = 2.3e6
N_OUTER, N_MID, N_CENTER = 20, 10, 3

# --- Math Helpers ---
def q_mult(q1, q2):
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
    x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
    y = w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2
    z = w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2
    return np.array([w, x, y, z])

def q_to_matrix(q):
    w, x, y, z = q
    return np.array([
        [1 - 2*y*y - 2*z*z,     2*x*y - 2*z*w,     2*x*z + 2*y*w],
        [    2*x*y + 2*z*w, 1 - 2*x*x - 2*z*z,     2*y*z - 2*x*w],
        [    2*x*z - 2*y*w,     2*y*z + 2*x*w, 1 - 2*x*x - 2*y*y]
    ])

# --- Rocket Logic ---
class RocketBody:
    def __init__(self, name, dry_mass, fuel_mass, height, radius):
        self.name = name
        self.dry_mass = dry_mass
        self.fuel_mass = fuel_mass
        self.max_fuel = fuel_mass
        self.h, self.r = height, radius
        self.pos = np.array([0.0, R_EARTH + 30.0, 0.0]) # Start at North Pole
        self.vel = np.array([0.0, 0.0, 0.0])
        self.q = np.array([1.0, 0.0, 0.0, 0.0])
        self.ang_vel = np.array([0.0, 0.0, 0.0])
        self.active = True
        self.throttle_state = 0.0 # For visualization

    def get_mass(self): return self.dry_mass + self.fuel_mass

    def get_inertia(self):
        m = self.get_mass()
        Iz = 0.5 * m * self.r**2
        Ix = (1/12) * m * (3*self.r**2 + self.h**2)
        return np.array([Ix, Ix, Iz])

    def update(self, force, torque, dt):
        if not self.active: return
        
        # Gravity
        r_mag = np.linalg.norm(self.pos)
        f_grav = (-self.pos / r_mag) * G * M_EARTH * self.get_mass() / (r_mag**2)
        
        # Drag (Simple)
        alt = r_mag - R_EARTH
        f_drag = np.zeros(3)
        if alt < ATMOSPHERE_HEIGHT:
            dens = AIR_DENSITY_SEA * (1 - alt/ATMOSPHERE_HEIGHT)
            if dens > 0:
                v_rel = self.vel
                v_mag = np.linalg.norm(v_rel)
                if v_mag > 0.1:
                    area = math.pi * self.r**2
                    drag_mag = 0.5 * dens * (v_mag**2) * 0.4 * area
                    f_drag = - (v_rel / v_mag) * drag_mag

        acc = (f_grav + f_drag + force) / self.get_mass()
        self.vel += acc * dt
        self.pos += self.vel * dt
        
        # Collision
        if np.linalg.norm(self.pos) < R_EARTH:
            self.pos = self.pos / np.linalg.norm(self.pos) * R_EARTH
            self.vel, self.ang_vel = np.zeros(3), np.zeros(3)

        # Rotation
        alpha = torque / self.get_inertia()
        self.ang_vel += alpha * dt
        w_quat = np.array([0, self.ang_vel[0], self.ang_vel[1], self.ang_vel[2]])
        dq = 0.5 * q_mult(w_quat, self.q)
        self.q += dq * dt
        self.q /= np.linalg.norm(self.q)

class StarshipEnv:
    def __init__(self):
        self.reset()

    def reset(self):
        self.booster = RocketBody("SuperHeavy", BOOSTER_DRY_MASS, BOOSTER_FUEL_MASS, 70, 4.5)
        self.ship = RocketBody("Starship", SHIP_DRY_MASS, SHIP_FUEL_MASS, 50, 4.5)
        self.ship.active = False
        self.staged = False
        self.t = 0

    def step(self, inputs):
        # inputs is a dict from websocket: {'throttle': 0-1, 'pitch': deg, 'yaw': deg, 'sep': bool}
        dt = DT
        self.t += dt
        
        # --- Booster Controls ---
        b_force, b_torque = np.zeros(3), np.zeros(3)
        rot_mat = q_to_matrix(self.booster.q)
        local_up = rot_mat.dot([0, 1, 0])
        local_right = rot_mat.dot([1, 0, 0])
        local_fwd = rot_mat.dot([0, 0, 1])

        # Manual Control Mapping
        thr = inputs.get('throttle', 0)
        gp, gy = np.radians(inputs.get('pitch', 0)), np.radians(inputs.get('yaw', 0))
        sep = inputs.get('sep', False)

        self.booster.throttle_state = thr

        if self.booster.active and self.booster.fuel_mass > 0:
            # 1. Outer (Fixed)
            f_outer = thr * N_OUTER * RAPTOR_THRUST * local_up
            # 2. Mid (Gimbal)
            gimbal_vec = rot_mat.dot([math.sin(gy), math.cos(gp)*math.cos(gy), math.sin(gp)])
            f_mid = thr * N_MID * RAPTOR_THRUST * gimbal_vec
            # 3. Center (Gimbal)
            f_cen = thr * N_CENTER * RAPTOR_THRUST * gimbal_vec
            
            b_force = f_outer + f_mid + f_cen
            lever = -35.0
            b_torque += np.cross(local_up * lever, f_mid + f_cen)
            
            m_dot = (N_OUTER+N_MID+N_CENTER) * thr * RAPTOR_THRUST / (350 * 9.81)
            self.booster.fuel_mass -= m_dot * dt

        # Simple Grid Fin Stabilization (Simplified)
        v_mag = np.linalg.norm(self.booster.vel)
        if v_mag > 10 and self.staged:
             # Dampen angular velocity
            b_torque -= self.booster.ang_vel * 1e7

        self.booster.update(b_force, b_torque, dt)

        # --- Stage Sep ---
        if not self.staged and sep:
            self.staged = True
            self.ship.active = True
            self.ship.pos = self.booster.pos + local_up * 60
            self.ship.vel = self.booster.vel + local_up * 2
            self.ship.q = self.booster.q
            self.booster.vel -= local_up * 1
            print("Staging Confirmed")

        # --- Ship Physics ---
        if self.ship.active:
            s_force, s_torque = np.zeros(3), np.zeros(3)
            s_rot = q_to_matrix(self.ship.q)
            # Auto-fire ship if staged
            if self.staged:
                self.ship.throttle_state = 1.0
                s_up = s_rot.dot([0,1,0])
                thrust = 6 * RAPTOR_THRUST
                s_force = s_up * thrust
                if self.ship.fuel_mass > 0:
                    self.ship.fuel_mass -= (thrust / (380*9.81)) * dt
            self.ship.update(s_force, s_torque, dt)
        else:
            self.ship.pos = self.booster.pos + local_up * 60
            self.ship.q = self.booster.q

    def get_state(self):
        return {
            "t": self.t,
            "booster": {
                "pos": self.booster.pos.tolist(),
                "q": self.booster.q.tolist(), # w, x, y, z
                "fuel": self.booster.fuel_mass,
                "thr": self.booster.throttle_state
            },
            "ship": {
                "pos": self.ship.pos.tolist(),
                "q": self.ship.q.tolist(),
                "fuel": self.ship.fuel_mass,
                "active": self.ship.active,
                "thr": self.ship.throttle_state
            }
        }

env = StarshipEnv()

@app.get("/")
async def get():
    with open("index.html", "r") as f:
        return HTMLResponse(f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Websocket Client Connected")
    
    try:
        while True:
            # Receive Controls
            data = await websocket.receive_text()
            inputs = json.loads(data)
            
            if inputs.get('reset'):
                env.reset()
            
            # Step Physics
            env.step(inputs)
            
            # Send State
            state = env.get_state()
            await websocket.send_text(json.dumps(state))
            
            # Throttle loop to ~30Hz send rate (Physics is 10Hz stepping but we can oversample or sync)
            await asyncio.sleep(0.033) 
            
    except Exception as e:
        print("Websocket Connection Closed", e)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)