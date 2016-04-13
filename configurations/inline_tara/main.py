from __future__ import division

# Add path to library in dev
from os import path
import sys
sys.path.append(path.join('..', '..', 'instrumentino'))

from instrumentino import Instrument
# from instrumentino import cfg
# from instrumentino.action import SysAction, SysActionParamTime,\
#     SysActionParamFloat, SysActionParamInt
from instrumentino.controllers.arduino import SysVarDigitalArduino,\
    SysVarAnalogArduinoUnipolar
from instrumentino.controllers.arduino.pins import DigitalPins, AnalogPins
from instrumentino.controllers.wetlabs import SysVarCountWETLabs
from instrumentino.controllers.wetlabs.bb3 import BB3


####################
# System constants #
####################
# Arduino pins
pinAnalDARK = 1     # Analog FDOM
pinAnalWHITE = 2    # Analog FCHL
pinAnalWCSD859 = 4  # Analog WETLabs FDOM
pinAnalKY013 = 3    # Analog Temperature Instrument
pinDigiKeyes = 8    # Digital Temperature&Humidity Instrument

# WETLabs BB3 wavelength
wvCountBB3349B = '470'
wvCountBB3349G = '532'
wvCountBB3349R = '660'

#####################
# System components #
#####################

analPins = AnalogPins('Arduino-FDOM', (
    SysVarAnalogArduinoUnipolar('DARK', (0, 5), pinAnalDARK, None,
                                'Analog', units='volts'),
    SysVarAnalogArduinoUnipolar('WHITE', (0, 5), pinAnalWHITE, None,
                                'Analog', units='volts'),
    SysVarAnalogArduinoUnipolar('Temperature', (0, 5), pinAnalKY013, None,
                                'Analog', units='volts'),
    SysVarAnalogArduinoUnipolar('FDOM', (0, 5), pinAnalWCSD859, None,
                                'Analog', units='volts')))

bb3_349 = BB3('ECO-BB3', (
    SysVarCountWETLabs('beta 470', (45, 4122), _key=wvCountBB3349B,
                       _compName="BB3", _units="counts"),
    SysVarCountWETLabs('beta 532', (45, 4122), _key=wvCountBB3349G,
                       _compName="BB3", _units="counts"),
    SysVarCountWETLabs('beta 660', (45, 4122), _key=wvCountBB3349R,
                       _compName="BB3", _units="counts"),
))


##########
# System #
##########


class System(Instrument):
    def __init__(self):
        comps = (analPins, bb3_349)
        actions = ()
        name = 'Inlino'
        description = 'A simple data logger design for the NAAMES cruise. '\
                      'Plug Arduino\'s pin as follow:\n\tA1: FDOM\n'\
                      '\tA2: FCHL\n\tA3: Temperature\n\tA4: Humidity\n'
        version = '0.1'

        Instrument.__init__(self, comps, actions, version, name, description)

###############
# Run program #
###############

if __name__ == '__main__':
    # run the program
    System()

# run with command: nice -20 pythonw main.py
