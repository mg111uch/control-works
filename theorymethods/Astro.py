import numpy as np

mE = 5.97e24	# mass of the earth in kg
vE = 30e3	# orbital velocity of the earth in meter/second
rE = 6.371e6	# radius of the earth in meter
dE = 149.6e9	# distance of the earth from the sun in meter
GRAVC = 6.67e-11	# Gravitational constant

# planets = ['Name', Position, Radius(km), x*rE,  Mass, Velocity, 'Color', 
# ['Mitra'], ['SamGrah'], ['Shatru'], [Uchh, Nich], DRISHTI, Element]
ea = ['Earth', dE, rE, 1*rE, mE, vE, 'Color']

su = ['Su_rya', 0, 696340, 109.3*rE, 333000*mE, 0, 'Color', 
	  ['Ch','Ma','Gu'],['Bu'],['Sh','Sa'], ['ARIES', 'LIBRA'],'Fire']
mo = ['Ch_andra', 0.3844e9, 1737, 0.2726*rE, mE, 1022, 'Color', 
	  ['Su','Bu'],['Ma','Gu','Sh','Sa'],[], ['TAURUS','SCORPIO'],'Water']
me = ['Bu_dh', 0.387*dE, 2440, 0.383*rE, 0.0553*mE, 1.607*vE, 'Color', 
	  ['Su','Sh'],['Ma','Gu','Sa'],['Ch'], ['VIRGO', 'PISCES'],'Earth']
ve = ['Sh_ukra', 0.723*dE, 6052, 0.95*rE, 0.815*mE, 1.174*vE, 'Color', 
	  ['Sa','Bu'],['Gu','Ma'],['Su','Ch'], ['PISCES', 'VIRGO'],'Water']
ma = ['Ma_ngal', 1.52*dE, 3390, 0.5321*rE, 0.107*mE, 0.802*vE, 'Color', 
	  ['Su','Ch','Gu'],['Sh','Sa'],['Bu'], ['CAPRICORN', 'CANCER'], [4,8],'Fire']
ju = ['Gu_ru', 5.20*dE, 69911, 10.973*rE, 317.8*mE, 0.434*vE, 'Color', 
	  ['Su','Ch','Ma'],['Sa'],['Sh','Bu'], ['CANCER', 'CAPRICORN'], [5,9],'Space']
sa = ['Sa_ni', 9.58*dE, 58232, 9.1401*rE, 95.2*mE, 0.323*vE, 'Color', 
	  ['Bu','Sh'],['Gu'],['Su','Ch','Ma'], ['LIBRA', 'ARIES'], [3,10],'Air']

ra = ['Ra_hu', 0, 0, 0, 0, 0, 'Color', 
	  [],[],[], [['TAURUS','GEMINI'], ['SCORPIO','SAGITTARIUS']], [5,9]]
ke = ['Ke_tu', 0, 0, 0, 0, 0, 'Color', 
	  [],[],[], [['SCORPIO','SAGITTARIUS'], ['TAURUS','GEMINI']], [5,9]]

ur = ['Uranus', 19.20*dE, 25362, 3.9808*rE, 14.5*mE, 0.228*vE, 'Color']
ne = ['Neptune', 30.05*dE, 24622, 3.8647*rE, 17.1*mE, 0.182*vE, 'Color']

# RASHI = [Sham{0}/Visham{1} - Alternate Rashis, 
# Six Awastha of 6 degree each{0-30} - Sam/Visham{1-Bal(25%);2-Kumar(50%);3-Yuva(100%);4-Vridh(50%);5-Mrit(25%)},
# 0-Char;1-Sthir;2-DwiSwabhav, 
# Tatva - 0-Fire;1-Prithvi;2-Vayu;3-Jal, Direction, [Directional strength]]
ARIES = ['Sham',0,'Char','Fire','East',['Mercury','Jupiter']]
TAURUS = ['ViSham',0,'Sthir','Prithvi','South']
GEMINI = ['Sham',0,'DwiSwa','Vayu','West']
CANCER = ['ViSham',0,'Char','Jal','North',['Moon','Venus']]
LEO = ['Sham',0,'Sthir','Fire','East']
VIRGO = ['ViSham',0,'DwiSwa','Prithvi','South']
LIBRA = ['Sham',0,'Char','Vayu','West',['Saturn']]
SCORPIO = ['ViSham',0,'Sthir','Jal','North']
SAGITTARIUS = ['Sham',0,'DwiSwa','Fire','East']
CAPRICORN = ['ViSham',0,'Char','Prithvi','South',['Sun','Mars']]
AQUARIUS = ['Sham',0,'Sthir','Vayu','West']
PISCES = ['ViSham',0,'DwiSwa','Jal','North']

def Force(p1,p2):
	F1 = GRAVC*p1[4]*p2[4]/np.power(np.abs(p1[1]-p2[1]),2)
	F2 = GRAVC*me[4]*p2[4]/np.power(np.abs(me[1]-p2[1]),2)
	return [p1[0], p2[0], np.round(F1/F2, 2)] # Relative to Mercury

print(Force(su,ea))
print(Force(mo,ea))
print(Force(me,ea))
print(Force(ve,ea))
print(Force(ma,ea))
print(Force(ju,ea))
print(Force(sa,ea))