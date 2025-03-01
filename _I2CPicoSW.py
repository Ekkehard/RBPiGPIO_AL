# Python Implementation: _I2CPico
# -*- coding: utf-8 -*-
##
# @file       _I2CPico.py
#
# @version    2.0.0
#
# @par Purpose
# Provides I<sup>2</sup>C bus code for Raspberry Pi Pico in software.
#
# This code has been tested on a Raspberry Pi Pico.
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

from GPIO_AL._I2CAPI import _I2CAPI

import machine

class _I2CPicoSW( _I2CAPI ):
    """!
    @brief Class dedicated to I2C hardware and software operations on the
           Raspberry Pi Pico.
    """

    def __init__( self,
                  sdaPin,
                  sclPin,
                  mode,
                  frequency,
                  attempts,
                  usePEC ):
        """!
        @brief Constructor for class I2CPicoSW.
        @param sdaPin pin number or GPIO line string for I<sup>2</sup>C data
        @param sclPin pin number or GPIO line string for I<sup>2</sup>C clock
        @param mode operational mode
        @param frequency I<sup>2</sup>C frequency in Hz
        @param attempts number of read or write attempts before throwing an
               exception
        @param usePEC set True to use Packet Error Checking
        """
        super().__init__( sdaPin, sclPin, mode, frequency, attempts, usePEC )
        self._usePEC = False

        
        self.__i2cObj = machine.SoftI2C( sda=machine.Pin( self._sdaLine ),
                                         scl=machine.Pin( self._sclLine ),
                                         freq=round( self._frequency ) )
        self.__open = True
        return

    def __del__( self ):
        """!
        @brief Destructor.
        """
        self.close()
        return

    def close( self ):
        """!
        @brief close the I2C device.
        """
        if self.__open:
            try:
                self.__i2cObj.deinit()
            except AttributeError:
                pass
            self.__open = False
        return

    def readByte( self, i2cAddress ):
        """!
        @brief Read a single general byte from an I<sup>2</sup>C device.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @return int with byte read
        """
        return list( self.__i2cObj.readfrom( i2cAddress, 1 ) )[0]

    def readByteReg( self, i2cAddress, register ):
        """!
        @brief Read a single byte from an I<sup>2</sup>C device register.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @param register device register to read from
        @return int with byte read
        """
        return list( self.__i2cObj.readfrom_mem( i2cAddress,
                                                 register,
                                                 1 ) )[0]

    def readBlockReg( self, i2cAddress, register, length ):
        """!
        @brief Read a block of bytes from an I<sup>2</sup>C device register.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @param register device register to start reading
        @param length number of bytes to be read
        @return list of ints with bytes read
        """
        return list( self.__i2cObj.readfrom_mem( i2cAddress,
                                                 register,
                                                 length ) )

    def writeQuick( self, i2cAddress ):
        """!
        @brief Issue an I<sup>2</sup>C  device address with the write bit set
        and check the acknowledge signal but do not write anything else.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        """
        self.__i2cObj.writeto( i2cAddress, bytearray( [] ) )
        return

    def writeByte( self, i2cAddress, value ):
        """!
        @brief Write a single byte to an I<sup>2</sup>C device.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param value value of byte to be written as an int
        """
        self.__i2cObj.writeto( i2cAddress, bytearray( [value] ) )
        return

    def writeByteReg( self, i2cAddress, register, value ):
        """!
        @brief Write a single byte to an I<sup>2</sup>C device register.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param register device register to write to
        @param value value of byte to be written as an int
        """
        self.__i2cObj.writeto_mem( i2cAddress,
                                   register,
                                   bytearray( [value] ) )
        return

    def writeBlockReg( self, i2cAddress, register, block ):
        """!
        @brief Write a block of bytes to an I<sup>2</sup>C device starting at
               register.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param register device register to start writing
        @param block list of ints with bytes to be written
        """
        self.__i2cObj.writeto_mem( i2cAddress,
                                   register,
                                   bytearray( block ) )
        return
