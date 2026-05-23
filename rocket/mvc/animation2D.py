import pygame
import random, math, time
import numpy as np
from estimatorController import EstimatorController

pygame.init()
display = pygame.display.set_mode((600,400))

canvas1 = pygame.Surface((150, 150))   # Canvas1 size
canvas2 = pygame.Surface((150, 150))   # Canvas2 size


pygame.display.set_caption('BFR Starship Simulator')

profile = pygame.image.load('Launch_profile.png')
profile.convert()

starship_image = pygame.image.load('starship.png')
starship_image.convert()
starship_rect = starship_image.get_rect()
pygame.draw.rect(starship_image, 'green', starship_rect, 1)

booster_image = pygame.image.load('falcon9_2d_thrust small1.png')
booster_image.convert()
booster_rect = booster_image.get_rect()
pygame.draw.rect(booster_image, 'green', booster_rect, 1)

ws, hs = starship_image.get_size()
wb, hb = booster_image.get_size()

background = pygame.Color(100,149,237)    #Cornflower blue
font = pygame.font.Font(None, 25)
font_color = pygame.Color('olivedrab1')
mid_font_color = pygame.Color('coral4')

clock = pygame.time.Clock()
FPS = 1

def game():
    booster_fuel =     3400*1000       # Booster fuel at Launch  (3100 Up + 300 Return Trip)
    booster_mass =      180*1000       # Dry mass of SuperHeavy Booster   
    star_fuel =        1200*1000       # Starship fuel 
    star_mass =         120*1000       # Dry mass of Starship     
    current_mass = booster_fuel + booster_mass + star_fuel + star_mass  
    launch_booster_fuel = booster_fuel    
    Raptor_thrust = [2.5*1000*1000,3*1000*1000]       # One Engine [Sea level, Vaccuum]
    Raptor_burn_rate =  650       # 808 kg burned per second
    Starship_dimension = [50,9]
    Booster_dimension = [71,9]

    platform = [225,390,150,10]  
    tail = 15                               # [X,Y,width,height]
    originXY = [platform[0]+platform[2]/2, platform[1]+platform[3]+tail]  # X Mark is Origin = LaunchPad

    thrustOffset = np.array([0, hb/2])
    minimumThrottle = 0.4
    atmosPress = 1
    wind_vel = np.array([10,2])
    angle_of_attack = 1
    pointing_factor = np.array([0, 0])
    P_dynamic = 1
    density_air = 1.3
    dragArea = 10.8
    Kd = 100

    sharedData = { }
    
    mvThrottle = 1 
    mvEngineOn = 0 
    mvYaw = 0

    controller = EstimatorController()

    shouldRunController = False
    hasLandedOrCrashed = False

    def runController():
      if hasLandedOrCrashed: return

      simTime = sharedData['time']
      xExact = sharedData['x']
      zExact = sharedData['z']
      vxExact = sharedData['vx'] 
      vzExact = sharedData['vz']  
      propMass = sharedData['propMass']

      histTime = sharedData['histTime']
      histX = sharedData['histX']
      histZ = sharedData['histZ']

      xCoeffs = np.polyfit(histTime, histX, 2)
      zCoeffs = np.polyfit(histTime, histZ, 2)
      x = xCoeffs[2] + xCoeffs[1] * simTime + xCoeffs[0]*simTime**2
      z = zCoeffs[2] + zCoeffs[1] * simTime + zCoeffs[0]*simTime**2
      vx = xCoeffs[1] + 2 * xCoeffs[0] * simTime
      vz = zCoeffs[1] + 2 * zCoeffs[0] * simTime

      mheVars = np.array([simTime, x, z, vx, vz, propMass])
      controller.setMPCVars(mheVars)
      MVs = controller.runMPC() 
      saveControllerOutput(simTime, MVs) 

    def saveControllerOutput(simTime, MVs):
      sharedData['mvTime'] = MVs[0,:] + simTime
      sharedData['mvThrottle'] = MVs[1,:]
      sharedData['mvEngineOn'] = MVs[2,:]
      sharedData['mvYaw'] = MVs[3,:]

    def retrieveControllerOutput(time, interpolate=False):
      if 'mvTime' not in sharedData:
         return (0, 0, 0)
      times = sharedData['mvTime']
      for i in range(times.size):
        if not interpolate and ( i == times.size-1 or times[i] <= time < times[i+1] ):
          return (sharedData['mvThrottle'][i],sharedData['mvEngineOn'][i],sharedData['mvYaw'][i])
    
    if not shouldRunController:
      mheVars = np.array([0, 0, 0, 0, 0, booster_fuel])
      controller.setMPCVars(mheVars) 
      MVs = controller.runMPC(firstRun=True)
      saveControllerOutput(0, MVs)

    g = 9.81        
    x, z, thb, dthb  = 0, 0, 0, 0
    v = np.array([0,0])

    pltTime = np.zeros(0)
    pltX = np.zeros(0)
    pltZ = np.zeros(0)
   
    dt = (1/FPS)
    t = 0
