# Python Implementation: _AnalogInputPi
##
# @file       _AnalogInputPi.py
#
# @version    2.0.0
#
# @par Purpose
# Provide GPIO pin I/O for Raspberry Pi.
#
# This code has been tested on a Raspberry Pi 0, 3, 4 and 5.
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
# Copyright (C) 2025 W. Ekkehard Blanz\n
# See NOTICE.md and LICENSE.md files that come with this distribution.

# File history:
#
#      Date         | Author         | Modification
#  -----------------+----------------+------------------------------------------
#   Sun Feb 02 2025 | Ekkehard Blanz | extracted from PinIO.py
#                   |                |

import gpiozero
from GPIO_AL._AnalogInputAPI import _AnalogInputAPI
from GPIO_AL.GPIOError import GPIOError

class _AnalogInputPi( _AnalogInputAPI ):
    """!
    """
    def __init__( self, 
                  channel, 
                  chipEnable,
                  chip ):
        """!
        @brief Constructor.
        @param pin I/O header pin number or GP line
        """
        self.__deviceObj = None
        if chip == 'MCP3001':
            self.__deviceObj = gpiozero.MCP3001( channel=channel, 
                                                 device=chipEnable )
        elif chip == 'MCP3002':
            self.__deviceObj = gpiozero.MCP3002( channel=channel, 
                                                 device=chipEnable )
        elif chip == 'MCP3004': 
            self.__deviceObj = gpiozero.MCP3004( channel=channel, 
                                                 device=chipEnable )
        elif chip == 'MCP3008':
            self.__deviceObj = gpiozero.MCP3008( channel=channel, 
                                                 device=chipEnable )
        elif chip == 'MCP3201':
            self.__deviceObj = gpiozero.MCP3201( channel=channel, 
                                                 device=chipEnable )
        elif chip == 'MCP3202':
            self.__deviceObj = gpiozero.MCP3202( channel=channel, 
                                                 device=chipEnable )
        elif chip == 'MCP3204':
            self.__deviceObj = gpiozero.MCP3204( channel=channel, 
                                                 device=chipEnable )
        elif chip == 'MCP3208':
            self.__deviceObj = gpiozero.MCP3208( channel=channel, 
                                                 device=chipEnable )
        elif chip == 'MCP3301':
            self.__deviceObj = gpiozero.MCP3301( channel=channel, 
                                                 device=chipEnable )
        elif chip == 'MCP3302':
            self.__deviceObj = gpiozero.MCP3302( channel=channel, 
                                                 device=chipEnable )
        elif chip == 'MCP3304':
            self.__deviceObj = gpiozero.MCP3304( channel=channel, 
                                                 device=chipEnable )
        else:
            raise GPIOError( 'unknown ADC chip' )
        self.__chip = chip

        if channel < 0 or channel >= int( chip[6] ):
            raise GPIOError( 'invalid channel for chip {0}'.format( chip ) )
        self.__channel = channel

        if chipEnable < 0 or chipEnable > 1:
            raise GPIOError( 'invalid chip enable pin {0}'.format( chipEnable ) )
        self.__chipEnable = chipEnable

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
               parameters.
        """
        if self.__deviceObj is None:
            raise GPIOError( 'device not open' )
        return 'analog input via ADC chip {0} (resolution: {1} bits) ' \
               'analog input channel: {2}, chip enable: {3}, ' \
               .format( self.__chip,
                        self.__deviceObj.bits, 
                        self.__channel, 
                        self.__chipEnable )

    def close( self ):
        """!
        @brief Close an ADC on Raspberry Pi.

        Gpiozero closes the SPI device properly and leaves the associated pins 
        that can also be used as regular GPIO pins in input mode.  The CE0 and 
        CE1 pins are not used by the GPIO library and are left in output mode 
        and pulled high when not in use by any SPI software.
        """
        if self.__deviceObj is not None:
            self.__deviceObj.close()
        self.__deviceObj = None
        return

    @property
    def level( self ):
        """!
        @brief Works as read property to get the current ADC level
               of an ADC channel
        @return ADC level as int between 0 and maxLevel
        """
        if self.__deviceObj is None:
            raise GPIOError( 'device not open' )
        return self.__deviceObj.raw_value
    
    @property
    def maxLevel( self ) -> int:
        """!
        @brief Works as read property to get the maximum ADC level
               of a Pin.
        @return maximum ADC level
        """
        if self.__deviceObj is None:
            raise GPIOError( 'device not open' )
        return 2**self.__deviceObj.bits - 1