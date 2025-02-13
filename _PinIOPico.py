# Python Implementation: _PinIOPico
##
# @file       _PinIOPico.py
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
#                   |                |

import machine
from GPIO_AL.GPIOError import GPIOError
from GPIO_AL._PinIOAPI import _PinIOAPI


class _PinIOPico( _PinIOAPI ):
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

        pull = None
        if self._mode == self._Mode.INPUT:
            mode = machine.Pin.IN
        elif self._mode == self._Mode.INPUT_PULLUP:
            mode = machine.Pin.IN
            pull = machine.Pin.PULL_UP
        elif self._mode == self._Mode.INPUT_PULLDOWN:
            mode = machine.Pin.IN
            pull = machine.Pin.PULL_DOWN
        elif self._mode == self._Mode.OUTPUT:
            mode = machine.Pin.OUT
        elif self._mode == self._Mode.OPEN_DRAIN:
            mode = machine.Pin.OPEN_DRAIN
            pull = machine.Pin.PULL_UP
        else:
            raise GPIOError( 'Internal error' )
        self.__pinObj = machine.Pin( self._line, mode, pull )

        if self._triggerEdge == self._Edge.BOTH:
            # TODO figure out a way to do that
            raise GPIOError( 'Trigger on changing signal not yet implemented' )

        if self._clbk is not None:
            self.__pinObj.irq( self._clbk, self._triggerEdge )

        return

    def __del__( self ):
        """!
        @brief Destructor.
        """
        self.close()
        return

    def close( self ):
        """!
        @brief Close the Pin - set it to input (high impedance) without pulling
               up or down.  Terminates event loop thread if running.
        """
        self.__pinObj.init( self._line, machine.Pin.IN )
        return
        
    def toggle( self ):
        """!
        @brief toggle the pin level.
        """
        self.level = 1 - self.__actLevel
        return

    @property
    def level( self ):
        """!
        @brief Works as read/write property to get the current voltage level
               of a Pin as a PinIO.Level type.
        @return PinIO.Level.HIGH or PinIO.Level.LOW
        """
        if self._mode == self._Mode.OUTPUT:
            raise GPIOError( 'cannot read from output pins' )
        return self.__pinObj.value()

    @level.setter
    def level( self, level ):
        """!
        @brief Works as the setter of a read/write property to set the Pin to a
               given voltage level.
        @param level level to set Pin to - one of PinIO.Level.HIGH and 
               PinIO.Level.LOW (1 and 0 can be used instead)
        """
        if self._mode < self._Mode.OUTPUT:
            raise GPIOError( 'cannot write to input pins' )
        self.__pinObj.value( level )
        self.__actLevel = level
        return
