import pygame
import math

pygame.init()
display = pygame.display.set_mode((600,400))
canvas1 = pygame.Surface((150, 150))   # Canvas1 size
canvas2 = pygame.Surface((150, 150))   # Canvas2 size
pygame.display.set_caption('BFR Starship Simulator')
starship_image = pygame.image.load('imgs/starship.png')
profile = pygame.image.load('imgs/Launch_profile.png')
profile.convert()
starship_image.convert()
w, h = starship_image.get_size()
background = pygame.Color(100,149,237)    #Cornflower blue
font = pygame.font.Font(None, 30)
font_color = pygame.Color('olivedrab1')
mid_font_color = pygame.Color('coral4')
clock = pygame.time.Clock()
FPS = 10    

def game():
    l = 35; d = 4.5; l1 = 50    
    xy = [300,355]                # Rocket location
    platform = [225,390]
#    Launch_mass =  5000*1000       #( Fuel = Launch_mass - StarShip_mass - booster_mass = 3500 tonnes)
    StarShip_mass = 1320*1000       # ( 1320 tonnes)    # Booster thrust( 72 Million Newton)
    stage1_fuel =   3200*1000       # First stage fuel used ( In Booster = 3200 tonnes)
    booster_mass =   180*1000       # Empty mass of SuperHeavy Booster = 180 tonnes
    stage1_mass =    480*1000       # First stage weight afer separation 
    stage2_fuel =   1200*1000       # Second stage fuel (Starship = 1200 tonnes)
    star_mass =      120*1000       # Dry mass of Starship       

    fuel_booster = stage1_fuel
    fuel_booster_left = stage1_mass - booster_mass     # 300 Tonnes fuel left for return
    fuel_star = stage2_fuel
    
    Raptor_thrust = 2*1000*1000       # One Engine thrust (2 Million Newton)
    Raptor_burn_rate =  808       # 808 kg burned per second
#    Fo =  100000                  # Orientation cold gas thrust ( 100 kN )    
    g = 10                        # Gravity
    
    t = 0
    t_first = 110                 # First Stage cut-off 
    t_second = 140                 # Second stage cutt-off
    t_boostback = 125
    t_reentry = 150
    t_landing = 170
    
    u = 0                         # Booster initial velocity
    run_once = True               # Starship initial velocity transfer from booster
    
#    omega_0 = 0    
#    I = m*120*120/12             # Moment of inertia

    angle_star = 0
    angle_booster = 0
    cos = math.cos(angle_booster)
    sin = math.sin(angle_booster)
    cos2 = math.cos(angle_star)
    sin2 = math.sin(angle_star)
    pos_star = [0,0]
    pos_booster = [0,0]
    tail = 50
    s,s_star,s1,s1_star,s2,s2_star = 0,0,0,0,0,0
    
    d_theta1 = (30*math.pi)/(180*FPS*t_first)   # Rotate 30 degrees clockwise in t_first
    d_theta2 = (90*math.pi)/(180*FPS*2)    # Rotate 90 degrees anti-clockwise in 2 sec to reach 60 degree for boost-back
    d_theta3 = (30*math.pi)/(180*FPS*10)  # Rotate 30 degrees anti-clockwise in 10 sec to get vertical in reentry
    d_theta4 = (60*math.pi)/(180*FPS*t_second)  # Rotate Starship 60 degrees more in clockwise to get into orbit        
    
    while t < 180:
        display.fill(background) 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return    
            
