# Python Implementation: _AnalogInputPico
##
# @file       _AnalogInputPico.py
#
# @version    2.0.0
#
# @par Purpose
# Provide GPIO pin I/O for Raspberry Pi Pico.
#
# This code has been tested on a Raspberry PiPico.
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
#   Sun Feb 02 2025 | Ekkehard Blanz | extracted from PinIO.py
#   Thu Feb 13 2025 | Ekkehard Blanz | made work on Pico again
#                   |                |

import machine
from GPIO_AL.GPIOError import GPIOError
from GPIO_AL._AnalogInputAPI import _AnalogInputAPI
from GPIO_AL.tools import argToPin, argToLine, lineToStr


class _AnalogInputPico( _AnalogInputAPI ):
    """!
    """
    def __init__( self, 
                  pin ):
        """!
        @brief Constructor.
        @param pin I/O header pin number or GPIO line
        """
        self.__line = argToLine( pin )
        self.__pin = argToPin( pin )
        self.__pinObj = machine.Pin( self.__line )
        self.__adcObj = machine.ADC( self.__pinObj )

        return

    def __del__( self ):
        """!
        @brief Destructor.
        """
        self.close()
        return
        
    def __str__( self ) -> str:
        """!
        @brief String representation of this class - returns all settable
               parameters.  Can be overwritten by child.
        """
        return 'header pin: {0}, line: {1}, mode: analog input' \
               .format( self.__pin,
                        lineToStr( self.__line ) )

    def close( self ):
        """!
        @brief Close the Pin - set it to input (high impedance) without pulling
               up or down.  Terminates event loop thread if running.
        """
        self.__pinObj.init( self.__line, machine.Pin.IN )
        return

    @property
    def level( self ) -> int:
        """!
        @brief Works as read property to get the current voltage level
               of a Pin.
        @return current voltage level between 0 and maxLevel
        """
        if not self.__adcObj:
            raise GPIOError( 'ADC object not initialized' )
        return self.__adcObj.read_u16()
    
    @property
    def maxLevel( self ) -> int:
        """!
        @brief Works as read property to get the maximum voltage level
               of a Pin.
        @return maximum voltage level
        """
        return 65535
