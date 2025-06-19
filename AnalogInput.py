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
#   Mon Jun 16 2025 | Ekkehard Blanz | added voltage property
#                   |                |
#

from GPIO_AL.GPIOError import GPIOError
from GPIO_AL._AnalogInputAPI import _AnalogInputAPI
from GPIO_AL.tools import isPico

hasVoltage = False
try:
    from PObjects import Voltage
    hasVoltage = True
except ModuleNotFoundError:
    hasVoltage = False


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
    analog input for all Raspberry Pi models, where needed with the help of 
    external ADC chips, thus allowing the same higher-level code to be used on 
    all Raspberry Pi models without significant modification.  The only 
    difference between using an external ADC and the built-in ADC of the 
    Raspberry Pi Pico is that the channel of external ADC chip must be specified
    where the Pico requires a Pin number or GP(IO) line string.

    This class uses the gpiozero library for the Raspberry Pis other than the 
    Pico internally, and hence supports all ADC chips supported by gpiozero.

    On Raspberry Pis without built-in ADC, the supported external ADC chips are 
    MCP3002, MCP3004, MCP3008, MCP3201, MCP3202, MCP3204, MCP3208, MCP3301, 
    MCP3302, or MCP3304.  These chips use the SPI protocol to communicate with 
    the Raspberry Pi.  They provide a maximal sample rate of about 20 kHz (if 
    the software can keep up) and a resolution of 10, 12 or 13 bits.
    
    The general GPIO SPI pins MOSI (GPIO10), MISO (GPIO9) and SCLK (GPIO11) are
    used for communication with these ADC chips.  The chipEnable parameter is 
    used to specify the SPI chip enable line number using CE0 (GPIO8) and CE1 
    (GPIO7).  These pins must therefore be connected to the appropriate pins on 
    the ADC chip as shown in the following table which uses the MCP3008 as an 
    example for the second column numbers.
    <table border="1" >
    <caption>Connection of MCP3x0y chips to Raspberry Pi other than Pico
             --- these chips have 10+x bits resolution and y analog input 
             channels</caption>
    <tr>
        <th>MCP3x0y Signal</th>
        <th>MCP3008 Pin Number</th>
        <th>RB Pi Line</th>  
        <th>RBPi Header Pin Number</th>
        <th>Description</th>
    </tr>
    <tr>
        <td>CH<m> (m = 0...y-1)</td>
        <td><n> (n = 1...8)</td>
        <td>not connected to RB Pi</td>
        <td>not connected to RB Pi</td>
        <td>Analog input channel connected to sensor</td>
    </tr>
    <tr>
        <td>DGND</td>
        <td>9</td>
        <td>GND</td>
        <td>6, 9, 14, 20, 25, 30, 34, or 39</td>
        <td>Digital ground</td>
    </tr>
    <tr>
        <td><SPAN STYLE="text-decoration:overline">CS</SPAN>/SHDN</td>
        <td>10</td>
        <td>GPIO7/CE1 or GPIO8/CE0</td>
        <td>24 or 26</td>
        <td>SPI chip select 0 or 1 / shutdown input 0 or 1</td>
    </tr>
    <tr>
        <td>D<sub>IN</sub></td>
        <td>11</td>
        <td>GPIO10/MOSI</td>
        <td>19</td>
        <td>SPI MOSI</td>
    </tr>
    <tr>
        <td>D<sub>OUT</sub></td>
        <td>12</td>
        <td>GPIO9/MISO</td>
        <td>21</td>
        <td>SPI MISO</td>
    </tr>
    <tr>
        <td>CLK</td>
        <td>13</td>
        <td>GPIO11/SCLK</td>
        <td>23</td>
        <td>SPI clock</td>
    </tr>
    <tr>
        <td>AGND</td>
        <td>14</td>
        <td>GND</td>
        <td>6, 9, 14, 20, 25, 30, 34, or 39</td>
        <td>Analog ground</td>
    </tr>
    <tr>
        <td>V<sub>REF</sub></td>
        <td>15</td>
        <td>3.3V</td>
        <td>1 or 17</td>
        <td>3.3 V analog reference voltage</td>
    </tr>
    <tr>
        <td>V<sub>DD</sub></td>
        <td>16</td>
        <td>3.3V</td>
        <td>1 or 17</td>
        <td>3.3 V digital supply voltage</td>
    </tr>
    </table>

    It is important to note that apart from specifying the intended target ADC 
    chip, the chipEnable is an active signal of the SPI protocol and cannot be
    static or hard-wired on a particular ADC chip, even if there is only one.
    
    As the Raspberry Pi Pico does not need an external ADC chip, the chipEnable 
    parameter as well as the chip parameter are ignored there.  The pins that 
    support ADC on the Pico are 31 (GP26/ADC0), 32 (GP27/ADC1), and 34 
    (GP28/ADC2).

    The voltage levels at the ADC pins are examined via a getter for the level 
    property of this class, i.e. if myDevice is an AnalogInput object, the 
    statement
    @code
        value = myDevice.level
    @endcode
    is used to examine the ADC input pin's voltage level as an integer between 0
    and  myDevice.maxLevel and store it in the variable value.  The value of
    myDevice.maxLevel is dependent on the ADC used, but is always 1023
    for 10-bit ADCs (e.g. MCP3002, MCP3004, MCP3008), 4095 for 12-bit ADCs
    (e.g. MCP3201, MCP3202, MCP3204, MCP3208), and 8191 for 13-bit ADCs (e.g. 
    MCP3301, MCP3302, MCP3304).  On the Raspberry Pi Pico, it is always 65535.

    CAUTION: Make sure you are only using voltages at any input pins of the ADC,
    external or built-in, that do not exceed the allowed level for your device.
    Otherwise, permanent  damage to the ADC chip or the Raspberry Pi Pico may 
    occur.
    """

    def __init__( self, 
                  channelOrPin: Union[int, str], 
                  chipEnable: Optional[int]=0,
                  chip: Optional[str]='MCP3008' ):
        """!
        @brief Constructor - initializes the class.
        @param channelOrPin either ADC integer channel or on the Pico I/O board 
               pin or GP line number.
               Can be an integer ADC channel number or on the Pico a board pin number or a string
               of the form GP<m> on the Pico where m represents the line number
        @param chipEnable can be either 0 or 1 for the SPI chip enable (defaults
               to 0 - ignored on the Pico)
        @param chip can be 'MCP3002', 'MCP3004', 'MCP3008', 'MCP3201', 
               'MCP3202', 'MCP3204', 'MCP3208', 'MCP3301', 'MCP3302', or 
               'MCP3304' (defaults to 'MCP3008' - ignored on the Pico)
        """
        self.__actor = None
        # instantiate actor
        if isPico():
            self.__actor = \
                _AnalogInputPico( channelOrPin ) # type: ignore
        else:
            self.__actor = \
                _AnalogInputPi( channelOrPin, chipEnable, chip ) # type: ignore
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
        @brief Close the ADC pin or chip - set this pin or all SPI pins (except 
        for the chipEnable pins) to input (high impedance) without pulling up or
        down.
        """
        if self.__actor:
            try:
                self.__actor.close()
            except Exception:
                pass
        self.__actor = None
        return

    @property
    def level( self ) -> int:
        """!
        @brief Works as read property to get the current ADC level
               of a Pin or ADC chip input as an int.
        @return int between 0 and maxLevel representing the ADC level
        """
        if self.__actor is None:
            raise GPIOError( 'Analog Input is not initialized' )
        return self.__actor.level
        
    @property
    def maxLevel( self ) -> int:
        """!
        @brief Works as read property to get the maximal value that the level
               property can return.
        @return maximal value the level property can return as an int
        """
        if self.__actor is None:
            raise GPIOError( 'Analog Input is not initialized' )
        return self.__actor.maxLevel
        
    if hasVoltage:
        @property
        def voltage( self ) -> Voltage: # type: ignore
            """!
            @brief Works as read property to get the current voltage at a pin or
                ADC chip input as a float.
            @return float between 0.0 and 3.3 representing the voltage at the pin
            """
            if self.__actor is None:
                raise GPIOError( 'Analog Input is not initialized' )
            return Voltage( 3.3 * self.__actor.level / self.__actor.maxLevel ) # type: ignore
    else:    
        @property
        def voltage( self ) -> float:
            """!
            @brief Works as read property to get the current voltage at a pin or
                ADC chip as a float.
            @return float between 0.0 and 3.3 representing the voltage at the pin
            """
            if self.__actor is None:
                raise GPIOError( 'Analog Input is not initialized' )
            return 3.3 * self.__actor.level / self.__actor.maxLevel


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
