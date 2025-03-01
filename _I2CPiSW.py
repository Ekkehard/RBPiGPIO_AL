# Python Implementation: _I2CbusPiSW
# -*- coding: utf-8 -*-
##
# @file       _I2CbusPiSW.py
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

from enum import IntEnum
from GPIO_AL.GPIOError import GPIOError
from GPIO_AL.tools import isPi5
from GPIO_AL._I2CAPI import _I2CAPI
              
class _I2CPiSW( _I2CAPI ):
    """!
    @brief Class dedicated to I2C software operations on the Raspberry Pi.
    """

    class BBMode( IntEnum ):
        # bb_i2c_zip commands:
        END = 0
        START = 2
        RESTART = 2
        STOP = 3
        ADDRESS = 4
        READ = 6
        WRITE = 7

    def __init__( self,
                  sdaPin,
                  sclPin,
                  mode,
                  frequency,
                  attempts,
                  usePEC ):
        """!
        @brief Constructor for class _PiSWI2C.
        @param sdaPin Pin number of GPIO line string for I<sup>2</sup>C data
        @param sclPin Pin number of GPIO line string for I<sup>2</sup>C clock
        @param mode operational mode
        @param frequency I<sup>2</sup>C frequency in Hz
        @param attempts number of read or write attempts before throwing an
               exception
        @param usePEC set True to use Packet Error Checking
        """
        self.__open = False
        if isPi5():
            raise GPIOError( 'Software mode not yet implemented '
                             'for RB Pi 5 as pigpio is not working here' )
        if mode != self._Mode.SOFTWARE:
            raise GPIOError( 'Internal Error: '
                             'Called software mode with wrong mode: {0}'
                             .format( mode ) )
        super().__init__( sdaPin, sclPin, mode, frequency, attempts, usePEC )
        import pigpio
        self.__i2cObj = pigpio.pi()
        if not self.__i2cObj.connected:
            raise GPIOError( 'Could not connect to GPIO via pigpio' )
            
        if self._frequency > 75000.0:
            raise GPIOError( 'Wrong frequency specified: {0}'
                             .format( self._orgFrequency ) )

        try:
            if self.__i2cObj.bb_i2c_open( self._sdaLine,
                                          self._sclLine,
                                          round( self._frequency ) ) != 0:
                raise GPIOError( 'Opening Software I2C failed' )
            self._usePEC = False
        except Exception as e:
            raise GPIOError( str( e ) )
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
        @brief Close the I2C device.
        """
        if self.__open:
            try:
                self.__i2cObj.bb_i2c_close( self._sdaLine )
            except:
                pass
            self.__i2cObj.stop()
            self.__open = False
        return

    def readByte( self, i2cAddress ) -> int:
        """!
        @brief Read a single general byte from an I<sup>2</sup>C device.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @return int with byte read
        """
        return int( list( self.__i2cObj.bb_i2c_zip( self._sdaLine,
                                               [self.BBMode.START,
                                                self.BBMode.ADDRESS, i2cAddress,
                                                self.BBMode.READ, 1,
                                                self.BBMode.STOP,
                                                self.BBMode.END] )[1] )[0] )
                                                
    def readByteReg( self, i2cAddress, register ):
        """!
        @brief Read a single byte from an I<sup>2</sup>C device register.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @param register device register to read from
        @return int with byte read
        """
        return  int( list( self.__i2cObj.bb_i2c_zip( self._sdaLine,
                                                [self.BBMode.START,
                                                 self.BBMode.ADDRESS, i2cAddress,
                                                 self.BBMode.WRITE, 1, register,
                                                 self.BBMode.RESTART,
                                                 self.BBMode.ADDRESS, i2cAddress,
                                                 self.BBMode.READ, 1,
                                                 self.BBMode.STOP,
                                                 self.BBMode.END] )[1] )[0] )

    def readBlockReg( self, i2cAddress, register, length ) -> list:
        """!
        @brief Read a block of bytes from an I<sup>2</sup>C device register.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @param register device register to start reading
        @param length number of bytes to be read
        @return list of ints with bytes read
        """
        return list( list( self.__i2cObj.bb_i2c_zip( self._sdaLine,
                                               [self.BBMode.START,
                                                self.BBMode.ADDRESS, i2cAddress,
                                                self.BBMode.WRITE, 1, register,
                                                self.BBMode.RESTART,
                                                self.BBMode.ADDRESS, i2cAddress,
                                                self.BBMode.READ, length,
                                                self.BBMode.STOP,
                                                self.BBMode.END] ) )[1] )

    def writeQuick( self, i2cAddress ):
        """!
        @brief Issue an I<sup>2</sup>C  device address with the write bit set
               and check the acknowledge signal but do not write anything else.
        
        The following does not work as it does not throw an exception when no
        acknowledge is sent 
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        """
        self.__i2cObj.bb_i2c_zip( self._sdaLine,
                                  [self.BBMode.START,
                                   self.BBMode.ADDRESS, i2cAddress,
                                   self.BBMode.WRITE, 0,
                                   self.BBMode.STOP,
                                   self.BBMode.END] )
        return

    def writeByte( self, i2cAddress, value ):
        """!
        @brief Write a single byte to an I<sup>2</sup>C device.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param value value of byte to be written as an int
        """
        self.__i2cObj.bb_i2c_zip( self._sdaLine,
                                  [self.BBMode.START,
                                   self.BBMode.ADDRESS, i2cAddress,
                                   self.BBMode.WRITE, 1, value,
                                   self.BBMode.STOP,
                                   self.BBMode.END] )
        return

    def writeByteReg( self, i2cAddress, register, value ):
        """!
        @brief Write a single byte to an I<sup>2</sup>C device register.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param register device register to write to
        @param value value of byte to be written as an int
        """
        self.__i2cObj.bb_i2c_zip( self._sdaLine,
                                  [self.BBMode.START,
                                   self.BBMode.ADDRESS, i2cAddress,
                                   self.BBMode.WRITE, 2,
                                   register, value,
                                   self.BBMode.STOP,
                                   self.BBMode.END] )
        return


    def writeBlockReg( self, i2cAddress, register, block ):
        """!
        @brief Write a block of bytes to an I<sup>2</sup>C device starting at
               register.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param register device register to start writing
        @param block list of ints with bytes to be written
        """
        self.__i2cObj.bb_i2c_zip( self._sdaLine,
                                  [self.BBMode.START,
                                   self.BBMode.ADDRESS, i2cAddress,
                                   self.BBMode.WRITE, 1 + len( block ),
                                   register] +
                                  block +
                                  [self.BBMode.STOP,
                                   self.BBMode.END] )
        return
