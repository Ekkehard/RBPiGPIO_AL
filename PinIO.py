# Python Implementation: PinIO
##
# @file       PinIO.py
#
# @version    2.0.0
#
# @par Purpose
# This module provides an abstraction layer for the Raspberry Pi General Purpose
# I/O (GPIO) single pin I/O functionality for all models of the regular 
# Raspberry Pi 0 and up Raspberry Pi 5, as well as the Raspberry Pi Pico
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
#   Wed Oct 27 2021 | Ekkehard Blanz | created
#   Thu Dec 09 2021 | Ekkehard Blanz | changed default mode for I2Cbus for
#                   |                | Raspberry Pi to Software
#   Sat Dec 18 2021 | Ekkehard Blanz | fixed bug in writeByteReg and
#                   |                | writeBlockReg for RB Pi Software I2C
#   Sun Jan 02 2022 | Ekkehard Blanz | replaced ARCHITECTURE with CPU_INFO
#   Wed Apr 27 2022 | Ekkehard Blanz | streamlined cpuInfo() and platform()
#                   |                | with common.py
#   Thu Apr 28 2022 | Ekkehard Blanz | added attempts parameter to __init__()
#                   |                | of I2Cbus and improved performance of
#                   |                | platform()
#   Thu Nov 07 2024 | Ekkehard Blanz | switched to gpiod v 2.2 on RB Pi
#   Sat Dec 14 2024 | Ekkehard Blanz | removed GPIOError, Pulse, and I2Cbus and
#                   |                | placed in separate files
#   Thu Feb 13 2025 | Ekkehard Blanz | made work on Pico again
#                   |                |
#


from GPIO_AL._PinIOAPI import _PinIOAPI
from GPIO_AL.tools import isPico

# determine platform and import appropriate module for GPIO access
if isPico():
    # MicroPython silently ignores type hints without the need to import typing
    from _PinIOPico import _PinIOPico
else:
    from typing import Union, Optional
    # the following data and functions are not needed for the Raspberry Pi Pico
    import gpiod
    if int( gpiod.__version__.split( '.' )[0] ) < 2 or \
       (int( gpiod.__version__.split( '.' )[0] ) == 2 and \
        int( gpiod.__version__.split( '.' )[1] ) < 2):
        raise ValueError( 'GPIO_AL requires gpiod version 2.2 or higher' )
    from GPIO_AL._PinIOPi import _PinIOPi



