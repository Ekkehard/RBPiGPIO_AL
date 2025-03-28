# Python Implementation: _PulseAPI
##
# @file       _PulseAPI.py
#
# @version    2.0.0
#
# @par Purpose
# Provide a common API for hardware and software generated pulses.
#
# This code has been tested on a Raspberry Pi 0, 3, 4 and 5 and a Raspberry Pi 
# Pico.
#
# @Comments
# This API should never be changed.  The most that is allowed is to add
# functionality, never to take existing functionality away!
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

from GPIO_AL.PinIO import PinIO
from GPIO_AL.GPIOError import GPIOError
from GPIO_AL.tools import lineToStr, isPico, argToLine, argToPin

if isPico():
    class ABC:
        pass
    def abstractmethod( f ):
        return f
    # MicroPython silently ignores type hints without the need to import typing
    Enum = object
else:
    from abc import ABC, abstractmethod # type: ignore
    from typing import Union, Optional
    from enum import Enum

    
class _PulseAPI( ABC ):
    """!
    @brief Abstract base class provides API for pulse classes.
    """

    class _Mode( Enum ): # type: ignore
        HARDWARE = 0
        SOFTWARE = 1

    def __init__( self,
                  pulsePin: Union[int,str,PinIO],
                  frequency: Union[float,object],
                  dutyCycle: float=0.5,
                  bursts: Optional[Union[int, None]]=None ):
        """!
        @brief Constructor - sets up common parameter for both modes.
        @param pulsePin integer with pin number in GPIO header, string with
                        GPIO<lineNumber> or PinIO object (not on Pico).
        @param frequency pulse frequency in Hz or a PObject with unit Hz
        @param dutyCycle 0 <= dutyCycle <= 1 duty cycle of pulse (default: 0.5)
        @param bursts number of impulses to generate or None for continuous
                      (default: None)
        """
        self._mode = None # to be overwritten by child
        self._pulsePin = pulsePin
        self._line = argToLine( pulsePin ) # type: ignore
        self._computeParams( frequency, dutyCycle, bursts )
        return
    
    def _computeParams( self,
                        frequency: Union[float,object],
                        dutyCycle: float,
                        bursts: Union[int, None] ):
        """!
        @brief (Re)compute essential parameters from user-supplied ones.
               Initially, and whenever some of them get changed.
        @param frequency pulse frequency in Hz or a PObject with unit Hz
        @param dutyCycle 0 <= dutyCycle <= 1 duty cycle of pulse (default: 0.5)
        @param bursts number of impulses to generate or None for continuous
                      (default: None)
        """
        self._bursts = bursts
        try:
            if str( frequency.unit ) != 'Hz': # type: ignore
                raise GPIOError( 'Wrong frequency object specified: {0}'
                                 .format( frequency ) )
        except AttributeError:
            pass
        self._orgFreq = frequency
        self._frequency = float( frequency ) # type: ignore
        self._dutyCycle = float( dutyCycle )
        if dutyCycle > 1 and dutyCycle <= 100:
            self._dutyCycle = dutyCycle / 100.
        else:
            self._dutyCycle = dutyCycle
        if self._dutyCycle < 0 or self._dutyCycle > 1:
            raise GPIOError( 'Wrong duty cycle specified: {0}'
                             .format( dutyCycle ) )
        self._period = 1 / self._frequency
        self._highTime = self._period * self._dutyCycle
        self._lowTime = self._period *  (1 - self._dutyCycle)
        return
            
    @abstractmethod
    def __del__( self ):
        """!
        @brief Destructor.  To be implemented by child.
        """
        pass
        
    def __str__( self ):
        """!
        @brief String representation of this class - returns all settable
               parameters.
        """
        return 'pin: {0}, line: {1}, frequency: {2}, duty cycle: {3}, ' \
               'bursts: {4}, mode: Pulse.{5}' \
               .format( self.pin,
                        self.line,
                        self.frequency,
                        self.dutyCycle,
                        self.bursts,
                        str( self._mode ).replace( '_', '' ) )
            
    @abstractmethod
    def start( self ):
        """!
        @brief Method to start any pulse to be implemented by child.
        """
        pass
        
    @abstractmethod
    def stop( self ):
        """!
        @brief Method to stop any pulse to be implemented by child.

        The child class must implement stop() in such a way that it can be
        called repeatedly.
        """
        pass

    @property
    def dutyCycle( self ) -> float:
        """!
        @brief read property to get duty cycle - can be overwritten by child.
        @return current duty cycle
        """
        return self._dutyCycle
  
    @dutyCycle.setter
    @abstractmethod
    def dutyCycle( self, value: float ):
        """!
        @brief Works as the setter of a read/write property to set the duty
               cycle to be implemented by child.
        @param value new duty cycle to use 0 <= value <= 1
        """
        pass

    @property
    def frequency( self ) -> Union[float, object]:
        """!
        @brief read property to get frequency to be implemented by child.
        @return current frequency as originally
        """
        return self._orgFreq
  
    @frequency.setter
    @abstractmethod
    def frequency( self, value: Union[float, object] ):
        """!
        @brief setter of the frequency property to be implemented by child.
        @param value pulse frequency in Hz or a PObject with unit Hz
        """
        pass

    @property
    def bursts( self ) -> Union[int, None]:
        """!
        @brief read property to get frequency to be implemented by child.
        @return current number of impulses in a burst
        """
        if self._bursts is not None and self._bursts <= 0:
            value = None
        else:
            value = self._bursts
        return value
  
    @bursts.setter
    @abstractmethod
    def bursts( self, value: int ):
        """!
        @brief setter of the burst property to be implemented by child.
        @param value number of impulses in a burst
        """
        pass

    @property
    def pin( self ) -> Union[int, str, PinIO, None]:
        """!
        @brief read property to get the pin number
        @return pin number
        """
        if isinstance( self._pulsePin, PinIO ):
            value = self._pulsePin.pin
        else:
            value = argToPin( self._pulsePin )
        return value
    
    @property
    def line( self ) -> str:
        """!
        @brief read property to get the line as a string
        @return line as a string
        """
        return lineToStr( self._line )