# Python Implementation: _AnalogInputAPI
##
# @file       _AnalogInputAPI.py
#
# @version    2.0.0
#
# @par Purpose
# Provide a common API for analog input.
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
# Copyright (C) 2025 W. Ekkehard Blanz\n
# See NOTICE.md and LICENSE.md files that come with this distribution.

# File history:
#
#      Date         | Author         | Modification
#  -----------------+----------------+------------------------------------------
#   Tue Mar 18 2025 | Ekkehard Blanz | extracted from Pulse.py
#                   |                |

from GPIO_AL.tools import isPico

if isPico():
    class ABC:
        pass
    def abstractmethod( funcobj ):
        """!
        @brief Decorator to mark abstract methods.
        """
        return funcobj
    # MicroPython silently ignores type hints without the need to import typing
else:
    from abc import ABC, abstractmethod # type: ignore

    
class _AnalogInputAPI( ABC ):
    """!
    @brief Abstract base class provides API for pin I/O classes.
    """

    # Enums are provided in the API so children have them.
    # They are copied to the main class so clients have easy access to them.

    @abstractmethod
    def __init__( self, *args, **kwargs ):
        """!
        @brief Constructor.
        @param parameters depend on the RB Pi architecture and are different
               for the Raspberry Pi and the Raspberry Pi Pico.
        """
        pass
            
    @abstractmethod
    def __del__( self ):
        """!
        @brief Destructor.
        """
        pass
            
    @abstractmethod
    def __str__( self ) -> str:
        """!
        @brief String representation of this class - returns all settable
               parameters.  Can be overwritten by child.
        """
        return ''
            
    @abstractmethod
    def close( self ):
        """!
        @brief Close the Pin - set it to input (high impedance) without pulling
               up or down.
        """
        pass

    @property
    @abstractmethod
    def level( self ) -> int:
        """!
        @brief Works as read property to get the current voltage level at the
               analog input pin or ADC chip.
        @return int representing the voltage level at given analog input
        """
        return 0

    @property
    @abstractmethod
    def maxLevel( self ) -> int:
        """!
        @brief Works as read property to get the maximal value that the level
               property can return.
               analog input.
        @return max value that level can return
        """
        return 0