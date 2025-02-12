# Python Implementation: _PinIOAPI
##
# @file       _PinIOAPI.py
#
# @version    2.0.0
#
# @par Purpose
# Provide a common API for general pin I/O.
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
#   Sat Feb 01 2025 | Ekkehard Blanz | extracted from Pulse.py
#                   |                |

from abc import ABC, ABCMeta, abstractmethod
from GPIO_AL.GPIOError import GPIOError
from GPIO_AL.tools import isPico, argToPin, argToLine, lineToStr, isHWpulsePin

if isPico():
    Enum = object
    IntEnum = object
else:
    from enum import Enum, IntEnum
    from typing import Union, Optional

    
class _PinIOAPI( metaclass=ABCMeta ):
    """!
    @brief Abstract base class provides API for pin I/O classes.
    """

    # Enums are provided in the API so children have them.
    # They are copied to the main class so clients have easy access to them.

    ## Pin operation mode as an Enum
    class _Mode( Enum ):
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

    ## Signal level as an IntEnum
    class _Level( IntEnum ):
        ## Low voltage level
        LOW = 0
        ## High voltage level
        HIGH = 1

    if isPico():
        import machine
        ## Trigger edge as an Enum
        class _Edge( IntEnum ):
            ## Trigger on falling edge
            FALLING = machine.Pin.IRQ_FALLING
            ## Trigger on rising edge
            RISING = machine.Pin.IRQ_RISING
            ## Trigger on both edges whenever signal changes
            BOTH = machine.Pin.IRQ_FALLING | machine.Pin.IRQ_RISING
    else:
        import gpiod
        ## Get trigger edge Enum directly from gpiod
        _Edge = gpiod.line.Edge

    def __init__( self, 
                  pin: Union[int, str], 
                  mode: _Mode, 
                  callback: Optional[callable]=None, 
                  edge: Optional[_Edge]=None,
                  force: Optional[bool]=False ):
        """!
        @brief Constructor.
        @param pin I/O header pin or GPIO line number
        @param mode I/O mode
        @param callback function for this Pin or None (default)
        @param edge edge on which to trigger the callback 
               defaults to None
        @param force set True to allow using pins reserved for hardware
        """

        self._open = False

        if not isinstance( mode, self._Mode ):
            raise GPIOError( 'Wrong I/O mode specified: {0}'.format( mode ) )
        self._mode = mode
        if callback is not None and not callable( callback ):
            raise GPIOError( 'Wrong callback function specified'
                             '{0}'.format( callback ) )
        self._clbk = callback
        if edge is not None and not isinstance( edge, self._Edge ):
            raise GPIOError( 'Wrong triggerEdge specified: '
                             '{0}'.format( edge ) )
        if (callback is not None and edge is None) or \
           (callback is None and edge is not None):
            raise GPIOError( 'Either both callback and edge must be specified '
                             'or none of them' )
        self._triggerEdge = edge

        if isHWpulsePin( pin ) and not force and not isPico():
            raise GPIOError( 'Using hardware PWM pin {0} for pin I/O is not '
                             'allowed on RB Pi without force'.format( pin ))

        self._line = argToLine( pin )
        self._pin = argToPin( pin )

        return
            
    @abstractmethod
    def __del__( self ):
        """!
        @brief Destructor.  To be implemented by child.
        """
        pass
        
    def __str__( self ) -> str:
        """!
        @brief String representation of this class - returns all settable
               parameters.  Can be overwritten by child.
        """
        if self._triggerEdge is not None:
            triggerEdge = str( self._triggerEdge ).replace( '_', '' )
        else:
            triggerEdge = 'None'
        return 'header pin: {0}, line: {1}, mode: {2}, callback: {3}, edge: {4}' \
               .format( self._pin,
                        lineToStr( self._line ),
                        str( self._mode ).replace( '_', '' ),
                        self.callback,
                        triggerEdge )
            
    @abstractmethod
    def close( self ):
        """!
        @brief Close the Pin - set it to input (high impedance) without pulling
               up or down.  Terminates event loop thread if running.
        """
        pass
        
    @abstractmethod
    def toggle( self ):
        """!
        @brief toggle the pin level.
        """
        pass

    @property
    def pin( self ) -> int:
        """!
        @brief Works as read-only property to get the GPIO header pin number
        associated with this class.
        @return GPIO header pin number associated with this class
        """
        return self._pin

    @property
    def line( self ) -> int:
        """!
        @brief Works as read-only property to get the GPIO line number
        associated with this class.
        @return GPIO line number associated with this class
        """
        return self._line

    @property
    def mode( self ) -> _Mode:
        """!
        @brief Works as read-only property to get I/O mode of that Pin as an
               int.
        @return mode PinIO.Mode.INPUT,  PinIO.Mode.INPUT_PULLUP,
                     PinIO.Mode.INPUT_PULLDOWN, PinIO.Mode.OUTPUT or 
                     PinIO.Mode.OPEN_DRAIN
        """
        return self._mode

    @property
    def callback( self ) -> str:
        """!
        @brief Works as read-only property to get the name of callback function
               as a string.
        @return callback function name or empty string
        """
        if self._clbk is not None:
            return self._clbk.__name__
        else:
            return 'None'

    @property
    def triggerEdge( self ) -> _Edge:
        """!
        @brief Works as read-only property to get the callback trigger edge
               as a PinIO.Edge type.
        @return trigger edge as PinIO.Edge.FALLING, PinIO.Edge.RISING,
                PinIO.Edge.BOTH or None
        """
        return self._triggerEdge

    @property
    @abstractmethod
    def level( self ) -> _Level:
        """!
        @brief Works as read/write property to get the current voltage level
               of a Pin as a PinIO.Level type.
        @return PinIO.Level.HIGH or PinIO.Level.LOW
        """
        pass

    @level.setter
    @abstractmethod
    def level( self, level: _Level ):
        """!
        @brief Works as the setter of a read/write property to set the Pin to a
               given voltage level.
        @param level level to set Pin to - one of PinIO.Level.HIGH and 
               PinIO.Level.LOW (1 and 0 can be used instead)
        """
        pass