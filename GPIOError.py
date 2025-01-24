# Python Implementation: GPIOError
##
# @file       GPIOError.py
#
# @mainpage   Raspberry Pi GPIO Error Exception
#
# @version    4.0.0
#
# @par Purpose
# This module providesthe exception to be thrown by modules of this package.
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
# Doing so, ironically, is following PEP 8 which speaks highly of the wisdom of
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
#   Sat Dec 14 2024 | Ekkehard Blanz | extracted from GPIO_AL.py
#                   |                |
#

from typing import Union, Optional
from enum import Enum, IntEnum
import time
import threading
import os

# first define our exception class
# (ValueError will be thrown if this import did not complete)
class GPIOError( Exception ):
    """!
    @brief Exception class to be thrown by the GPIO_AL module, or modules that
           use it.

    The class only has a constructor, a __str__ method, which produces the
    string with which it was instantiated, and a severity property, which 
    returns the severity with which it was instantiated.
    """

    class Severity( Enum ):
        """!
        @brief Severity Enum, consists of
            WARNING - Warning only
            ERROR - Regular error
            FATAL - Fatal error from which one cannot recover
        """
        WARNING = 0
        ERROR = 1
        FATAL = 2

    def __init__( self, 
                  value: str, 
                  severity: Optional[Severity]=Severity.ERROR ):
        """!
        @brief Constructor - accepts and internally stores error message as well
               as a severity of the error.
        @param value error message for this instance
        @param severity member of GPIOErr.Severity
        """
        self.__value = value
        self.__severity = severity


    def __str__( self ):
        """!
        @brief Serialize the error message.
        """
        return str( '{0}: {1}'.format( self.__severity, self.__value ) )


    @property
    def severity( self ):
        """!
        @brief Works as a property to obtain severity of the error that caused
               the exception.
        """
        return self.__severity