##############################-------Booster Controls--------#########################################                                    
        star_burn = False
        booster_burn = False
    
        if t < t_first:
            booster_burn = True         
        elif t > t_boostback and t < (t_boostback+10):
            booster_burn = True
        elif t > t_reentry and t < (t_reentry+10):
            booster_burn = True
        elif t > t_landing:
            booster_burn = True
        else:
            booster_burn = False 
                            
        if booster_burn == True and t < t_first:
            fuel_booster -= (Raptor_burn_rate*36)/FPS         # 36 Raptor engines fired
            a = ((36*Raptor_thrust)/(StarShip_mass+fuel_booster+stage1_mass)) - g*cos   
            v = u + a*t
            s1 = s
            s = u*t + (a*t**2)/2
            s2 = s
            ds = s2-s1
            pos_booster[0] += ds*sin     # Booster X position
            pos_booster[1] += ds*cos     # Booster Y position
            angle_booster += d_theta1
        elif booster_burn == True and t >= t_first:
            fuel_booster_left -= (Raptor_burn_rate*3)/FPS      #  3 Raptor engines fired
            a = ((3*Raptor_thrust)/(fuel_booster_left+booster_mass)) - g*cos
            v = u + a*t 
            s1 = s
            s = u*t + (a*t**2)/2
            s2 = s
            ds = s2-s1
            pos_booster[0] += ds*sin
            pos_booster[1] += ds*cos
            if angle_booster > (-60*math.pi/180) and t < t_reentry:
                angle_booster -= d_theta2            
        else:
            a =  - g*cos         # Free fall of booster
            v = u + a*t
            s1 = s
            s = u*t + (a*t**2)/2
            s2 = s
            ds = s2-s1            
            pos_booster[0] += ds*sin
            pos_booster[1] += ds*cos
            if angle_booster < (15*math.pi/180) and t > t_boostback:
                angle_booster += d_theta2/5                
            if angle_booster > 0 and t > t_reentry:
                angle_booster -= d_theta2/5    
                
#############################-------StarShip Controls--------#######################################        
        if t > t_first+3: 
            star_burn = True
            
        if star_burn == True:
            if run_once == True:
                u_star = u
                run_once = False
            fuel_star -= (Raptor_burn_rate*3)/FPS             #  3 Raptor engines fired  
            a_star = ((1*Raptor_thrust)/(star_mass+fuel_star)) - g*cos2         
            v_star = u_star + a_star*t 
            s1_star = s_star
            s_star = u_star*t + (a_star*t**2)/2
            s2_star = s_star
            ds_star = s2_star-s1_star
            pos_star[0] += ds_star*sin2           # StarShip X position
            pos_star[1] += ds_star*cos2           # StarShip Y position
            angle_star += d_theta4           
        else:    
            a_star = a
            v_star = v            
            s_star = s                        
            pos_star[0] = pos_booster[0]
            pos_star[1] = pos_booster[1]
            angle_star = angle_booster
        
#        alpha = F1*l / I     # angular acceleration
#        omega_0*t + (alpha*t**2)/2     # Inclination        
                                             
        t += (1/FPS)                        
                    
#        if s < 50: 
#            tail = s 
#        else:    
#            tail = 50
#############################################################################################################  
        rot_image = pygame.transform.rotate(starship_image, -angle_star*180/math.pi)
        image_rect = rot_image.get_rect ()        
        w1, h1 = rot_image.get_size()
                
###########################################################################################################                 
        display.blit(profile,[0,0]) 
        pygame.draw.rect(display,(50,50,50),[platform[0],platform[1],150,10])         
        cos = math.cos(angle_booster)
        sin = math.sin(angle_booster)
#        altitude_star = (v*cos)**2/(2*a)
#        altitude_booster = (v*cos)**2/(2*a) 
        beta1 = math.atan(tail/d)     # Tail angle
        x1_tail = (d*math.cos(beta1-angle_booster)/math.cos(beta1))
        y1_tail = (d*math.sin(beta1-angle_booster)/math.cos(beta1))
        if angle_booster < (3.5*math.pi/180):
            display.blit(rot_image,[xy[0]+l*sin-w*cos/2+s*sin,xy[1]-l*cos-h*cos-w*sin/2-s*cos])
            pygame.draw.polygon(display,(255,255,255),[(xy[0]+l*sin-d*cos+s*sin,xy[1]-l*cos-d*sin-s*cos),
                                                      (xy[0]+l*sin+d*cos+s*sin,xy[1]-l*cos+d*sin-s*cos),
                                                      (xy[0]-l*sin+d*cos+s*sin,xy[1]+l*cos+d*sin-s*cos),
                                                      (xy[0]-l*sin-d*cos+s*sin,xy[1]+l*cos-d*sin-s*cos)])
            pygame.draw.polygon(display,(255,100,10),[(xy[0]-l*sin-d*cos+s*sin,xy[1]+l*cos-d*sin-s*cos),
                                                     (xy[0]-l*sin+d*cos+s*sin,xy[1]+l*cos+d*sin-s*cos),
                                                     (xy[0]-l*sin+d*cos+s*sin-x1_tail,xy[1]+l*cos+d*sin-s*cos+y1_tail)])                   ##############################################################################################################        
        
