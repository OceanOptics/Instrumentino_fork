from __future__ import division

# Add path to library in dev
from os import path
import sys
sys.path.append(path.join('..', '..', 'instrumentino'))

from instrumentino import Instrument
from instrumentino.controllers.arduino import SysVarAnalogArduinoUnipolar
from instrumentino.controllers.arduino.pins import AnalogPins
from instrumentino.controllers.wetlabs import SysVarCountWETLabs
from instrumentino.controllers.wetlabs.bb3 import BB3


####################
# System constants #
####################
# Arduino pins
pinAnalWCSD859 = 2  # Analog WETLabs FDOM

# WETLabs BB3 wavelength
wvCountBB3349B = '470'
wvCountBB3349G = '532'
wvCountBB3349R = '660'


#####################
# System components #
#####################

analPins = AnalogPins('Arduino-FDOM',
    (SysVarAnalogArduinoUnipolar('FDOM', (0, 5), pinAnalWCSD859, None,
                                'Analog', units='volts'),))

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
        name = 'Inlinino'
        description = 'A simple data logger design for the NAAMES cruise.'
        version = '1.0'

        Instrument.__init__(self, comps, (), version, name, description)

###############
# Run program #
###############

if __name__ == '__main__':
    # run the program
    System()

