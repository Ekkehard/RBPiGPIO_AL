# Python Implementation: Pulse
##
# @file       Pulse.py
#
# @version    2.0.0
#
# @par Purpose
# This module provides an abstraction layer for the Raspberry Pi General Purpose
# I/O (GPIO) PWM functionality for all models of the regular Raspberry Pi 0 and 
# up as well as the Raspberry Pi Pico.  Using this module, code should run and 
# use the common functionality of the GPIO and the PWM hardware shared by most 
# Raspberry Pi architectures without modifications on all those architectures.
# Where hardware PWM is not available, this class switches automatically to
# software-generated PWM.
#
# The module contains a class _HWPulse, which is the only class that needs to be
# modified should the RB Pi hardware PWM mechanism ever change.
#
# This code has been tested on a Raspberry Pi 0, 3, 4 and 5 and a Raspberry Pi 
# Pico.
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
#   Sat Dec 14 2024 | Ekkehard Blanz | extracted from GPIO_AL.py
#   Thu Feb 13 2025 | Ekkehard Blanz | made work on Pico again
#                   |                |

from GPIO_AL.tools import isPico, isHWpulsePin
from GPIO_AL.PinIO import PinIO
from GPIO_AL._PulseAPI import _PulseAPI

if isPico():
    # MicroPython silently ignores type hints without the need to import typing
    from GPIO_AL._PulsePicoHW import _PulsePicoHW
else:
    from typing import Union, Optional
    from GPIO_AL._PulsePiHW import _PulsePiHW
    from GPIO_AL._PulseSW import _PulseSW


