# Python Implementation: _PiI2Cbus
# -*- coding: utf-8 -*-
##
# @file       _PiI2Cbus.py
#
# @version    4.0.0
#
# @par Purpose
# Provides I2Cbus code for Raspberry Pis - hardware and software
#
# This code has been tested on a Raspberry Pi 0, 3, 4 and 5.
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
from ._I2CbusAPI import _I2CbusAPI
from .GPIOError import GPIOError

class _PiHWI2C( _I2CbusAPI ):
    """!
    """
    DEFAULT_BUS = 1
    DEFAULT_DATA_PIN = 'GPIO2'
    DEFAULT_CLOCK_PIN = 'GPIO3'
    DEFAULT_MODE = self.Mode.HARDWARE
    ## Number of I/O attempts in I/O methods before throwing exception
    ATTEMPTS = 1
    ## Default frequency for I<sup>2</sup>C bus communications on chips
    ## other than the BCM2835 is 100 kHz
    DEFAULT_I2C_FREQ = 100000


    def __init__( self,
                  sdaPin=DEFAULT_DATA_PIN,
                  sclPin=DEFAULT_CLOCK_PIN,
                  mode=DEFAULT_MODE,
                  frequency=DEFAULT_I2C_FREQ,
                  attempts=ATTEMPTS,
                  usePEC=False ):
        """!
        @brief Constructor for class _PiHWI2C.

        @param sdaPin GPIO Pin number for I<sup>2</sup>C data (default GPIO2 on
               Raspberry Pi and 8 on Raspberry Pi Pico)
        @param sclPin GPIO Pin number for I<sup>2</sup>C clock (default GPIO3 on
               Raspberry Pi and 9 on Raspberry Pi Pico)
        @param mode one of I2<Cbus.HARDWARE_MODE or I2Cbus.SOFTWARE_MODE
               AKA bit banging (default I2Cbus.SOFTWARE for Raspberry Pi and
               I2Cbus.HARDWARE for Raspberry Pi Pico)
        @param frequency I<sup>2</sup>C frequency in Hz (default 75 kHz for
               Software mode and 100 kHz for hardware mode and Raspbberry Pi 
               Pico in all modes).  This parameter is ignored for Raspberry Pi 
               in hardeware mode, where the frequency is always 100 kHz.
        @param attempts number of read or write attempts before throwing an
               exception (default 1 for Pico in all modes and 5 for Pi in 
               software mode)
        @param usePEC set True to use Packet Error Checking (default False).
               This parameter is ignored when PEC is not supported.
        """
        if mode != self.Mode.SOFTWARE:
            raise GPIOError( 'Internal Error: '
                             'Called software mode with wrong mode' )

        super().__init__( sdaPin, sclPin, mode, frequency, attempts, usePEC )
        # if bit banging buses are left open they cause problems even for
        # ahardware I2C operations
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

        if self._sdaPin == 0 and self._sclPin == 1 and not isPi5():
            i2cBus = 0
        elif self._sdaPin == 2 and self._sclPin == 3:
            i2cBus = 1
        else:
            raise GPIOError( 'Wrong I2C Pins specified' )
            
        if self._frequency != DEFAULT_I2C_FREQ:
            raise GPIOError( 'Wrong frequency specified: {0}'
                             .format( self.orgFrequency ) )
                             
        # SMBus's __init__() does an open() internally
        self.__i2cObj = SMBus( i2cBus )
        try:
            self.__i2cObj.enable_pec( self._usePEC )
        except IOError:
            self._usePEC = False

        self.__open = True
        self.__failedAttempts = 0
        return


    def __del__( self ):
        """!
        @brief Destructor - only meaningful on the Raspberry Pi and
               potentially during Unit Tests on the Raspberry Pi Pico.

        Closes the software I<sup>2</sup>C bus on the Raspberry Pi.
        """
        self.close()
        return


    def __str__( self ):
        """!
        @brief String representing initialization parameters used by this class.
        """
        return 'sda Pin: GPIO{0}, scl Pin: GPIO{1}, mode: HW, f: {2} kHz, ' \
               'num. attempts: {3}, usePEC: {4}' \
               .format( self._sdaPin,
                        self._sclPin,
                        self._frequency / 1000.,
                        self._attempts,
                        self._usePEC )

    def close( self ):
        """!
        @brief On the Raspberry Pi, it is important to call this method to
               properly close the pigpio object in software mode.
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
        @param register device register to start reading
        @param value value of byte to be written as an int
        """
        self.__i2cObj.write_byte_data( i2cAddress, register, value )
        return
        
    def writeBlockReg( self, i2cAddress, register, block ):
        """!
        @brief Write a block of bytes to an I<sup>2</sup>C device starting at
               register.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param register device register to start reading
        @param block list of ints with bytes to be written
        """
        self.__i2cObj.write_i2c_block_data( i2cAddress, register, block )
        return
              
              
