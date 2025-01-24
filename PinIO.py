# Python Implementation: GPIO_AL
##
# @file       GPIO_AL.py
#
# @mainpage   Raspberry Pi GPIO Abstraction Layer
#
# @version    4.0.0
#
# @par Purpose
# This module provides an abstraction layer for the Raspberry Pi General Purpose
# I/O (GPIO) single Opin I/O functionality for all models of the regular 
# Raspberry Pi 0 and up Raspberry Pi 5, as well as the Raspberry Pi Pico
#
# This code has been tested on a Raspberry Pi 0, 3, 4 and 5 and a Raspberry Pi 
# Pico.
#
# @par Comments
# This is Python 3 code!  PEP 8 guidelines are decidedly NOT followed in some
# instances, and guidelines provided by "Coding Style Guidelines" a "Process
# Guidelines" document from WEB Design are used instead where the two differ,
# as the latter span several programming languages and are therefore applicable
# also for projects that require more than one programming language; it also
# provides consistency across hundreds of thousands of lines of legacy code.
# Doing so, ironically, is following PEP 8, which speaks highly of the wisdom of
# the authors of PEP 8.
#
# @par Known Bugs
# None
#
# @author
# W. Ekkehard Blanz <Ekkehard.Blanz@gmail.com>
#
# @copyright
# Copyright (C) 2021 - 2024 W. Ekkehard Blanz\n
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
#                   |                |
#

from typing import Union, Optional
from enum import Enum, IntEnum
import time
import threading
import os

from GPIO_AL.tools import argToLine, argToPin, isHWpulsePin, isPico, \
                          gpioChipPath

# determine platform and import appropriate module for GPIO access
if isPico():
    import machine
else:
    # the following data and functions are not needed for the Raspberry Pi Pico
    import gpiod
    if int( gpiod.__version__.split( '.' )[0] ) < 2 or \
       (int( gpiod.__version__.split( '.' )[0] ) > 1 and \
        int( gpiod.__version__.split( '.' )[1] ) < 2):
        raise ValueError( 'GPIO_AL requires gpiod version 2.2 or higher' )