##############################################################################################################        
        canvas1.fill((0,0,0))
        cos2 = math.cos(angle_star)
        sin2 = math.sin(angle_star)
        if t < 90:
            canvas1.fill(background)
        else:
            canvas1.fill((0,0,0))
        pygame.draw.rect(canvas1, (0,255,0), [0,0,150,150], 5)         # Draw border inside canvas  
        canvas1_x = 75-w1/2
        canvas1_y = 60-h1/2
        canvas1.blit(rot_image,[canvas1_x,canvas1_y])
        pygame.draw.rect(canvas1, (0, 255, 0), [canvas1_x,canvas1_y,w1,h1], 1)
        text6 = font.render('Vel: '+str("{:.0f}".format(v_star)+' m/s'), True, font_color)
        canvas1.blit(text6, (5, 5))
        text10 = font.render('Tilt: '+str("{:.1f}".format(angle_star*180/math.pi)+' deg'), True, font_color)
        canvas1.blit(text10, (5, 125))
        if star_burn == True:            
            beta2 = math.atan(tail/4)
            x2_tail = (4*math.cos(beta2-angle_star)/math.cos(beta2))
            y2_tail = (4*math.sin(beta2-angle_star)/math.cos(beta2))
            pygame.draw.polygon(canvas1,(255,100,10),[(75-25*sin2-4*cos2,60+25*cos2-4*sin2),
                                                     (75-25*sin2+4*cos2,60+25*cos2+4*sin2),
                                                     (75-25*sin2+4*cos2-x2_tail,60+25*cos2+4*sin2+y2_tail)]) 
        draw_area1 = canvas1.get_rect().move(600-150, 90-30)                # Canvas location on screen  
        display.blit(canvas1, draw_area1)                                # View canvas on above location                 
         
##############################################################################################################                  
        canvas2.fill((0,0,0))         
        if t < 90 or t > 150: 
            canvas2.fill(background)        
        else:
            canvas2.fill((0,0,0))
        pygame.draw.rect(canvas2, (0,255,0), [0,0,150,150], 5)         # Draw border inside canvas                            
        pygame.draw.polygon(canvas2,(255,255,255),[(75+l*sin-d*cos,60-l*cos-d*sin),
                                                  (75+l*sin+d*cos,60-l*cos+d*sin),
                                                  (75-l*sin+d*cos,60+l*cos+d*sin),
                                                  (75-l*sin-d*cos,60+l*cos-d*sin)])
        if booster_burn == True:            
            pygame.draw.polygon(canvas2,(255,100,10),[(75-l*sin-d*cos,60+l*cos-d*sin),
                                                     (75-l*sin+d*cos,60+l*cos+d*sin),
                                                     (75-l*sin+d*cos-x1_tail,60+l*cos+d*sin+y1_tail)])           
        text5 = font.render('Vel: '+str("{:.0f}".format(v)+' m/s'), True, font_color)
        canvas2.blit(text5, (5, 5))
        text11 = font.render('Tilt: '+str("{:.1f}".format(angle_booster*180/math.pi)+' deg'), True, font_color)
        canvas2.blit(text11, (5, 125))
        draw_area2 = canvas2.get_rect().move(600-150, 400-150)           # Canvas location on screen          
        display.blit(canvas2, draw_area2)                                # View canvas on above location 
