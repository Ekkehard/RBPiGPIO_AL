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
#   Thu Feb 13 2025 | Ekkehard Blanz | made work on Pico again
#                   |                |

from machine import PWM, Pin, Timer
from GPIOError import GPIOError
from _PulseAPI import _PulseAPI

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
        """!
        @brief Constructor - sets up parameters.
        @param pulsePin integer with pin number in GPIO header or string with
                        GPIO<lineNumber>
        @param frequency in Hz as float or PObject with unit Hz
        @param dutyCycle duty cycle 0 <= dutyCylce <= 1
        @param bursts number of bursts or None for continuous operation
        """

        super().__init__( pulsePin, frequency, dutyCycle, bursts )
        self._mode = self._Mode.HARDWARE
        self.__pinObj = None
        self.__pwmObj = None
        self.__burstTimerObj = None
        self.__burstTime = None
        if bursts:
            if self._frequency > 1000:
                raise GPIOError( 'pulse frequency {0} Hz exceeds maximal '
                                 'frequency of 1 kHz for bursts for Pico '
                                 'under microPython'
                                 .format( self._frequency ) )

            # burst times must be in ms for the Pico Timer under microPico
            shortestBurstTime = 2
            self.__burstTime = \
                round( (self._bursts * self._period  # type: ignore
                        - self._lowTime / 2)  * 1000. )
            if self.__burstTime < shortestBurstTime:
                raise GPIOError( 'Bursts must last longer than {0} ms'
                                .format( shortestBurstTime ) )
        self.__pinObj = Pin( self._line )
        self.__pwmObj = PWM( self.__pinObj )
        return

    def __del__( self ):
        """!
        @brief Destructor - stops everything and even deinits the PWM device.
        """
        self.stop()
        if self.__pwmObj:
            self.__pwmObj.deinit()
            self.__pwmObj = None
        if self.__pinObj:
            # Pin object has no deinit method - we force its destructor upon
            # next garbage collection
            self.__pinObj = None
        if self.__burstTimerObj:
            self.__burstTimerObj.deinit()
            self.__burstTimerObj = None
        return

    def start( self ):
        """!
        @brief Method to start a HW pulse.
        """
        self.__pwmObj.freq( round( self._frequency ) ) # type: ignore
        if self.__burstTime:
            self.__burstTimerObj = Timer()
            self.__burstTimerObj.init( mode=Timer.ONE_SHOT,
                                       period=int( self.__burstTime ),
                                       callback=self.__stop )
        self.__pwmObj.duty_u16( round( 65535 * self._dutyCycle ) ) # type: ignore
        return

    def stop( self ):
        """!
        @brief Method to stop the HW pulse - sets duty cycle to 0.
        """
        if self.__pwmObj:
            self.__pwmObj.duty_u16( 0 )
        return
    
    def __stop( self, timerObj ):
        """!
        @brief Method to serve as a callback for the burst timer.
        @param as a callback function needs timer object as a parameter
               which will be ignored
        """
        self.stop()
        return

    @property
    def dutyCycle( self ):
        # Python bug? Doesn't recognize implementation in parent class
        return super().dutyCycle

    @dutyCycle.setter
    def dutyCycle( self, value ):
        """!
        @brief Works as the setter of a read/write property to set the duty
               cycle.
        @param value new duty cycle to use 0 <= value <= 1
        """
        self._computeParams( self._frequency, value, self._bursts )
        self.__pwmObj.duty_u16( round( 65535*self._dutyCycle ) ) # type: ignore
        return

    @property
    def frequency( self ):
        # Python bug? Doesn't recognize implementation in parent class
        return super().frequency
  
    @frequency.setter
    def frequency( self, value ):
        """!
        @brief setter of the frequency property.
        @param value new frequency to use
        """
        self._computeParams( value, self._dutyCycle, self._bursts )
        self.__pwmObj.freq( round( self._frequency ) ) # type: ignore
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
