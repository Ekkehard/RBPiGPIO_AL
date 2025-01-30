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

from enum import Enum
from typing import Union, Optional
from abc import ABC, ABCMeta, abstractmethod
from GPIO_AL.tools import argToLine
from GPIO_AL.GPIOError import GPIOError


class _I2CbusAPI( metaclass=ABCMeta ):
    """!
    @brief Abstract base class provides API for I<sup>2</sup>C classes.
    """

    class _Mode( Enum ):
        ## Operate I<sup>2</sup>C bus in hardware mode
        HARDWARE = 0
        ## Operate I<sup>2</sup>C bus in software (bit banging) mode
        SOFTWARE = 1

    def __init__( self,
                  sdaPin: Union[int, str],
                  sclPin: Union[int, str],
                  mode: _Mode,
                  frequency: Union[float,object],
                  attempts: int,
                  usePEC: bool ):
        """!
        @brief Constructor
        @param sdaPin header pin or GPIO line number for I<sup>2</sup>C data 
               (default GPIO2 on Raspberry Pi and 8 on Raspberry Pi Pico).
               Ints are interpreted as header pin numbers, strings starting with
               GPIO as line numbers.
        @param sclPin header pin or GPIO line number for I<sup>2</sup>C clock 
               (default GPIO3 on Raspberry Pi and 9 on Raspberry Pi Pico).
               Ints are interpreted as header pin numbers, strings starting with
               GPIO as line numbers.
        @param mode one of I2Cbus.Mode.HARDWARE or I2Cbus.Mode.SOFTWARE
        @param frequency I<sup>2</sup>C frequency in Hz (default 75 kHz for
               Software mode and 100 kHz for hardware mode and Raspbberry Pi 
               Pico in all modes).  This parameter is ignored for Raspberry Pi 
               in hardeware mode, where the frequency is always 100 kHz.
               Also accepts PObjects of Unit Hz.
        @param attempts number of read or write attempts before throwing an
               exception
        @param usePEC set True to use Packet Error Checking
        @throws GPIOException in case of parameter error
        """
        # store our incoming parameters
        self._sdaLine= argToLine( sdaPin )
        self._sclLine= argToLine( sclPin )
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

    def __str__( self ):
        """!
        @brief String representing of initialization parameters used by this 
               class.
        """
        return 'sda Pin: GPIO{0}, scl Pin: GPIO{1}, mode: {2}, f: {3} kHz,\n'\
               'num. attempts: {4}, PEC: {5}' \
               .format( self.sda,
                        self.scl,
                        str( self.mode ).replace( '_', '' ),
                        float( self.frequency ) / 1000.,
                        self.attempts,
                        self.usePEC )
    
    @property
    def sda( self ):
        """!
        @brief Works as read-only property to get the sda line number.
        """
        return self._sdaLine

    @property
    def scl( self ):
        """!
        @brief Works as read-only property to get the scl line number.
        """
        return self._sclLine

    @property
    def mode( self ):
        """!
        @brief Works as read-only property to get the I<sup>2</sup>C bus mode
               (I2Cbus.Mode.HARDWARE or I2Cbus.Mode.SOFTWARE).
        """
        return self._mode

    @property
    def frequency( self ):
        """!
        @brief Works as read-only property to get the frequency the
               I<sup>2</sup>C bus is operating at.
        """
        return self._orgFrequency

    @property
    def attempts( self ):
        """!
        @brief Obtain the user-supplied number of communication attempts.
        """
        return self._attempts

    @property
    def usePEC( self ):
        """!
        @brief Return current status of Packet Error Checking.
        """
        return self._usePEC
        
    @abstractmethod
    def close( self ):
        """!
        @brief On Raspberry Pis using pigpio, it is important to call this 
               method to properly close the pigpio object in software mode.
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
        @brief Issue an I<sup>2</sup>C device address with the write bit set
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
        @param register device register to write to
        @param value value of byte to be written as an int
        """
        pass

    @abstractmethod
    def writeBlockReg( self, i2cAddress: int, register: int, block: int ):
        """!
        @brief Write a block of bytes to an I<sup>2</sup>C device starting at
               register.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param register device register to start writing
        @param block list of ints with bytes to be written
        """
        pass