class Pulse( _PulseAPI ):
    """!
    @brief Class to create arbitrary pulses on arbitrary pins.

    This class allows the generation of pulses of a large range of frequencies 
    and duty cycles as well as bursts with a specified number of impulses on any
    pin of the GPIO.  Some pins support hardware-generated pulses (on a 
    Raspberry Pi Pico, all pins do).  If this class detects that the requested 
    pin is one of those pins and that the necessary kernel modules are loaded,
    it will use hardware to generate the pulses; otherwise, the pulses will be 
    generated via software.  The software to generate the pulses will run in 
    the background with minimal overhead.  It is noted, however, that the 
    Raspbian (Debian) operating system is not a real-time operating system, and
    pulse parameters for software-generated pulses are therefore not guaranteed 
    to be stable and not meant for precise measurements.  In particular, if the 
    pulses are used to control servo motors, software-generated pulses can cause
    the motors to move erratically, especially under heavy CPU load on a 
    Raspberry Pi.
    
    This module can provide a list of pins that support hardware-generated 
    pulses, if they exist and the needed modules are loaded.  Minimal and 
    maximal frequencies are vastly different for hardware and software 
    generated pulses and this class won't accept out-of-reach frequencies as 
    parameters.  In particular, hardware-generated pulses can oscillate from 
    0.1 Hz up to about 5 MHz, while software-generated pulses can oscillate from
    arbitrarily low frequencies up to about 2 kHz.  For hardware-generated 
    pulses to work, the module pwm-2chan needs to be loaded by putting the line
    @code
        dtoverlay=pwm-2chan
    @endcode
    or
    @code
        dtoverlay=pwm-2chan,pin=18,func=2,pin2=19,func2=2
    @endcode
    in the file config.txt in /boot/firmware.  If that module is not loaded, 
    this class will only use software-generated pulses.  Usually, GPIO18 
    (pin 12) and GPIO19 (pin 35) are used for hardware pulses, but if the line
    @code
        dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4
    @endcode
    is placed in config.txt instead of one of the previously mentioned lines,
    the pins GPIO12 (pin 32) and GPIO13 (pin 33) are used for hardware pulses
    instead.  This class is aware of the content of the file config.txt and 
    checks if the system has been booted with that exact config.txt in place
    and that config.txt has not changed since then.
    
    The class is initiated with a pulsePin parameter that is either an int, a 
    string, or a PinIO object.  If it is given as an int, it is assumed that
    this represents the Pin number on the GPIO header of the Raspberry Pi, not
    the GPIO line number.  If it is given as a string, it must be of the form
    GPIO<line> where line is the GPIO line number.  Lastly, the parameter can be
    given as a PinIO object.  In this case, this object is used to generate
    software-timed pulses, even if it is a PinIO object for Pins that are
    capable of generating hardware pulses.
    
    This class can be initiated with a frequency in Hz given as a float or
    with a PObject (-derived object) with unit 'Hz'. 

    Both frequency and duty cycle can be read and set via properties of the 
    Pulse object, i.e. if myPulse is the Pulse object then
    @code
        value = myPulse.dutyCycle
    @endcode
    gets the current value of the duty cycle of the pulse and stores it in the
    variable value and
    @code
        myPulse.frequency = value
    @endcode
    sets the frequency of the pulse to whatever the variable value contains, 
    which is assumed to be be in Hz.
    
    When operating in burst mode, there are a few additional restrictions.  The 
    time the bursts can last is a minimum of 0.75 ms in hardware mode; in 
    software mode there is no restriction.  Additionally, the maximal frequency
    in burst mode is limited to 10 kHz in hardware mode; in software mode, all 
    frequency that this mode can operate with are also available in burst mode.
    Please note that in hardware mode the burst mechanism is controlled via 
    software timing and all restrictions with respect to software timing on 
    non-real-time operating systems apply for hardware bursts too.
    The class will properly dispose of all objects that are created internally.
    However, if an external PinIO object was provided, it will not be destroyed
    by this class upon termination.
    """

    def __init__( self,
                  pulsePin: Union[int, str, PinIO],
                  frequency: Union[float,object],
                  dutyCycle: Optional[float]=0.5,
                  bursts: Optional[int]=None ):
        """!
        @brief Constructor - sets up parameters and determines mode (hard- or
               software)
        This class merely provides a common API to both hardware and software
        generated pulses and selects the proper one of the two.
        @param pulsePin I/O header pin or GPIO line number to generate pulses 
               on.  Can be an integer header pin number or a string of the form
               GPIO<m> on the Raspberry Pi or GP<m> on the Pico where m 
               represents the line number
        @param frequency pulse frequency in Hz as float or PObject with unit Hz
        @param dutyCycle 0 <= dutyCycle <= 1 duty cycle of pulse (default: 0.5)
        @param bursts number of impulses to generate or None for continuous
                      operation (default: None)
        """
        self.__actor = None
        if isinstance( pulsePin, PinIO ) or not isHWpulsePin( pulsePin ):
            self.__actor = _PulseSW( pulsePin, frequency, dutyCycle, bursts )
        elif isPico():
            self.__actor = _PulsePicoHW( pulsePin, 
                                         frequency, 
                                         dutyCycle, 
                                         bursts )
        else:
            self.__actor = _PulsePiHW( pulsePin, frequency, dutyCycle, bursts )
        return

    def __del__( self ):
        """!
        @brief Destructor - only meaningful on the Raspberry Pi and
               potentially during Unit Tests on the Raspberry Pi Pico.

        Closes the pin.
        """
        self.stop()
        if self.__actor: 
            del self.__actor
            self.__actor = None
        return

    def  __enter__( self ):
        """!
        @brief Enter method for context management.
        @return an object that is used in the "as" construct, here it is self
        """
        return self

    def __exit__( self, excType, excValue, excTraceback ):
        """!
        @brief Exit method for context management.
        @param excType type of exception ending the context
        @param excValue value of the exception ending the context
        @param excTraceback traceback of exception ending the context
        @return False (will re-raise the exception)
        """
        # we could just let the destruction of the classes take care of properly
        # closing all the devices and timers, but we can also call the stop() 
        # method to come to a coordinated halt.  This requires that the "actor"
        # classes can tolerate repeated stop commands.
        self.stop()
        return False

    def __str__( self ) -> str:
        """!
        @brief String representation of this class - returns all settable
               parameters.
        """
        return self.__actor.__str__()

    def start( self ):
        """!
        @brief Method to start any pulse.
        """
        self.__actor.start()
        return

    def stop( self ):
        """!
        @brief Method to stop any pulse.
        """
        # In case of an emergency stop, the actor may not even exist (anymore)
        if self.__actor: self.__actor.stop()
        return

    @property
    def dutyCycle( self ) -> float:
        """!
        @brief Works as read/write property to get the current duty cycle.
        @return current duty cycle
        """
        return self.__actor.dutyCycle

    @dutyCycle.setter
    def dutyCycle( self, value: float ):
        """!
        @brief Works as the setter of a read/write property to set the duty
               cycle
        @param value new duty cycle to use 0 <= value <= 1
        """
        self.__actor.dutyCycle = value
        return

    @property
    def frequency( self ) -> float:
        """!
        @brief Implements read property of frequency.
        @return current frequency in Hz as a float (or PObject if that was 
                provided)
        """
        return self.__actor.frequency
  
    @frequency.setter
    def frequency( self, value: Union[float,object] ):
        """!
        @brief setter of the frequency read/write property.
        @param value pulse frequency in Hz or a PObject with unit Hz
        """
        self.__actor.frequency = value
        return



if "__main__" == __name__:
    import sys
    
    def main() -> int:
        """!
        @brief Unit test - coarse Python syntax test only.
        """
        
        o1 = Pulse( 'GPIO12', 1000 )
        o2 = Pulse( 'GPIO18', 1000 )
        
        del o1
        del o2
        
        print( '\nSUCCESS: no Python syntax errors detected\n' )
        
        return 0

    sys.exit( int( main() or 0 ) )
