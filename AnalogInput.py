# Python Implementation: AnalogInput
##
# @file       AnalogInput.py
#
# @version    2.0.0
#
# @par Purpose
# This module provides an abstraction layer for the Raspberry Pi analog input
# functionality even for Raspberry Pi models that do not have this functionality
# built in.  For models other than the Raspberry Pi Pico, it uses a specifiable
# external ADC to provide the analog input functionality.
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
# Copyright (C) 2025 W. Ekkehard Blanz\n
# See NOTICE.md and LICENSE.md files that come with this distribution.

# File history:
#
#      Date         | Author         | Modification
#  -----------------+----------------+------------------------------------------
#   Wed Mar 19 2025 | Ekkehard Blanz | created
#                   |                |
#

from GPIO_AL.GPIOError import GPIOError
from GPIO_AL._AnalogInputAPI import _AnalogInputAPI
from GPIO_AL._AnalogInputPi import _AnalogInputPi
from GPIO_AL._AnalogInputPico import _AnalogInputPico
from GPIO_AL.tools import isPico

# determine platform and import appropriate module for GPIO access
if isPico():
    # MicroPython silently ignores type hints without the need to import typing
    from GPIO_AL._AnalogInputPico import _AnalogInputPico
else:
    from typing import Union, Optional
    from GPIO_AL._AnalogInputPi import _AnalogInputPi



class AnalogInput( _AnalogInputAPI ):
    """!
    @brief Class to encapsulate analog input capabilities
    
    To put it upfront, Raspberry Pi models other than the Raspberry Pi Pico do
    not have analog input capabilities built-in.  All the models that don't have
    this capability must use external Analog-to-Digital-Converter (ADC) hardware
    to provide it.  But since many sensors one might want to connect to a 
    Raspberry Pi provide analog outputs, this class provides a common API for 
    analog input for all Raspberry Pi models, thus allowing the same higher-
    level code to be used on all Raspberry Pi models without significant 
    modification.  The only difference between using an external ADC and the
    built-in ADC of the Raspberry Pi Pico is that the external ADC channel must 
    be specified where the Pico requires a Pin or line number.  This class uses
    the gpiozero library for the Raspberry Pis other than the Pico internally, 
    and hence supports all ADC chips supported by gpiozero.

    On Raspberry Pis other than the Pico, the supported ADC chips are MCP3002,
    MCP3004, MCP3008, MCP3201, MCP3202, MCP3204, MCP3208, MCP3301, MCP3302, or 
    MCP3302.  These chips use the SPI protocol to communicate with the Raspberry
    Pi.  The general SPI pins MOSI (GPIO10), MISO (GPIO9) and SCLK (GPIO11) are 
    used for communication with the ADC chip.  The chipEnable parameter is used
    to specify the SPI chip enable line number using CE0 (GPIO8) and CE1 (GPIO7).
    These pins must therefore be connected to the appropriate pins on the ADC
    chip.

    Pins' voltage levels are examined via a getter for the level property of 
    this class, i.e. if myDevice is a AnalogInput object via the statement
    @code
        value = myDevice.level
    @endcode
    to examine the pin's voltage level as an integer between 0 and 
    myDevice.maxLevel and store it in the variable value.

    CAUTION: Make sure you are only using voltages at any input pins of the ADC 
    that do not exceed the allowed level for your device.  Otherwise, permanent 
    damage to the ADC chip may occur.
    """

    def __init__( self, 
                  channelOrPin: Union[int, str], 
                  chipEnable: Optional[int]=0,
                  chip: Optional[str]='MCP3008' ):
        """!
        @brief Constructor - initializes the class.
        @param either ADC channel or I/O board pin or GP line number on the 
               Pico.  Can be an integer channel or board pin number or a string
               of the form GP<m> on the Pico where m represents the line number
        @param chipEnable can be either 0 or 1 for the SPI chip enable (defaults
               to 0 - ignored on the Pico)
        @param chip (can be 'MCP3002', 'MCP3004', 'MCP3008', 'MCP3201', 
               'MCP3202', 'MCP3204', 'MCP3208', 'MCP3301', 'MCP3302', or 
               'MCP3302', defaults to 'MCP3008' - ignored on the Pico)
        """
        self.__open = False
        # instantiate actor
        if isPico():
            self.__actor = \
                _AnalogInputPico( channelOrPin ) # type: ignore
        else:
            self.__actor = \
                _AnalogInputPi( channelOrPin, chipEnable, chip ) # type: ignore
        self.__open = True
        return

    def __del__( self ):
        """!
        @brief Destructor - only meaningful on the Raspberry Pi and
               potentially during Unit Tests on the Raspberry Pi Pico.  Only
               gets called when the garbage collector decides to call it, which
               may be never.

        Closes the pin and terminates the event loop thread if running.
        """
        self.close()
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

        Closes the pin.
        @param excType type of exception ending the context
        @param excValue value of the exception ending the context
        @param excTraceback traceback of exception ending the context
        @return False (will re-raise the exception)
        """
        self.close()
        return False

    def __str__( self ) -> str:
        """!
        @brief String representation of this class - returns all settable
               parameters.
        """
        return self.__actor.__str__()

    def close( self ):
        """!
        @brief Close the Pin - set it to input (high impedance) without pulling
               up or down.
        """
        if self.__open and self.__actor:
            self.__actor.close()
        self.__open = False
        return

    @property
    def level( self ) -> int:
        """!
        @brief Works as read property to get the current voltage level
               of a Pin or ADC chip input as an int.
        @return int between 0 and maxLevel representing the voltage level
        """
        if self.__actor:
            return self.__actor.level
        else:
            return 0
        
    @property
    def maxLevel( self ) -> int:
        """!
        @brief Works as read property to get the maximal value that the level
               property can return.
        """
        if not self.__actor:
            raise GPIOError( 'Analog Input actor is not initialized' )
        return self.__actor.maxLevel


#  main program - NO Unit Test - Unit Test is in separate file

if __name__ == "__main__":

    import sys

    def main():
        """!
        @brief Main program - to save some resources, we do not include the
               Unit Test here.  In essence, this just checks the syntax.
        """
        with AnalogInput( 0 ) as device:
            print( device )
        print( '\nSUCCESS: No Python syntax errors detected\n' )
        print( 'Please use included GPIO_ALUnitTest.py for complete Unit Test' )
        return 0

    sys.exit( int( main() or 0 ) )
