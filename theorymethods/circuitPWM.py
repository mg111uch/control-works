import numpy as np
import math
import matplotlib
matplotlib.use('TKAgg')
import matplotlib.pyplot as plt
# from PySpice.Spice.Netlist import Circuit
# from PySpice.Unit import *

# t = np.linspace(0, 1/50.0, 50)
# v = np.sin(2*np.pi*50*t) # 50 Hz
# i = 1/2.0*np.sin(2*2*np.pi*50*t) # 2nd order

# p = v*i

# plt.figure()
# plt.plot(t, v, label='voltage (V)')
# plt.plot(t, v, label='current (A)')
# plt.plot(t, p, label='instantaneous power (W)')
# plt.plot(t, np.average(p)*np.ones_like(p), label='average (W)')
# plt.xlabel('Time (s)')
# plt.xlim([0, 0.02])
# plt.legend()
# plt.show()

# '''
carrier_frequency = 10000
modulation_frequency = 50

carrier_signal = np.sin(2 * np.pi * carrier_frequency * np.linspace(0, 1, 1000))
modulation_signal = np.sin(2 * np.pi * modulation_frequency * np.linspace(0, 1, 1000))

pwm_signal = np.where(carrier_signal > modulation_signal, 1, 0)

plt.plot(pwm_signal)
plt.xlabel('Time (s)')
plt.ylabel('PWM Signal')
plt.show()
# '''