class _PiSWI2C( _I2CbusAPI ):
    """!
    """
        DEFAULT_DATA_PIN = 'GPIO2'
        DEFAULT_CLOCK_PIN = 'GPIO3'
        DEFAULT_MODE = self.Mode.SOFTWARE
        DEFAULT_I2C_FREQ = 75000
        ATTEMPTS = 5

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
                  sdaPin: Optional[Union[int, str]]=DEFAULT_DATA_PIN,
                  sclPin: Optional[Union[int, str]]=DEFAULT_CLOCK_PIN,
                  mode: Optional[int]=DEFAULT_MODE,
                  frequency: Optional[Union[float,object]]=DEFAULT_I2C_FREQ,
                  attempts: Optional[int]=ATTEMPTS,
                  usePEC: Optional[bool]=False ):
        """!
        @brief Constructor for class _PiSWI2C.

        @param sdaPin GPIO Pin number for I<sup>2</sup>C data (default GPIO2 on
               Raspberry Pi and 8 on Raspberry Pi Pico)
        @param sclPin GPIO Pin number for I<sup>2</sup>C clock (default GPIO3 on
               Raspberry Pi and 9 on Raspberry Pi Pico)
        @param mode one of I2<Cbus.HARDWARE_MODE or I2Cbus.SOFTWARE_MODE
               AKA bit banging (default I2Cbus.SOFTWARE for Raspberry Pi and
               I2Cbus.HARDWARE for Raspberry Pi Pico)
        @param frequency I<sup>2</sup>C frequency in Hz (default 75 kHz for
               Software mode and 100 kHz for hardware mode and Raspbberry Pi 
               Pico in all modes).  This parameter is ignored for Raspberry Pi 
               in hardeware mode, where the frequency is always 100 kHz.
        @param attempts number of read or write attempts before throwing an
               exception (default 1 for Pico in all modes and 5 for Pi in 
               software mode)
        @param usePEC set True to use Packet Error Checking (default False).
               This parameter is ignored when PEC is not supported.
        """
        
        if isPi5():
            raise GPIOError( 'Software mode not yet implemented '
                             'for RB Pi 5 is pigpio is not working here' )
        if mode != self.Mode.SOFTWARE:
            raise GPIOError( 'Internal Error: '
                             'Called software mode with wrong mode' )
        super().__init__( sdaPin, sclPin, mode, frequency, attempts, usePEC )
        import pigpio
        self.__i2cObj = pigpio.pi()
        if not self.__i2cObj.connected:
            raise GPIOError( 'Could not connect to GPIO via pigpio' )
        try:
            # in case somebody didn't close it properly...
            self.__i2cObj.bb_i2c_close( self._sdaPin )
        except:
            pass


        try:
            if self.__i2cObj.bb_i2c_open( self._sdaPin,
                                          self._sclPin,
                                          self._frequency ) != 0:
                raise GPIOError( 'Opening Software I2C failed' )
            self._usePEC = False
        except Exception as e:
            raise GPIOError( str( e ) )
        self.__open = True
        return

    def __del__( self ):
        """!
        @brief Destructor - only meaningful on the Raspberry Pi and
               potentially during Unit Tests on the Raspberry Pi Pico.

        Closes the software I<sup>2</sup>C bus on the Raspberry Pi.
        """
        self.close()
        return

    def __str__( self ):
        """!
        @brief String representing initialization parameters used by this class.
        """
        return 'sda Pin: GPIO{0}, scl Pin: GPIO{1}, mode: SW, f: {2} kHz, '\
               'num. attempts: {3}, PEC: {4}' \
               .format( self._sdaPin,
                        self._sclPin,
                        self._frequency / 1000.,
                        self._attempts,
                        self._usePEC )

    def close( self ):
        """!
        @brief On the Raspberry Pi, it is important to call this method to
               properly close the pigpio object in software mode.
        """
        if self.__open:
            try:
                self.__i2cObj.bb_i2c_close( self._sdaPin )
            except:
                pass
            self.__i2cObj.stop()
            self.__open = False
        return

    def readByte( self, i2cAddress ):
        """!
        @brief Read a single general byte from an I<sup>2</sup>C device.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @return int with byte read
        """
        return list( self.__i2cObj.bb_i2c_zip( self._sdaPin,
                                               [self.BBMode.START,
                                                self.BBMode.ADDRESS, i2cAddress,
                                                self.BBMode.READ, 1,
                                                self.BBMode.STOP,
                                                self.BBMode.END] )[1] )[0]
                                                
    def readByteReg( self, i2cAddress, register ):
        """!
        @brief Read a single byte from an I<sup>2</sup>C device register.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @param register device register to read from
        @return int with byte read
        """
        return  list( self.__i2cObj.bb_i2c_zip( self._sdaPin,
                                                [self.BBMode.START,
                                                self.BBMode.ADDRESS, i2cAddress,
                                                 self.BBMode.WRITE, 1, register,
                                                 self.BBMode.RESTART,
                                                 self.BBMode.ADDRESS, i2cAddress,
                                                 self.BBMode.READ, 1,
                                                 self.BBMode.STOP,
                                                 self.BBMode.END] )[1] )[0]

    def readBlockReg( self, i2cAddress, register, length ):
        """!
        @brief Read a block of bytes from an I<sup>2</sup>C device register.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @param register device register to start reading
        @param length number of bytes to be read
        @return list of ints with bytes read
        """
        return list( self.__i2cObj.bb_i2c_zip( self._sdaPin,
                                               [self.BBMode.START,
                                                self.BBMode.ADDRESS, i2cAddress,
                                                self.BBMode.WRITE, 1, register,
                                                self.BBMode.RESTART,
                                                self.BBMode.ADDRESS, i2cAddress,
                                                self.BBMode.READ, length,
                                                self.BBMode.STOP,
                                                self.BBMode.END] )[1] ))

    def writeQuick( self, i2cAddress ):
        """!
        @brief Issue an I<sup>2</sup>C  device address with the write bit set
               and check the acknowledge signal but do not write anything else.
        
        The following does not work as it does not throw an exception when no
        acknowledge is sent 
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        """
        self.__i2cObj.bb_i2c_zip( self._sdaPin,
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
        self.__i2cObj.bb_i2c_zip( self._sdaPin,
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
        @param register device register to start reading
        @param value value of byte to be written as an int
        """
        self.__i2cObj.bb_i2c_zip( self._sdaPin,
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
        @param register device register to start reading
        @param block list of ints with bytes to be written
        """
        self.__i2cObj.bb_i2c_zip( self._sdaPin,
                                  [self.BBMode.START,
                                   self.BBMode.ADDRESS, addr,
                                   self.BBMode.WRITE, 1 + len( block ),
                                   register] +
                                  block +
                                  [self.BBMode.STOP,
                                   self.BBMode.END] )
        return
