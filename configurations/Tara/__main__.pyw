from __future__ import division

# Add path to library
from os import path
import sys
sys.path.append(path.join('..', '..', 'instrumentino'))

from instrumentino import Instrument
from instrumentino.controllers.arduino import SysVarAnalogArduinoUnipolar
from instrumentino.controllers.arduino.pins import AnalogPins


####################
# System constants #
####################
# Arduino pins
pinAnalWSCD = 2  # Analog WETLabs FDOM


#####################
# System components #
#####################
# Define analog component
analPins = AnalogPins('Arduino-WSCD',
    (SysVarAnalogArduinoUnipolar('FDOM', (0, 5), pinAnalWSCD, None,
                                'Analog', units='volts'),))


##########
# System #
##########

class System(Instrument):
    def __init__(self):
        comps = (analPins,)
        name = 'Inlinino'
        description = 'A simple data logger design for TARA Pacific.'
        version = '1.0'

        Instrument.__init__(self, comps, (), version, name, description)


###############
# Run program #
###############

if __name__ == '__main__':
    # run the program
    System()