class PinIO():
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
        def myCallback( pin, level=None, tick=None ):
            ...
            return
    @endcode
    to work on all Raspberry Pi architectures.  Here pin is the pin (not line or
    offset) number, level is of type PinIO.Level, and tick is the number of the
    event.

    NOTE: It is strongly recommended to instantiate this class using a "with"
    statment.  Otherwise it cannot be guaranteed that the destructor of the 
    class will be called as the Python interpreter will not call the destructur
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

    CAUTION: Make sure you are not using voltages at any pins that exceed the
    allowed level for your device.  Otherwise, permanent destruction of the
    Raspberry Pi chip may result.
    """

    class Mode( Enum ):
        ## Input mode without resistors pulling up or down
        INPUT = 0
        ## Input mode with pullup resistor
        INPUT_PULLUP = 1
        ## Input mode with pulldown resistor
        INPUT_PULLDOWN = 2
        ## Regular output mode
        OUTPUT = 3
        ## Open drain mode - implemented in software on hardware that does not
        ## support it
        OPEN_DRAIN = 4

    class Level( IntEnum ):
        ## Low voltage level
        LOW = 0
        ## High voltage level
        HIGH = 1

    if isPico():
        class Edge( Enum ):
            ## Trigger on falling edge
            FALLING = machine.Pin.IRQ_FALLING
            ## Trigger on rising edge
            RISING = machine.Pin.IRQ_RISING
            ## Trigger on changing signal i.e. both edges
            BOTH = machine.Pin.IRQ_FALLING | machine.Pin.IRQ_RISING
    else:
        Edge = gpiod.line.Edge

    def __init__( self, 
                  pin: Union[int, str], 
                  mode: Mode, 
                  callback: Optional[callable]=None, 
                  edge: Optional[Edge]=None,
                  force: Optional[bool]=False ):
        """!
        @brief Constructor - sets Pin properties, including callback
               capabilities.
        @param pin I/O header pin or GPIO line number to associate with object
               Can be an integer pin number or a string of the form GPIO<m>
               where m represents the GPIO line number
        @param mode I/O mode - one of MOde.INPUT, PinIO.Mode.INPUT_PULLUP,
               PinIO.Mode.INPUT_PULLDOWN, PinIO.Mode.OUTPUT, or 
               PinIO.Mode.OPEN_DRAIN
        @param callback function for this Pin or None (default)
        @param edge edge on which to trigger the callback, one of
               PinIO.Edge.FALLING, PinIO.Edge.RISING or PinIO.Edge.BOTH - 
               defaults to None
        @param force set True to allow using reserved (for hardware) pins
        """
        if not isinstance( mode, self.Mode ):
            raise GPIOError( 'Wrong I/O mode specified: {0}'.format( mode ) )
        self.__mode = mode
        if callback is not None and not callable( callback ):
            raise GPIOError( 'Wrong callback funtion specified' )
        self.__clbk = callback
        if edge is not None and not isinstance( edge, self.Edge ):
            raise GPIOError( 'Wrong triggerEdge specified: '
                             '{0}'.format( edge ) )
        if (callback is not None and edge is None) or \
           (callback is None and edge is not None):
            raise GPIOError( 'Either both callback and edge must be specified '
                             'or none of them' )
        self.__triggerEdge = edge

        # set to False in case the setup methods throw an exception
        self.__open = False

        self.__pinObj = None    # will be set by setup methods
        if isHWpulsePin( pin ) and not force:
            raise GPIOError( 'Hardware PWM pin {0} not allowed without force'
                             .format( pin ))

        if self.__mode != self.Mode.OUTPUT and \
           self.__mode != self.Mode.OPEN_DRAIN:
            self.__set = (lambda _level: self.__error( 'Cannot set level on '
                                                       'input Pins' ) )
        elif self.__mode == self.Mode.OUTPUT:
            # consider returning self.__actLevel
            self.__level = (lambda : self.__error( 'Cannot read level from '
                                                   'output Pins' ) )

        # initialize host-specific libraries and hardware
        if isPico():
            self.__setupRPPico( pin )
        else:
            self.__setupRP( pin )

        # after everything went well, we declare the GPIO pin open
        self.__open = True

        if self.__mode == self.Mode.OUTPUT or \
           self.__mode == self.Mode.OPEN_DRAIN:
            self.__set( self.Level.HIGH )

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

        Closes the pin and terminates the event loop thread if running.
        @param excType type of exception ending the context
        @param excValue value of the exception ending the context
        @param excTraceback traceback of excweption ending the context
        @return False (will re-raise the exception)
        """
        self.close()
        return False


    def __str__( self ):
        """!
        @brief String representation of this class - returns all settable
               parameters.
        """
        if self.triggerEdge is not None:
            triggerEdge = self.triggerEdge
        else:
            triggerEdge = 'None'
        return 'pin: {0}, line: GPIO{1}, mode: {2}, callback: {3}, edge: {4}' \
               .format( self.pin,
                        self.line,
                        self.mode,
                        self.callback,
                        triggerEdge )


    def __error( self, text ):
        """!
        @brief Private method that throws an exception.

        Raising an exception alone is a statement - not an expression - in a
        lambda function we need an expression, and this is it.
        @param text string of text to throw GPIOError exception with
        """
        raise GPIOError( text )


    def __setupRP( self, pin ):
        """!
        @brief Private method to set up hardware of the Raspberry Pi as well as
        lambda functions to read from and write to single I/O Pins.
        """
        from gpiod.line import Direction, Drive, Value, Bias, Edge

        self.__line = argToLine( pin )
        self.__pin = argToPin( pin )

        if self.__mode.value < self.Mode.OUTPUT.value:
            if self.__mode == self.Mode.INPUT_PULLUP:
                config={self.__line: 
                            gpiod.LineSettings( direction=Direction.INPUT,
                                                active_low=False,
                                                bias=Bias.PULL_UP )}
            elif self.__mode == self.Mode.INPUT_PULLDOWN:
                config={self.__line: 
                            gpiod.LineSettings( direction=Direction.INPUT,
                                                active_low=False,
                                                bias=Bias.PULL_DOWN )}
            else:
                # normal input operation
                config={self.__line:
                            gpiod.LineSettings( direction=Direction.INPUT,
                                                active_low=False,
                                                bias=Bias.AS_IS )}
            self.__level = (lambda: 
                self.Level.LOW 
                    if self.__pinObj.get_value( self.__line ) == Value.INACTIVE
                    else self.Level.HIGH)
        else:
            self.__makeLevel = (lambda level: Value.INACTIVE if level == 0
                                                             else Value.ACTIVE)
            if self.__mode == self.Mode.OUTPUT:
                self.__set = (lambda level: self.__setRBP( level ) )
                config = {self.__line:
                             gpiod.LineSettings( direction=Direction.OUTPUT,
                                                 active_low=False,
                                                 drive=Drive.PUSH_PULL )}
            else: # do we still need the software simulation?
                self.__set = (lambda level: self.__setRBP( level ) )
                
                self.__level = (lambda: 
                           self.Level.LOW 
                           if 
                               self.__pinObj.get_value( self.__line ) == 
                               Value.INACTIVE
                            else self.Level.HIGH)
                config = {self.__line:
                             gpiod.LineSettings( direction=Direction.OUTPUT,
                                                 active_low=False,
                                                 drive=Drive.OPEN_DRAIN )}

        if self.__clbk is not None:
            config[self.__line].edge_detection = self.__triggerEdge

        # in gpiod we use a LineRequest object as the pinObject
        self.__pinObj = gpiod.request_lines( gpioChipPath( self.__line ),
                                             consumer='GPIO_AL',
                                             config=config )
        self.__close = self.__closeRP

        if self.__clbk is not None:
            import threading
            self.__terminateFd = os.eventfd( 0 )
            self.__eventThread = threading.Thread( target=self.__waitEventLoop )
            self.__eventThread.start()
        else:
            self.__terminateFd = None
            self.__eventThread = None
        return

    def __closeRP( self ):
        """!
        @brief Close a pin on Raspberry Pi, close event loop thread if running, 
               and set pin to input.
        """
        if self.__clbk is not None:
            if self.__eventThread.is_alive():
                os.eventfd_write( self.__terminateFd, 1 )
                self.__eventThread.join()
            os.close( self.__terminateFd )
        # switch to INPUT no pullup or pulldown
        self.__pinObj.reconfigure_lines( config={self.__line:
                       gpiod.LineSettings( direction=gpiod.line.Direction.INPUT,
                                           active_low=False,
                                           bias=gpiod.line.Bias.AS_IS )} )
        self.__pinObj.release()
        return


    def __waitEventLoop( self ):
        """!
        @brief Main GPIO-event loop to be run in a separate thread.

        Uses poll to wait for events on GPIO pins and calls caller-supplied 
        functions or methods when those events occur.  Also waits for an event
        on the doneFd file descriptor, which will terminate the event loop.
        """
        import select
        eventToLevel = {gpiod.EdgeEvent.Type.FALLING_EDGE: self.Level.LOW,
                        gpiod.EdgeEvent.Type.RISING_EDGE: self.Level.HIGH}
        poll = select.poll()
        poll.register( self.__pinObj.fd, select.POLLIN )
        poll.register( self.__terminateFd, select.POLLIN )
        done = False
        while not done:
            for fd, _ in poll.poll():
                if fd == self.__terminateFd:
                    # handle done event
                    done = True
                    break
                else:
                    # handle any edge events
                    for event in self.__pinObj.read_edge_events():
                        self.__clbk( self.pin, 
                                     eventToLevel[event.event_type], 
                                     event.line_seqno )
        return


    def __setupRPPico( self, pin ):
        """!
        @brief Private method to set up hardware of the Raspberry Pi Pico as
        well as lambda functions to read from and write to single I/O Pins.
        """
        self.__pin = pin
        pull = None
        if self.__mode == self.INPUT:
            mode = machine.Pin.IN
        elif self.__mode == self.INPUT_PULLUP:
            mode = machine.Pin.IN
            pull = machine.Pin.PULL_UP
        elif self.__mode == self.INPUT_PULLDOWN:
            mode = machine.Pin.IN
            pull = machine.Pin.PULL_DOWN
        elif self.__mode == self.OUTPUT:
            mode = machine.Pin.OUT
        elif self.__mode == self.OPEN_DRAIN:
            mode = machine.Pin.OPEN_DRAIN
            pull = machine.Pin.PULL_UP
        else:
            raise GPIOError( 'Internal error' )
        self.__pinObj = machine.Pin( pin, mode, pull )

        self.__close = (lambda:
                        self.__pinObj.init( pin, machine.Pin.IN ))

        if self.__mode == self.Mode.OUTPUT or \
           self.__mode == self.Mode.OPEN_DRAIN:
            self.__set = (lambda level: self.__setRBPPico( level ) )

        if self.__mode != self.Mode.OUTPUT:
            self.__level = (lambda: self.__pinObj.value())

        if self.__clbk is not None:
            self.__pinObj.irq( self.__clbk, triggerEdge )

        return


    def __softwareOpenDrainSet( self, level ):
        """!
        @brief Private method to simulate an open drain circuit on a Raspberry
               Pi that doesn't offer hardware support for it.
        @param level level to set Pin to - one of PinIO.Level.HIGH or 
                     PinIO.Level.LOW
        """
        if level == self.HIGH:
            # output is never driven high - just pulled up in input mode
            self.__pinObj.set_mode( self.__pin, pigpio.INPUT )
            self.__pinObj.set_pull_up_down( self.__pin, pigpio.PUD_UP )
        else:
            # output is actively driven low
            self.__pinObj.set_mode( self.__pin, pigpio.OUTPUT )
            self.__pinObj.write( self.__pin, level )

        return


    def close( self ):
        """!
        @brief Close the Pin - set it to input (high impedance) without pulling
               up or down.  Terminates event loop thread if running.
        """
        if self.__open:
            self.__close()
            self.__open = False
        return


    def __setRBP( self, level ):
        """!
        @brief set the pin level.
        """
        self.__pinObj.set_value( self.__line, self.__makeLevel( level ) )
        self.__actLevel = level
        return
        
        
    def __setRBPPico( self, level ):
        self.__pinObj.value( level )
        self.__actLevel = level
        return
        
        
    def toggle( self ):
        """!
        @brief toggle the pin level.
        """
        self.__set( 1 - self.__actLevel )
        return

    @property
    def pin( self ):
        """!
        @brief Works as read-only property to get the GPIO pin number
        associated with this class.
        @return GPIO header pin number associated with this class
        """
        return self.__pin


    @property
    def line( self ):
        """!
        @brief Works as read-only property to get the GPIO line number
        associated with this class.
        @return GPIO line number associated with this class
        """
        return self.__line


    @property
    def mode( self ):
        """!
        @brief Works as read-only property to get I/O mode of that Pin as an
               int.
        @return mode PinIO.Mode.INPUT,  PinIO.Mode.INPUT_PULLUP,
                     PinIO.Mode.INPUT_PULLDOWN, PinIO.Mode.OUTPUT or 
                     PinIO.Mode.OPEN_DRAIN
        """
        return self.__mode


    @property
    def callback( self ):
        """!
        @brief Works as read-only property to get the name of callback function
               as a string.
        @return callback function name or emtpy string
        """
        if self.__clbk is not None:
            return self.__clbk.__name__
        else:
            return 'None'


    @property
    def triggerEdge( self ):
        """!
        @brief Works as read-only property to get the callback trigger edge
               as a PinIO.Edge type.
        @return trigger edge as PinIO.Edge.FALLING, PinIO.Edge.RISING or None
        """
        return self.__triggerEdge


    @property
    def level( self ):
        """!
        @brief Works as read/write property to get the current voltage level
               of a Pin as a PinIO.Level type.
        @return PinIO.Level.HIGH or PinIO.Level.LOW
        """
        # The dud self.__level() will be overridden by setup methods.
        return self.__level()


    @level.setter
    def level( self, level ):
        """!
        @brief Works as the setter of a read/write property to set the Pin to a
               given voltage level.
        @param level level to set Pin to - one of PinIO.Level.HIGH and 
               PinIO.Level.LOW (1 and 0 can be used instead)
        """
        # The dud self.__set() will be overridden by setup methods.
        self.__set( level )
        return


#  main program - NO Unit Test - Unit Test is in separate file

if __name__ == "__main__":

    import sys

    def myCallback( pin, level, count ):
        return

    def main():
        """!
        @brief Main program - to save some resources, we do not include the
               Unit Test here.  In essence, this just checks the syntax.
        """
        with PinIO( 'GPIO5', PinIO.Mode.INPUT, myCallback, PinIO.Edge.RISING ) \
             as pin:
            print( 'pin: {0}'.format( pin ) )
        print( 'Please use included GPIO_ALUnitTest.py for complete Unit Test' )
        return 0

    sys.exit( int( main() or 0 ) )
