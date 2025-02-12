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
        @param dutyCycle duty cycle 0 < dutyCylce < 1
        @param bursts number of burts or None for continuous operation
        """
        self.__swTimer = None
        self.__pin = None
        self.__burstCount = 0
        super().__init__( pulsePin, frequency, dutyCycle, bursts )
        self._mode = self._Mode.SOFTWARE
        if self._bursts is None:
            self._bursts = -1
        if isinstance( pulsePin, PinIO ):
            if pulsePin.mode != PinIO.Mode.OUTPUT and \
               pulsePin.mode != PinIO.Mode.OPEN_DRAIN:
                raise GPIOError ( 'pulsePin must be in OUTPUT or OPEN_DRAIN '
                                  'mode' )
            self.__pin = pulsePin
        else:
            # TODO can we initialize that at level LOW?
            self.__pin = PinIO( pulsePin, PinIO.Mode.OUTPUT )
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
            # We did not get the PinIO object fomr someone else
            # so we have to destroy it ourselves
            if self.__pin:
                self.__pin = None
        if self.__swTimer:
            self.__swTimer = None
        return

    def __str__( self ):
        """!
        @brief String representation of this class - returns all settable
               parametrs.
        """
        if self._bursts == -1:
            bursts = None
        else:
            bursts = self._bursts
        return 'pin: {0}, frequency: {1}, duty cycle: {2}, bursts: {3}, ' \
               'mode: SOFTWARE' \
               .format( self._pulsePin,
                        self._orgFreq,
                        self._dutyCycle,
                        bursts )

    def __runHigh( self ):
        """!
        @brief internal function to handle the "high" part of a software pulse.
        """
        if self.__done:
            return
        self.__nextTrigger += self._highTime
        self.__pin.level = PinIO.Level.HIGH
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
        self.__pin.level = PinIO.Level.LOW
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
            self.__pin.level = PinIO.Level.LOW
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
        if self.__burstTime:
            raise GPIOError( 'Cannot set duty cycle during a burst in SW mode' )
        if value > 1 and value <= 100:
            self._dutyCycle = value / 100.
        else:
            self._dutyCycle = value
        if self._dutyCycle < 0 or self._dutyCycle > 1:
            raise GPIOError( 'Wrong duty cycle specified: {0}'
                             .format( dutyCycle ) )
        if self._dutyCycle == 0: 
            self.__pin.level = PinIO.Level.LOW
        elif self._dutyCycle == 1:
            self.__pin.level = PinIO.Level.HIGH
        else:
            self.__high = 1. / self._frequency * self._dutyCycle
            self.__low = 1. / self._frequency * (1. - self._dutyCycle)
        return

    @property
    def frequency( self ) -> Union[float, object]:
        # Python bu? Doesn't recognize implementation in parent class
        return super().frequency
  
    @frequency.setter
    def frequency( self, value ):
        """!
        @brief setter of a freqyency property.
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
        self._frequency = float( value )
        self._orgFreq = value
        self._period = 1. / self._frequency
        self.__high = self._period * self._dutyCycle
        self.__low = self._period * (1. - self._dutyCycle)
        return

