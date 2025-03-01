# Python Implementation: _I2CbusPiHW
# -*- coding: utf-8 -*-
##
# @file       _I2CbusPiHW.py
#
# @version    2.0.0
#
# @par Purpose
# Provides I2Cbus code for Raspberry Pis - hardware and software
#
# This code has been tested on a Raspberry Pi 0, 3, 4 and 5.
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

from GPIO_AL.GPIOError import GPIOError
from GPIO_AL.tools import isPi5
from GPIO_AL._I2CAPI import _I2CAPI

class _I2CPiHW( _I2CAPI ):
    """!
    @brief Class dedicated to I2C hardware operations on the Raspberry Pi.
    """


    def __init__( self,
                  sdaPin,
                  sclPin,
                  mode,
                  frequency,
                  attempts,
                  usePEC ):
        """!
        @brief Constructor for class _PiHWI2C.
        @param sdaPin Pin number of GPIO line string for I<sup>2</sup>C data
        @param sclPin Pin number of GPIO line string for I<sup>2</sup>C clock
        @param mode operational mode
        @param frequency I<sup>2</sup>C frequency in Hz
        @param attempts number of read or write attempts before throwing an
               exception
        @param usePEC set True to use Packet Error Checking
        """
        self.__open = False
        if mode != self._Mode.HARDWARE:
            raise GPIOError( 'Internal Error: '
                             'Called hardware mode with wrong mode: {0}'
                             .format( mode ) )

        super().__init__( sdaPin, sclPin, mode, frequency, attempts, usePEC )
        # if bit banging buses are left open they cause problems even for
        # hardware I2C operations
        if not isPi5():
            # This assumes that software I2C is handled via pigpio
            # TODO once we got our own software I2C, this can go away
            import pigpio
            i2cObj = pigpio.pi()
            try:
                i2cObj.bb_i2c_close( 2 )
                i2cObj.stop()
            except Exception:
                pass

        # in hardware mode, use SMBus - prefer smbus2 over smbus
        try:
            from smbus2 import SMBus
        except ModuleNotFoundError:
            from smbus import SMBus

        if self._sdaLine == 0 and self._sclLine == 1 and not isPi5():
            i2cBus = 0
        elif self._sdaLine == 2 and self._sclLine == 3:
            i2cBus = 1
        else:
            raise GPIOError( 'Wrong I2C Pins specified' )
            
        if self._frequency != 100000:
            raise GPIOError( 'Wrong frequency specified: {0}'
                             .format( self._orgFrequency ) )
                             
        # SMBus's __init__() does an open() internally
        self.__i2cObj = SMBus( i2cBus )
        try:
            self.__i2cObj.enable_pec( self._usePEC )
        except IOError:
            self._usePEC = False

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
        @brief Closes the I2C device.
        """
        if self.__open:
            self.__i2cObj.close()
            self.__open = False
        return

    def readByte( self, i2cAddress ):
        """!
        @brief Read a single general byte from an I<sup>2</sup>C device.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @return int with byte read
        """
        return self.__i2cObj.read_byte( i2cAddress )

    def readByteReg( self, i2cAddress, register ):
        """!
        @brief Read a single byte from an I<sup>2</sup>C device register.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @param register device register to read from
        @return int with byte read
        """
        return self.__i2cObj.read_byte_data( i2cAddress, register )


    def readBlockReg( self, i2cAddress, register, length ):
        """!
        @brief Read a block of bytes from an I<sup>2</sup>C device register.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @param register device register to start reading
        @param length number of bytes to be read
        @return list of ints with bytes read
        """
        return self.__i2cObj.read_i2c_block_data( i2cAddress,
                                                  register,
                                                  length )

    def writeQuick( self, i2cAddress ):
        """!
        @brief Issue an I<sup>2</sup>C  device address with the write bit set
        and check the acknowledge signal but do not write anything else.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        """
        self.__i2cObj.write_quick( i2cAddress )
        return

    def writeByte( self, i2cAddress, value ):
        """!
        @brief Write a single byte to an I<sup>2</sup>C device.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param value value of byte to be written as an int
        """
        self.__i2cObj.write_byte( i2cAddress, value )
        return
        
    def writeByteReg( self, i2cAddress, register, value ):
        """!
        @brief Write a single byte to an I<sup>2</sup>C device register.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param register device register to write to
        @param value value of byte to be written as an int
        """
        self.__i2cObj.write_byte_data( i2cAddress, register, value )
        return
        
    def writeBlockReg( self, i2cAddress, register, block ):
        """!
        @brief Write a block of bytes to an I<sup>2</sup>C device starting at
               register.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param register device register to start writing
        @param block list of ints with bytes to be written
        """
        self.__i2cObj.write_i2c_block_data( i2cAddress, register, block )
        return
              