######################################################################################################################                
            
        text = font.render('Time: '+str("{:.0f}".format(t)+' sec'), True, font_color)
        display.blit(text, (400, 10))
        
        if t > 15 and t < 20:
            text12 = font.render('Starship launched', True, mid_font_color)
            text13 = font.render('       for Mars', True, mid_font_color)
        elif t > 35 and t < (t_first-15):
            text12 = font.render('   Of-Course ', True, mid_font_color)
            text13 = font.render('I Still Love You', True, mid_font_color)
        elif t > (t_first-2) and t < (t_first+1):
            text12 = font.render('First stage ', True, mid_font_color)
            text13 = font.render('  cut-off', True, mid_font_color)
        elif t > (t_first+2) and t < (t_first+5):
            text12 = font.render('Second stage ', True, mid_font_color)
            text13 = font.render('  ignition', True, mid_font_color)
        elif t > (t_first+8) and t < (t_boostback-3):
            text12 = font.render('Booster in ', True, mid_font_color)
            text13 = font.render('coast phase', True, mid_font_color)
        elif t > (t_boostback-1) and t < (t_boostback+10):
            text12 = font.render('Boostback burn ', True, mid_font_color)
            text13 = font.render('     to site', True, mid_font_color)
        elif t > (t_boostback+11) and t < (t_reentry-3):
            text12 = font.render('Re-orient for ', True, mid_font_color)
            text13 = font.render('  Re-entry', True, mid_font_color)
        elif t > (t_reentry-1) and t < (t_reentry+10):
            text12 = font.render('Re-entry burn', True, mid_font_color)
        elif t > (t_reentry+12) and t < (t_landing-2):
            text12 = font.render('  Landing ', True, mid_font_color) 
            text13 = font.render('re-orientaion', True, mid_font_color)
        elif t > t_landing and t < (t_landing+10):
            text12 = font.render('Landing burn', True, mid_font_color)
        else:
            text12 = font.render('', True, mid_font_color) 
            text13 = font.render('', True, mid_font_color)
        display.blit(text12, (235, 125))
        display.blit(text13, (235, 150))
        
        if pos_star[1] < 1000:
            text2 = font.render('StarShip XY ('+str("{:.0f}".format(pos_star[0]))+' , '
                                                    +str("{:.0f}".format(pos_star[1]))+') m',True, font_color)
        else:
            text2 = font.render('StarShip XY ('+str("{:.0f}".format(pos_star[0]/1000))+' , '
                                                    +str("{:.0f}".format(pos_star[1]/1000))+') km',True, font_color)
        display.blit(text2, (350, 35))
        
        if pos_booster[1] < 1000:
            text2 = font.render('Booster XY ('+str("{:.0f}".format(pos_booster[0]))+' , '
                                                   +str("{:.0f}".format(pos_booster[1]))+') m',True, font_color)
        else:
            text2 = font.render('Booster XY ('+str("{:.0f}".format(pos_booster[0]/1000))+' , '
                                                   +str("{:.0f}".format(pos_booster[1]/1000))+') km',True, font_color)
        display.blit(text2, (350, 220))
        
        text7 = font.render('Fuel left ', True, font_color)                
        display.blit(text7, (360,90-30))
        text8 = font.render(str("{:.0f}".format(fuel_star/1000)+' T'), True, font_color)                
        display.blit(text8, (370,110-30))
        text9 = font.render('Fuel left ', True, font_color)                
        display.blit(text9, (360,245))
        text4 = font.render(str("{:.0f}".format(fuel_booster/1000)+' T'), True, font_color)                
        display.blit(text4, (370,270))
        
        pygame.draw.rect(display,(255,200,0),[420,130-30,20,100])
        pygame.draw.rect(display,(255,0,0),[420,130-30,20,(1-(fuel_star/(stage2_fuel)))*100])
        pygame.draw.rect(display,(255,200,0),[420,290,20,100])
        pygame.draw.rect(display,(255,0,0),[420,290,20,(1-(fuel_booster/(stage1_fuel+fuel_booster_left)))*100])        
#############################################################################################################                
        pygame.display.update()
        clock.tick(FPS)
    
game()    
pygame.quit() 