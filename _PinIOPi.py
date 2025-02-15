# Python Implementation: _PinIOPi
##
# @file       _PinIOPi.py
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
# Copyright (C) 2021 - 2025 W. Ekkehard Blanz\n
# See NOTICE.md and LICENSE.md files that come with this distribution.

# File history:
#
#      Date         | Author         | Modification
#  -----------------+----------------+------------------------------------------
#   Sun Feb 02 2025 | Ekkehard Blanz | extracted from PinIO.py
#                   |                |

import os
import gpiod
if int( gpiod.__version__.split( '.' )[0] ) < 2 or \
    (int( gpiod.__version__.split( '.' )[0] ) > 1 and \
    int( gpiod.__version__.split( '.' )[1] ) < 2):
    raise ValueError( 'GPIO_AL requires gpiod version 2.2 or higher' )
from gpiod.line import Direction, Drive, Value, Bias
from GPIO_AL.GPIOError import GPIOError
from GPIO_AL._PinIOAPI import _PinIOAPI
from GPIO_AL.tools import gpioChipPath


class _PinIOPi( _PinIOAPI ):
    """!
    """
    def __init__( self, 
                  pin, 
                  mode, 
                  callback=None, 
                  edge=None,
                  force=False ):
        """!
        @brief Constructor.
        @param pin I/O header pin number or GPIO line
        @param mode I/O mode
        @param callback function for this Pin or None (default)
        @param edge edge on which to trigger the callback or None
        @param force set True to allow using pins reserved for hardware
        """

        super().__init__( pin, mode, callback, edge, force )

        self.__pinObj = None
        self.__terminateFd = None
        self.__eventThread = None

        if self._mode == self._Mode.INPUT:
            # normal input operation
            config={self._line:
                        gpiod.LineSettings( direction=Direction.INPUT,
                                            active_low=False,
                                            bias=Bias.AS_IS )}
        elif self._mode == self._Mode.INPUT_PULLUP:
            config={self._line: 
                        gpiod.LineSettings( direction=Direction.INPUT,
                                            active_low=False,
                                            bias=Bias.PULL_UP )}
        elif self._mode == self._Mode.INPUT_PULLDOWN:
            config={self._line: 
                        gpiod.LineSettings( direction=Direction.INPUT,
                                            active_low=False,
                                            bias=Bias.PULL_DOWN )}
        elif self._mode == self._Mode.OUTPUT:
            config = {self._line:
                            gpiod.LineSettings( direction=Direction.OUTPUT,
                                                active_low=False,
                                                drive=Drive.PUSH_PULL )}
        elif self._mode == self._Mode.OPEN_DRAIN:
            config = {self._line:
                            gpiod.LineSettings( direction=Direction.OUTPUT,
                                                active_low=False,
                                                drive=Drive.OPEN_DRAIN )}
        else:
            raise GPIOError( 'Internal error - wrong mode: {0}'.format( mode ) )

        if self._clbk is not None:
            config[self._line].edge_detection = self._triggerEdge

        # in gpiod we use a LineRequest object as the pinObject
        self.__pinObj = gpiod.request_lines( gpioChipPath( self._line ),
                                             consumer='GPIO_AL',
                                             config=config )
        if self._clbk is not None:
            import threading
            self.__terminateFd = os.eventfd( 0 )
            self.__eventThread = threading.Thread( target=self.__waitEventLoop )
            self.__eventThread.start()

        if self._mode.value >= self._Mode.OPEN_DRAIN.value: # type: ignore
            self.level = self._Level.HIGH
        self._open = True

        return

    def __waitEventLoop( self ):
        """!
        @brief Main GPIO-event loop to be run in a separate thread.

        Uses poll to wait for events on GPIO pins and calls caller-supplied 
        functions or methods when those events occur.  Also waits for an event
        on the doneFd file descriptor, as those will terminate the event loop.
        """
        import select
        eventToLevel = {gpiod.EdgeEvent.Type.FALLING_EDGE: self._Level.LOW,
                        gpiod.EdgeEvent.Type.RISING_EDGE: self._Level.HIGH}
        poll = select.poll()
        poll.register( self.__pinObj.fd, select.POLLIN ) # type: ignore
        poll.register( self.__terminateFd, select.POLLIN ) # type: ignore
        done = False
        while not done:
            for fd, _ in poll.poll():
                if fd == self.__terminateFd:
                    # handle done event
                    done = True
                    # break out of fore loop - do not complete event list
                    break
                else:
                    # handle all edge events that caused an interrupt
                    for event in self.__pinObj.read_edge_events(): # type: ignore
                        self._clbk( self ) # type: ignore
        return

    def __del__( self ):
        """!
        @brief Destructor.
        """
        self.close()
        return

    def close( self ):
        """!
        @brief Close a pin on Raspberry Pi, close event loop thread if running, 
               and set pin to input.
        """
        if self._open:
            if self._clbk is not None and self.__eventThread is not None:
                if self.__eventThread.is_alive():
                    os.eventfd_write( self.__terminateFd, 1 ) # type: ignore
                    self.__eventThread.join()
                os.close( self.__terminateFd ) # type: ignore
            # switch to INPUT no pullup or pulldown
            self.__pinObj.reconfigure_lines( config={self._line: # type: ignore
                        gpiod.LineSettings( direction=gpiod.line.Direction.INPUT,
                                            active_low=False,
                                            bias=gpiod.line.Bias.PULL_DOWN )} )
            self.__pinObj.reconfigure_lines( config={self._line: # type: ignore
                        gpiod.LineSettings( direction=gpiod.line.Direction.INPUT,
                                            active_low=False,
                                            bias=gpiod.line.Bias.AS_IS )} )
            self.__pinObj.release() # type: ignore
        self._open = False
        return
        
    def toggle( self ):
        """!
        @brief toggle the pin level.
        """
        self.level = 1 - self.__actLevel
        return

    @property
    def level( self ): # type: ignore
        """!
        @brief Works as read/write property to get the current voltage level
               of a Pin as a PinIO.Level type.
        @return PinIO.Level.HIGH or PinIO.Level.LOW
        """
        if self._mode == self._Mode.OUTPUT:
            raise GPIOError( 'cannot read from output pins' )
        if self.__pinObj.get_value( self._line ) == Value.INACTIVE: # type: ignore
            return self._Level.LOW
        else:
            return self._Level.HIGH

    @level.setter
    def level( self, level ):
        """!
        @brief Works as the setter of a read/write property to set the Pin to a
               given voltage level.
        @param level level to set Pin to - one of PinIO.Level.HIGH and 
               PinIO.Level.LOW (1 and 0 can be used instead)
        """
        if self._mode.value < self._Mode.OUTPUT.value: # type: ignore
            raise GPIOError( 'cannot write to input pins' )
        if level == self._Level.LOW:
            value = Value.INACTIVE
        else:
            value = Value.ACTIVE
        self.__pinObj.set_value( self._line, value ) # type: ignore
        self.__actLevel = level
        return