class PinIO( _PinIOAPI ):
    """!
    @brief Class to encapsulate single Pin I/O.

    This class allows a given pin to be configured as an input pin with or
    without pull up or pull down resistors, as a regular output pin, or as an
    open drain pin, in which case only setting its level to PinIO.Level.LOW will
    actually drive it low and setting its level to PinIO.Level.HIGH will put the
    Pin in input mode with a pullup resistor.  Levels of Pins that have been set 
    to any input mode cannot be set; levels of Pins that have been set to output
    mode cannot be read; levels of Pins that have been set to open drain mode
    can be set and read.  Upon closing (or destruction), the pin is set to input
    mode without pullup or pulldown to best protect the Raspberry Pi and the
    circuitry it is connected to.

    Moreover, the class allows a callback function to be specified as well as
    the direction of the signal edge that will trigger the event for the 
    callback function to be called; both can be None, in which case no callback 
    functionality is provided for the selected Pin.  Callback functions must be 
    provided by the user in the form
    @code
        def myCallback( pinObj ):
            ...
            return
    @endcode
    which works on all Raspberry Pi architectures.  Here pinObj is the PinIO 
    object associated with the line on which this event occurred.

    NOTE: It is strongly recommended to instantiate this class using a "with"
    statement.  Otherwise it cannot be guaranteed that the destructor of the 
    class will be called as the Python interpreter will not call the destructor
    when one thinks it should---not even when del is used or the variable 
    holding the object is re-assigned.  The "with" statement, at the other hand,
    is safe and is guaranteed to shut down the object properly.  This is 
    particularly important when using callback functions, as only with a "with" 
    statement it is guaranteed that the event loop thread is terminated 
    properly.  If the "with" statement is not used, the close method must be
    called when the PinIO object is no longer needed.

    Pins' voltage levels are examined and set via setters and getters for the
    level property of this class, i.e. if myPin is a PinIO object via the
    statements
    @code
        value = myPin.level
    @endcode
    to examine the pin's voltage level and store it in the variable value, and
    @code
        myPin.level = value
    @endcode
    to set the voltage level of the pin to whatever the variable value contains,
    which should be of type PinIO.Level.

    The type PinIO.Level is derived from IntEnum and therefore variables of this
    type can be used interchangeably with ints, which of course should only
    assume the values 0 and 1.

    The class also provides an Open Drain mode.  In this mode, pins are only
    driven low by any device on a bus line and rely on an external resistor to
    pull the line up when no device on the bus is driving it low.  An internal 
    Raspberry Pi resistor is not enough to pull the bus line high - an external
    resistor is therefore mandatory.  Pleas assure that only one resistor is
    pulling that line high, as some devices may provide such a pullup resistor.
    Too many such pullup resistors on a single line may result in permanent
    damage to any device connected to that line, including the Raspberry Pi.
    The same holds true if the pullup resistor is chosen too small.  If you 
    don't completely understand this or don't know how to chose a proper pullup
    resistor, please don't use this mode without help from an expert.

    CAUTION: Make sure you are only using voltages at any pins that do not 
    exceed the allowed level for your device.  Otherwise, permanent damage to
    the Raspberry Pi chip may occur.
    """

    ## Mode Enum - one of INPUT, INPUT_PULLUP, INPUT_PULLDOWN, OUTPUT, and 
    ## OPEN_DRAIN
    Mode = _PinIOAPI._Mode

    ## Level Enum - one of LOW or HIGH
    Level = _PinIOAPI._Level

    ## Edge Enum, trigger edge one of FALLING, RISING, or BOTH
    Edge = _PinIOAPI._Edge

    def __init__( self, 
                  pin: Union[int, str], 
                  mode: Mode, 
                  callback: Optional[callable]=None,  # type: ignore
                  edge: Optional[Edge]=None,
                  force: Optional[bool]=False ):
        """!
        @brief Constructor - sets Pin properties, including callback
               capabilities.
        @param pin I/O header pin or GPIO line number to associate with object.
               Can be an integer header pin number or a string of the form 
               GPIO<m> on the Raspberry Pi or GP<m> on the Pico where m 
               represents the line number
        @param mode I/O mode - one of Mode.INPUT, PinIO.Mode.INPUT_PULLUP,
               PinIO.Mode.INPUT_PULLDOWN, PinIO.Mode.OUTPUT, or 
               PinIO.Mode.OPEN_DRAIN
        @param callback function for this Pin or None (default)
        @param edge edge on which to trigger the callback, one of
               PinIO.Edge.FALLING, PinIO.Edge.RISING or PinIO.Edge.BOTH - 
               defaults to None
        @param force set True to allow using pins reserved for hardware -
               defaults to False
        """
        self.__open = False
        # instantiate actor
        if isPico():
            self.__actor = \
                PinIOPico( pin, mode, callback, edge, force ) # type: ignore
        else:
            self.__actor = \
                _PinIOPi( pin, mode, callback, edge, force ) # type: ignore

        # for output modes drive "meaningful" levels and set self.__actLevel
        if self.mode == self.Mode.OUTPUT:
            self.level = self.Level.LOW # type: ignore
        elif self.mode == self.Mode.OPEN_DRAIN:
            self.level = self.Level.HIGH # type: ignore
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

        Closes the pin and terminates the event loop thread if running.
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
               up or down.  Terminates event loop thread if running.
        """
        if self.__open and self.__actor:
            self.__actor.close()
        self.__open = False
        return
        
    def toggle( self ):
        """!
        @brief toggle the pin level.
        """
        if self.__actor: self.__actor.toggle()
        return

    @property
    def pin( self ) -> Union[int,None]:
        """!
        @brief Works as read-only property to get the GPIO header pin number
        associated with this class.
        @return GPIO header pin number associated with this class (or None)
        """
        if self.__actor:
            return self.__actor.pin
        else:
            return None


    @property
    def line( self ) -> Union[int,None]:
        """!
        @brief Works as read-only property to get the GPIO line number
        associated with this class.
        @return GPIO line number associated with this class (or None)
        """
        if self.__actor:
            return self.__actor.line
        else:
            return None


    @property
    def mode( self ) -> Union[Mode,None]:
        """!
        @brief Works as read-only property to get I/O mode of that Pin as an
               int.
        @return mode PinIO.Mode.INPUT,  PinIO.Mode.INPUT_PULLUP,
                     PinIO.Mode.INPUT_PULLDOWN, PinIO.Mode.OUTPUT or 
                     PinIO.Mode.OPEN_DRAIN (or None)
        """
        if self.__actor:
            return self.__actor.mode
        else:
            return None


    @property
    def callback( self ) -> Union[str,None]:
        """!
        @brief Works as read-only property to get the name of callback function
               as a string.
        @return callback function name or empty string
        """
        if self.__actor:
            return self.__actor.callback
        else:
            return None


    @property
    def triggerEdge( self ) -> Edge:
        """!
        @brief Works as read-only property to get the callback trigger edge
               as a PinIO.Edge type.
        @return trigger edge as PinIO.Edge.FALLING, PinIO.Edge.RISING,
                PinIO.Edge.BOTH or None
        """
        return self.__actor.triggerEdge


    @property
    def level( self ) -> Union[Level,None]:
        """!
        @brief Works as read/write property to get the current voltage level
               of a Pin as a PinIO.Level type.
        @return PinIO.Level.HIGH or PinIO.Level.LOW
        """
        if self.__actor:
            return self.__actor.level
        else:
            return None


    @level.setter
    def level( self, level: Level ):
        """!
        @brief Works as the setter of a read/write property to set the Pin to a
               given voltage level.
        @param level level to set Pin to - one of PinIO.Level.HIGH and 
               PinIO.Level.LOW (1 and 0 can be used instead)
        """
        self.__actor.level = level
        return


#  main program - NO Unit Test - Unit Test is in separate file

if __name__ == "__main__":

    import sys

    def myCallback( line, level, count ):
        """!
        @brief Dud as a callback function.
        """
        return

    def main():
        """!
        @brief Main program - to save some resources, we do not include the
               Unit Test here.  In essence, this just checks the syntax.
        """
        with PinIO( 'GPIO5', PinIO.Mode.INPUT, myCallback, PinIO.Edge.RISING ) \
             as pin:
            print( pin )
        print( '\nSUCCESS: No Python syntax errors detected\n' )
        print( 'Please use included GPIO_ALUnitTest.py for complete Unit Test' )
        return 0

    sys.exit( int( main() or 0 ) )
