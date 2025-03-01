# Python Implementation: _I2CAPI
# -*- coding: utf-8 -*-
##
# @file       _I2CAPI.py
#
# @version    2.0.0
#
# @par Purpose
# Provides API for all flavors of the I2C bus software.
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
#   Mon Jan 27 2025 | Ekkehard Blanz | extracted from I2Cbus.py
#                   |                |
#

from GPIO_AL.tools import argToLine
from GPIO_AL.GPIOError import GPIOError
from GPIO_AL.tools import isPico, lineToStr

if isPico():
    class ABC:
        pass
    def abstractmethod( f ):
        return f
    # MicroPython silently ignores type hints without the need to import typing
    Enum = object
else:
    from abc import ABC, abstractmethod # type: ignore
    from typing import Union
    from enum import Enum


class _I2CAPI( ABC ):
    """!
    @brief Abstract base class provides API for I<sup>2</sup>C classes.

    NOTE: metaclass=ABCMeta has been replaced by just ABCMeta inheritance to make
    also work under MicroPython.
    """

    # Enums are provided in the API so children have them.
    # They are copied to the main class so clients have easy access to them.

    class _Mode( Enum ): # type: ignore
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
        @param sdaPin header pin number or GPIO line string for I<sup>2</sup>C 
               data (default GPIO2 on Raspberry Pi and 8 on Raspberry Pi Pico).
               Ints are interpreted as header pin numbers, strings starting with
               GPIO as line numbers.
        @param sclPin header pin number or GPIO line string for I<sup>2</sup>C 
               clock (default GPIO3 on Raspberry Pi and 9 on Raspberry Pi Pico).
               Ints are interpreted as header pin numbers, strings starting with
               GPIO as line numbers.
        @param mode one of I2C.Mode.HARDWARE or I2C.Mode.SOFTWARE
        @param frequency I<sup>2</sup>C frequency in Hz (default 75 kHz for
               Software mode and 100 kHz for hardware mode and Raspberry Pi 
               Pico in all modes).  This parameter is ignored for Raspberry Pi 
               in hardware mode, where the frequency is always 100 kHz.
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
            if str( frequency.unit ) != 'Hz': # type: ignore
                raise GPIOError( 'Wrong frequency object specified: {0}'
                                 .format( frequency ) )
        except AttributeError:
            pass
        self._orgFrequency = frequency
        self._frequency = float( frequency ) # type: ignore
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
        return 'sda line: {0}, scl line: {1}, mode: I2C.{2}, f: {3} kHz,\n'\
               'num. attempts: {4}, PEC: {5}' \
               .format( self.sda,
                        self.scl,
                        str( self.mode ).replace( '_', '' ),
                        float( self.frequency ) / 1000., # type: ignore
                        self.attempts,
                        self.usePEC )
    
    @property
    def sda( self ) -> str:
        """!
        @brief Works as read-only property to get the sda line string.
        """
        return lineToStr( self._sdaLine )

    @property
    def scl( self ) -> str:
        """!
        @brief Works as read-only property to get the scl line string.
        """
        return lineToStr( self._sclLine )

    @property
    def mode( self ) -> _Mode:
        """!
        @brief Works as read-only property to get the I<sup>2</sup>C bus mode
               (I2C.Mode.HARDWARE or I2C.Mode.SOFTWARE).
        """
        return self._mode

    @property
    def frequency( self ) -> Union[float, object]:
        """!
        @brief Works as read-only property to get the frequency the
               I<sup>2</sup>C bus is operating at.
        """
        return self._orgFrequency

    @property
    def attempts( self ) -> int:
        """!
        @brief Obtain the user-supplied number of communication attempts.
        """
        return self._attempts

    @property
    def usePEC( self ) -> bool:
        """!
        @brief Return current status of Packet Error Checking.
        """
        return self._usePEC
        
    @abstractmethod
    def close( self ):
        """!
        @brief On Raspberry Pis using pigpio, it is very important to call this
               method to properly close the pigpio object in software mode.
        """
        pass

    def readId( self, i2cAddress ) -> tuple:
        """!
        @brief Read the ID tuple of a device consisting of manufacturer ID,
               device ID, and die revision.
        @param i2cAddress address of I<sup>2</sup>C device to read ID from
        @return tuple of (manufacturerId, deviceId, dieRev)
        @throws GPIOError in case of an error
        """
        try:
            self.writeQuick( 0x7C )
        except Exception as e:
            # no acknowledge bit causes exception but we don't care
            pass
        byteList = self.readBlockReg( i2cAddress, 0x7C, 3 )
        manufacturerId = byteList[1] >> 4 | byteList[1] >> 4
        deviceId = (byteList[1] & 0x0F) << 5 | (byteList[2] & 0xF8) >> 3
        dieRev = byteList[2] & 0x07
        return manufacturerId, deviceId, dieRev

    @abstractmethod
    def readByte( self, i2cAddress: int ) -> int:
        """!
        @brief Read a single general byte from an I<sup>2</sup>C device.
        @param i2cAddress int address of I<sup>2</sup>C device to be read from
        @return int with byte read
        """
        return 0

    @abstractmethod
    def readByteReg( self, 
                     i2cAddress: int, 
                     register: int ) -> int:
        """!
        @brief Read a single byte from an I<sup>2</sup>C device register.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @param register device register to read from as an int
        @return int with byte read
        """
        return 0

    @abstractmethod
    def readBlockReg( self,
                      i2cAddress: int,
                      register: int,
                      length: int ) -> list:
        """!
        @brief Read a block of bytes from an I<sup>2</sup>C device register.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @param register device register to start reading
        @param length number of bytes to be read
        @return list of ints with bytes read
        """
        return []

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
    def writeBlockReg( self, i2cAddress: int, register: int, block: list ):
        """!
        @brief Write a block of bytes to an I<sup>2</sup>C device starting at
               register.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param register device register to start writing
        @param block list of ints with bytes to be written
        """
        pass

