# Python Implementation: _PulseSW
##
# @file       _Pulse.py
#
# @version    2.0.0
#
# @par Purpose
# Provide software generated pulses for the Pulse class of the GPIO_AL module.
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
#   Fri Jan 31 2025 | Ekkehard Blanz | extracted from Pulse.py
#                   |                |

 
import threading
import time
from typing import Union
from GPIO_AL.PinIO import PinIO
from GPIO_AL.GPIOError import GPIOError
from GPIO_AL._PulseAPI import _PulseAPI


class _PulseSW( _PulseAPI ):
    """!
    @brief Internal child class to implement software PWM pulses.
    """
    def __init__( self,
                  pulsePin,
                  frequency,
                  dutyCycle,
                  bursts ):
        """!
        @brief Constructor - sets up parameters.
        @param pulsePin integer with pin number in GPIO header or string with
                        GPIO<lineNumber>
        @param frequency in Hz as float or PObject with unit Hz
        @param dutyCycle duty cycle 0 <= dutyCylce <= 1
        @param bursts number of bursts or None for continuous operation
        """
        self.__swTimer = None
        self.__pin = None
        self.__burstCount = 0
        if isinstance( pulsePin, PinIO ):
            if pulsePin.mode != PinIO.Mode.OUTPUT and \
               pulsePin.mode != PinIO.Mode.OPEN_DRAIN:
                raise GPIOError ( 'pulsePin must be in OUTPUT or OPEN_DRAIN '
                                  'mode' )
            self.__pin = pulsePin
        else:
            self.__pin = PinIO( pulsePin, PinIO.Mode.OUTPUT ) # type: ignore
            
        super().__init__( pulsePin, frequency, dutyCycle, bursts )
        self._mode = self._Mode.SOFTWARE
        if self._bursts is None:
            self._bursts = -1
        self.__done = False
        return
        
    def __del__( self ):
        """!
        @brief Destructor - only meaningful on the Raspberry Pi and
               potentially during Unit Tests on the Raspberry Pi Pico.

        Properly destroys all objects that have been created by this class.
        """
        self.stop()
        if not isinstance( self._pulsePin, PinIO ):
            # We did not get the PinIO object from someone else
            # so we have to destroy it ourselves
            if self.__pin:
                self.__pin = None
        if self.__swTimer:
            self.__swTimer = None
        return

    def __runHigh( self ):
        """!
        @brief internal function to handle the "high" part of a software pulse.
        """
        if self.__done:
            return
        self.__nextTrigger += self._highTime
        self.__pin.level = PinIO.Level.HIGH # type: ignore
        self.__swTimer = threading.Timer( self.__nextTrigger - time.time(),
                                          self.__runLow )
        self.__swTimer.start()
        self.__burstCount += 1
        return

    def __runLow( self ):
        """!
        @brief internal function to handle the "low" part of a software pulse.
        """
        if self.__done:
            return
        self.__nextTrigger += self._lowTime
        self.__pin.level = PinIO.Level.LOW # type: ignore
        if self.__burstCount == self._bursts:
            self.__done = True
        self.__swTimer = threading.Timer( self.__nextTrigger - time.time(),
                                          self.__runHigh )
        self.__swTimer.start()
        return

    def start( self ):
        """!
        @brief Method to start the software pulse.
        """
        firstTimeCorrection = 0.000440
        self.frequency = self._frequency
        self.__nextTrigger = time.time() - firstTimeCorrection

        # we have to start with low, as the software pulse mechanism takes some 
        # time to "settle" - it is still not perfect, but the best we can do
        self.__runHigh()
        return

    def stop( self ):
        """!
        @brief Method to stop the software pulse.
        Closes and destroys the pin object, and, if present, the burst timer
        object.
        """
        
        self.__done = True
        if self.__swTimer: 
            self.__swTimer.cancel()
            self.__swTimer = None
        if self.__pin:
            self.__pin.level = PinIO.Level.LOW # type: ignore
        return

    @property
    def dutyCycle( self ) -> float:
        # Python bu? Doesn't recognize implementation in parent class
        return super().dutyCycle

    @dutyCycle.setter
    def dutyCycle( self, value ):
        """!
        @brief Works as the setter of a read/write property to set the duty
               cycle
        @param value new duty cycle to use 0 <= value <= 1
        """
        if self._bursts and not self.__done:
            raise GPIOError( 'Cannot set duty cycle during a burst in SW mode' )
        self._computeParams( self._frequency, value, self._bursts )
        if self._dutyCycle == 0: 
            self.__pin.level = PinIO.Level.LOW # type: ignore
        elif self._dutyCycle == 1:
            self.__pin.level = PinIO.Level.HIGH # type: ignore
        else:
            pass
        return

    @property
    def frequency( self ) -> Union[float, object]:
        # Python bu? Doesn't recognize implementation in parent class
        return super().frequency
  
    @frequency.setter
    def frequency( self, value ):
        """!
        @brief setter of a frequency property.
        @param value new duty cycle to use 0 <= value <= 1
        """
        try:
            if str( value.unit ) != 'Hz':
                raise GPIOError( 'Wrong frequency object specified: {0}'
                                 .format( value ) )
        except AttributeError:
            pass
        if float( value ) > 2000:
            raise GPIOError( 'frequency {0} exceeds max frequency for '
                             'software mode'.format( value ) )
        self._computeParams( value, self._dutyCycle, self._bursts )
        return

    @property
    def bursts( self ):
        # Python bug? Doesn't recognize implementation in parent class
        return super().bursts
  
    @bursts.setter
    def bursts( self, value ):
        """!
        @brief setter of the bursts property.  Requires re-start!
        @param value new number of impulses to use in a burst
        """
        self.stop()
        self._computeParams( self._frequency, self._dutyCycle, value )
        return

    @property
    def pin( self ) -> int:
        # Python bug? Doesn't recognize implementation in parent class
        return super().pin # type: ignore
    
    @property
    def line( self ) -> str:
        # Python bug? Doesn't recognize implementation in parent class
        return super().line