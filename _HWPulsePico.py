# Python Implementation: _HWPulsePico
##
# @file       _HWPulsePico.py
#
# @version    2.0.0
#
# @par Purpose
# Provide hardware generated pulses for the Pulse class of the GPIO_AL module 
# for Raspberry Pico.
#
# This code has been tested on a Raspberry Pi Pico.
#
# This class is the only class that needs to be modified should the RB Pi 
# hardware PWM mechanism ever change.
#
# @par Known Bugs
# None
#
# @author
# W. Ekkehard Blanz <Ekkehard.Blanz@gmail.com>
#
# @copyright
# Copyright (C) 2021 - 2025 W. Ekkehard Blanz\n
# See NOTICE.md and LICENSE.md files that come with this distribution.

# File history:
#
#      Date         | Author         | Modification
#  -----------------+----------------+------------------------------------------
#   Fri Jan 31 2025 | Ekkehard Blanz | extracted from Pulse.py
#                   |                |

from typing import Union, Optional
from GPIO_AL.GPIOError import GPIOError
from GPIO_AL._PulseAPI import _PulseAPI

class _HWPulsePi( _PulseAPI ):
    """!
    @brief Internal child class to implement hardware PWM pulses on a Raspbery 
           Pi.
    
    If the RB Pi hardware PWM support changes, this is the only class that needs
    to be touched.  Be mindful to keep the API determined by PulseAPI as is. 
    """
    def __init__( self,
                  pulsePin: Union[int, str],
                  frequency: Union[float,object],
                  dutyCycle: float,
                  bursts: Union[int, None] ):
        raise GPIOError( 'Not yet implemented', GPIOError.Severity.FATAL )