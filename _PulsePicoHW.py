# Python Implementation: _PulsePicoHW
##
# @file       _PulsePicoHW.py
#
# @version    2.0.0
#
# @par Purpose
# Provide hardware generated pulses for the Pulse class of the GPIO_AL module 
# for Raspberry Pi Pico.
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

from machine import PWM, Pin
from GPIO_AL.GPIOError import GPIOError
from GPIO_AL._PulseAPI import _PulseAPI

class _PulsePicoHW( _PulseAPI ):
    """!
    @brief Internal child class to implement hardware PWM pulses on a Raspberry 
           Pi Pico.
    
    If the RB Pi hardware PWM support changes, this is the only class that needs
    to be touched.  Be mindful to keep the API determined by PulseAPI as is. 
    """
    def __init__( self,
                  pulsePin,
                  frequency,
                  dutyCycle,
                  bursts ):

        super().__init__( pulsePin, frequency, dutyCycle, bursts )
        self._mode = self._Mode.HARDWARE
        self.__pwmObj = None
        shortestBurstTime = 0.000750
        if self._bursts:
            self.__burstTime = self._bursts * self._period - self._lowTime / 2
            if self.__burstTime < shortestBurstTime:
                raise GPIOError( 'Time bursts must last longer than {0} s'
                                .format( shortestBurstTime ) )
            self.__burstTime -= shortestBurstTime
        return

    def __del__( self ):
        """!
        @brief Destructor - stops everything and even unexports the pwm device
               for this channel on the Pi.
        """
        self.stop()
        self.__pwmObj = None
        return

    def __str__( self ):
        """!
        @brief String representation of this class - returns all settable
               parameters.
        """
        return 'pin: {0}, frequency: {1}, duty cycle: {2}, bursts: {3}, ' \
               'mode: HARDWARE' \
               .format( self._pulsePin,
                        self._orgFreq,
                        self._dutyCycle,
                        self._bursts )

    def start( self ):
        """!
        @brief Method to start a HW pulse.
        """
        if self.__burstTime:
            self.__burstTimer = threading.Timer( self.__burstTime,
                                                 self.stop )
        self.__pwmObj = PWM( Pin( self._pulsePin ), 
                             freq=self._frequency, 
                             duty_u16=round( 65535 * self._dutyCycle ) )
        if self.__burstTimer:
            self.__burstTimer.start()
        return

    def stop( self ):
        """!
        @brief Method to stop the HW pulse; destroys the burst timer object if
               present.
        """
        self.__pwmObj.deinit()
        return

    @property
    def dutyCycle( self ) -> float:
        # Python bu? Doesn't recognize implementation in parent class
        return super().dutyCycle

    @dutyCycle.setter
    def dutyCycle( self, value ):
        """!
        @brief Works as the setter of a read/write property to set the duty
               cycle.
        @param value new duty cycle to use 0 <= value <= 1
        """
        if value > 1 and value <= 100:
            self._dutyCycle = value / 100.
        else:
            self._dutyCycle = value
        if self._dutyCycle < 0 or self._dutyCycle > 1:
            raise GPIOError( 'Wrong duty cycle specified: {0}'
                             .format( value ) )
        self.__pwmObj.duty_u16( round( 65535 * self._dutyCycle ) )
        return

    @property
    def frequency( self ) -> Union[float, object]:
        # Python bu? Doesn't recognize implementation in parent class
        return super().frequency
  
    @frequency.setter
    def frequency( self, value ):
        """!
        @brief setter of the frequency property.
        @param value new frequency to use
        """
        try:
            if str( value.unit ) != 'Hz':
                raise GPIOError( 'Wrong frequency object specified: {0}'
                                 .format( value ) )
        except AttributeError:
            pass
        self._orgFreq = value
        self._frequency = float( value )
        try:
            self.__pwmObj.freq( self._frequency )
        except:
            raise GPIOError( 'Wrong frequency specified: {0}'.format( value ) )
        return
