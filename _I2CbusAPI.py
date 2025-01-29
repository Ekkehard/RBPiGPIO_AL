# Python Implementation: _I2CbusAPI
# -*- coding: utf-8 -*-
##
# @file       _I2CbusAPI.py
#
# @version    4.0.0
#
# @par Purpose
# Provides API for all flavors of the I2C bus software.
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
# Copyright (C) 2021 - 2025 W. Ekkehard Blanz\n
# See NOTICE.md and LICENSE.md files that come with this distribution.

# File history:
#
#      Date         | Author         | Modification
#  -----------------+----------------+------------------------------------------
#   Mon Jan 27 2025 | Ekkehard Blanz | extracted from I2Cbus.py
#                   |                |
#

from typing import Union, Optional
from abc import ABC, ABCMeta, abstractmethod
from GPIO_AL.tools import argToLine
from GPIO_AL import GPIOError


class _I2CbusAPI( metaclass=ABCMeta )
    """!
    @brief Abstract base class provides API for I<sup>2</sup>C classes.
    """
    def __init__( self,
                  sdaPin: Union[int, str],
                  sclPin: Union[int, str],
                  mode: int,
                  frequency: Union[float,object],
                  attempts: int,
                  usePEC: bool ):
        """!
        @brief Constructor

        @param sdaPin GPIO pin number string or board pin number
        @param sclPin GPIO pin number string or board pin number
        @param mode one of I2Cbus.HARDWARE_MODE or I2Cbus.SOFTWARE_MODE
        @param frequency I<sup>2</sup>C frequency in Hz 
        @param attempts number of read or write attempts before throwing an
               exception
        @param usePEC set True to use Packet Error Checking
        @throws GPIOException in case of parameter error
        """
        # store our incoming parameters
        self._sdaPin = argToLine( sdaPin )
        self._sclPin = argToLine( sclPin )
        self._mode = mode
        self._usePEC = usePEC
        try:
            if str( frequency.unit ) != 'Hz':
                raise GPIOError( 'Wrong frequency object specified: {0}'
                                 .format( frequency ) )
        except AttributeError:
            pass
        self._orgFrequency = frequency
        self._frequency = float( frequency )
        self._attempts = attempts
        return
            
    @abstractmethod
    def __del__( self ):
        """!
        @brief Destructor.  To be implemented by child.
        """
        pass
        
    @abstractmethod
    def __str__( self ) > str:
        """!
        @brief String representation of this class - returns all settable
               parameters.  To be implemented by child.
        """
        pass
        
    @abstractmethod
    def close( self ):
        """!
        @brief On the Raspberry Pi, it is important to call this method to
               properly close the pigpio object in software mode.
        """
        pass

    @abstractmethod
    def readByte( self, i2cAddress: int ) -> int:
        """!
        @brief Read a single general byte from an I<sup>2</sup>C device.
        @param i2cAddress int address of I<sup>2</sup>C device to be read from
        @return int with byte read
        """
        pass

    @abstractmethod
    def readByteReg( self, i2cAddress: int, register: int ) -> int:
        """!
        @brief Read a single byte from an I<sup>2</sup>C device register.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @param register device register to read from as an int
        @return int with byte read
        """
        pass

    @abstractmethod
    def readBlockReg( self,
                      i2cAddress: int,
                      register: int,
                      length: int ) -> int:
        """!
        @brief Read a block of bytes from an I<sup>2</sup>C device register.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @param register device register to start reading
        @param length number of bytes to be read
        @return list of ints with bytes read
        """
        pass

    @abstractmethod
    def writeQuick( self, i2cAddress: int ):
        """!
        @brief Issue an I<sup>2</sup>C  device address with the write bit set
        and check the acknowledge signal but do not write anything else.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        """
        pass

    @abstractmethod
    def writeByte( self, i2cAddress: int, value: int ):
        """!
        @brief Write a single byte to an I<sup>2</sup>C device.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param value value of byte to be written as an int
        """
        pass

    @abstractmethod
    def writeByteReg( self, i2cAddress: int, register: int, value: int ):
        """!
        @brief Write a single byte to an I<sup>2</sup>C device register.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param register device register to start reading
        @param value value of byte to be written as an int
        """
        pass

    @abstractmethod
    def writeBlockReg( self, i2cAddress: int, register: int, block: int ):
        """!
        @brief Write a block of bytes to an I<sup>2</sup>C device starting at
               register.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param register device register to start reading
        @param block list of ints with bytes to be written
        """
        pass