# '''   
    while t<10:
        display.fill(background) 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return   

        if shouldRunController: 
           runController()
        #    mvThrottle, mvEngineOn, mvYaw = retrieveControllerOutput(t, True)
        if hasLandedOrCrashed: 
           mvThrottle, mvEngineOn, mvYaw = 0, 0, 0
        
        mvThrottle = max(min(mvThrottle, 1.0), minimumThrottle)
        if mvEngineOn == 0: mvThrottle = 0
        booster_fuel -= Raptor_burn_rate * 36 * mvThrottle * dt
        if booster_fuel <= 0: booster_fuel,mvThrottle = 0, 0
        
        cosB, sinB = np.cos(thb* math.pi/180.0), np.sin(thb* math.pi/180.0)
        rotMatB = np.array(((cosB,-sinB), (sinB, cosB)))

        current_mass = booster_fuel + booster_mass + star_fuel + star_mass
        momentInertia = 0.2 * current_mass * (Starship_dimension[0]+Booster_dimension[0])**2

        thrustAngle = 0
        if thrustAngle > 7 : thrustAngle = 7
        if thrustAngle < -7 : thrustAngle = -7

        if 0<z<5500: atmosPress = (0.5-1)*z/(5500-0) + 1
        if 5500<z<15000: atmosPress = (0.1-0.5)*z/(15000-5500) + 0.5
        if 15000<z<32000: atmosPress = (0.01-0.1)*z/(32000-15000) + 0.1
        if 32000<z: atmosPress = 0

        thrust_engine = mvThrottle*(Raptor_thrust[0]*atmosPress + Raptor_thrust[1]*(1-atmosPress))
        thrustMag = 36*thrust_engine
        
        thrust = np.array([thrustMag * math.sin(thrustAngle * math.pi/180.0), 
                           thrustMag * math.cos(thrustAngle * math.pi/180.0)])
        thrust = np.matmul(rotMatB, thrust)
        
        thrustOffset = np.matmul(rotMatB, thrustOffset)
        thrustTorque = np.cross(thrustOffset, thrust)
        
        v_rel = (v - wind_vel)
        dynPress = 0.5 * density_air * np.dot(v_rel,v_rel)
        v_rel_hat = (v - wind_vel)/((v - wind_vel)**2).sum()**0.5
        pointing_factor = v_rel + mvYaw
        angle_of_attack = (pointing_factor**2).sum()**0.5
        dragArea = 10.8 + (174.3-10.8) * angle_of_attack
        Cd = 1.5
        F_drag = - dynPress * dragArea * Kd * Cd * v_rel_hat
        F_gravity = np.array([0, -g * current_mass])

        v[0] += (thrust[0] + F_gravity[0] + F_drag[0]) / current_mass * dt
        v[1] += (thrust[1] + F_gravity[1] + F_drag[1]) / current_mass * dt
        dthb += thrustTorque / momentInertia

        x += v[0] * dt
        z += v[1] * dt
        thb += dthb * dt

        t += dt

        pltTime = np.append(pltTime,[t])
        pltX = np.append(pltX,[x])
        pltZ = np.append(pltZ,[z])

        sharedData['time'] = t
        sharedData['x'] = x
        sharedData['z'] = z
        sharedData['vx'] = v[0]
        sharedData['vz'] = v[1]
        sharedData['propMass'] = booster_fuel

        sharedData['histTime'] = pltTime[-6:-1]
        sharedData['histX'] = pltX[-6:-1]
        sharedData['histZ'] = pltZ[-6:-1]

        print(sharedData)

        if t>5: shouldRunController = True

        com_starship = [originXY[0]+((hb+hs)/4)*sinB + x, 
                        originXY[1]-(hb + (hb+hs)/4*cosB) - z]
        com_booster = [originXY[0]-((hb+hs)/4)*sinB + x,
                        originXY[1]-(hb - (hb+hs)/4*cosB) - z]
        centerOfmass = [(com_starship[0]+com_booster[0])/2,
                        (com_starship[1]+com_booster[1])/2]

        rot_starship_image = pygame.transform.rotate(starship_image,  thb )  
        trans_starship_Rect = rot_starship_image.get_rect(center=com_starship)     
        display.blit(rot_starship_image,trans_starship_Rect)

        rot_booster_image = pygame.transform.rotate(booster_image,  thb )
        trans_booster_Rect = rot_booster_image.get_rect(center=com_booster) # 
        display.blit(rot_booster_image, trans_booster_Rect)

        pygame.draw.rect(display, 'blue', (originXY[0], originXY[1], 3, 3))
        pygame.draw.rect(display, 'red', (com_starship[0], com_starship[1], 3, 3))
        pygame.draw.rect(display, 'red', (com_booster[0], com_booster[1], 3, 3))
        pygame.draw.rect(display, 'green', (centerOfmass[0], centerOfmass[1], 3, 3))

        display.blit(profile,[0,0]) 
        pygame.draw.rect(display,(50,50,50),[platform[0],platform[1],platform[2],platform[3]])

##############################################################################################################                  
        canvas2.fill((0,0,0))         
        if z < 70000: canvas2.fill(background)   
        pygame.draw.rect(canvas2, 'green', [0,0,150,150], 2)         # Draw border inside canvas 
        canvas2_x = 75-wb/2
        canvas2_y = 75-hb/2
        canvas2.blit(rot_booster_image,[canvas2_x,canvas2_y]) 
               
        text5 = font.render('Vel(Mach): '+str("{:.1f}".format((v**2).sum()**0.5 / 340)), True, font_color)
        canvas2.blit(text5, (5, 5))
        text11 = font.render('Tilt(deg): '+str("{:.1f}".format(thb)), True, font_color)
        canvas2.blit(text11, (5, 125))
        draw_area2 = canvas2.get_rect().move(600-150, 400-150)           # Canvas location on screen          
        display.blit(canvas2, draw_area2)                                 
######################################################################################################################                
                
        text = font.render('Time(sec): '+str("{:.0f}".format(t)), True, font_color)
        display.blit(text, (400, 10))

        text2 = font.render('Booster XY ('+str("{:.2f}".format(x/1000))+' , '
                    +str("{:.2f}".format(z/1000))+') km',True, font_color)
        display.blit(text2, (350, 220))

        text9 = font.render('Fuel left ', True, font_color)                
        display.blit(text9, (360,245))
        text4 = font.render(str("{:.0f}".format(booster_fuel/1000)+' T'), True, font_color)                
        display.blit(text4, (370,270))
        
        pygame.draw.rect(display,(255,200,0),[420,290,20,100])
        pygame.draw.rect(display,(255,0,0),[420,290,20,(1-(booster_fuel/launch_booster_fuel))*100])        
#############################################################################################################  
        pygame.display.update()
        clock.tick(FPS)
# '''    
game()    
pygame.quit() 

# T + 00:16 = 016 = Pitch kick and roll
# T + 01:08 = 068 = Mach 1 = 1235 km/h 
# T + 01:10 = 070 = ( 12 km / 1500 km/h) = 416 m/s
# T + 01:22 = 082 = Max Q
# T + 01:33 = 093 = ( 22 km / 2500 km/h) = 694 m/s
# T + 02:37 = 157 = ( 70 km / 7000 km/h) = 1945 m/s = 5.8 Mach
# T + 02:40 = 160 = Stage separation
# T + 06:20 = 380 = Re entry Burn
# T + 08:00 = 480 = Landing Burn
# T + 08:32 = 510 = Landing

# Velocity to reach karman line 100 km = 1500 m/s
# Velocity to reach LEO 280 km = 10,000 m/s