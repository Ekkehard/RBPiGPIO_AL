# Python Implementation: I2CbusL
# -*- coding: utf-8 -*-
##
# @file       I2Cbus.py
#
# @version    4.0.0
#
# @par Purpose
# This module provides an I2C bus abstraction layer for the Raspberry Pi General 
# Purpose I/O (GPIO) functionality for all models of the regular Raspberry Pi 0 
# and up as well as the Raspberry Pi Pico.  Using this module, code should run 
# and use the common functionality of the GPIO shared by all Raspberry Pi 
# architectures without modifications on all those architectures.
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
#   Sat Dec 14 2024 | Ekkehard Blanz | extracted from GPIO_AL.py
#   Thu Jan 23 2025 | Ekkehard Blanz | now also works on a Raspberry Pi 5
#                   |                |
#

from typing import Union, Optional
from enum import Enum, IntEnum
from GPIO_AL.tools import isPico, cpuInfo, isPi5, argToLine
from GPIO_AL import GPIOError


class I2Cbus():
    """!
    @brief Class to handle I<sup>2</sup>C bus communication.

    The GPIO Pins on the Raspberry Pi are GPIO 2 for I<sup>2</sup>C data and
    GPIO 3 for I<sup>2</sup>C clock for hardware I<sup>2</sup>C and freely
    selectable for software I<sup>2</sup>C (bit banging); on the Raspberry Pi
    Pico, the GPIO Pins for I<sup>2</sup>C communication are also freely
    selectable under software I<sup>2</sup>C, they are restricted to GPIO 1 for
    data and GPIO 2 for clock, GPIO 4 for data and GPIO 5 for clock, GPIO 6
    for data and GPIO 7 for clock, GPIO 9 for data and GPIO 10 for clock,
    GPIO 11 for data and GOPI 12 for clock, GPIO 14 for data and GOPI 15 for
    clock, GPIO 16 for data and GPIO 17 for clock, GPIO 19 for data and GPIO
    20 for clock, GPIO 21 for data and GPIO 22 for clock, GPIO 24 for data
    and GPIO 25 for clock, GPIO 26 for data and GPIO 27 for clock, or GPIO 31
    for data and GPIO 32 for clock.

    Since many targets can be connected on an I<sup>2</sup>C bus, one I2Cbus
    object must be able to handle them all.  Therefore, I2Cbus objects are
    created one per I<sup>2</sup>C bus, which is uniquely defined by the sda
    and scl Pins - NOT one such object per target on that bus.  Every
    I<sup>2</sup>C I/O operation therefore needs to be given the
    I<sup>2</sup>C address of the target this communication is meant for.

    On the Raspberries running under Linux-like operating systems, it is
    mandatory that the user be part of the group i2c to be able to use the
    I<sup>2</sup>C bus.  This can be accomplished by issuing the command (in a
    terminal window)
    @code
        sudo usermod -a -G i2c <user name>
    @endcode
    and then logging out and back in again.  Otherwise, access to the
    I<sup>2</sup>C device requires elevated privileges (sudo), and the
    practice of using those when not strictly necessary is strongly discouraged.

    Also, on systems Raspberry Pis other than the Raspberry Pi 5 running under 
    an operating system the pigpiod daemon needs to run to use the software 
    mode.  Either use
    @code
        sudo pigpiod
    @endcode
    whenever you want to use it or enable the daemon at boot time using
    @code
        sudo systemctl enable pigpiod
    @endcode
    to have the GPIO daemon start every time the Raspberry Pi OS boots.  On the
    Raspberry Pi 5 pigpio no longer works, and therefore software mode is
    currently not available there.

    It is worth noting that the defaults for the operating mode are different
    between different systems.  This is because either the Broadcomm BCM2835 
    chip, which the Raspberry Pi 3 uses for hardware I<sup>2</sup>C, or the 
    standard Raspberry Pi driver smbus2 is broken and does not (reliably) 
    support clock stretching when requested by a target.  This was found through
    experimentation and measurements and also confirmed online at
    https://www.advamation.com/knowhow/raspberrypi/rpi-i2c-bug.html.  The
    software mode supports clock stretching properly on the Raspberry Pi 3.
    Naturally, the software-generated I<sup>2</sup>C clock on a non-real-time
    OS is not very consistent, but targets will tolerate a non-consistent
    clock better, albeit not always completely, than a broken clock-stretch
    mechanism when they need it.  Therefore, the default operating mode on a
    Raspberry Pi 3 is software, but since other systems work just fine with
    hardware I<sup>2</sup>C, the default operating mode there is hardware to 
    free the CPU from the task of generating I<sup>2</sup>C signals.  This 
    software still allows the caller to select hardware mode also on the 
    Raspberry Pi 3, but the user is strongly advised to make sure that no target
    on the I<sup>2</sup>C bus requires clock stretching in such cases.  
    Moreover, the user is much more likely to run into error conditions on a 
    Raspberry Pi 3 I<sup>2</sup>C bus than on any other system, and it is a very
    good idea to write "robust" code that checks error conditions continuously 
    and deals with them appropriately when the I<sup>2</sup>C bus and clock 
    stretching has to be used on a Raspberry Pi 3, even in software mode.
    """

    ## Operate I<sup>2</sup>C bus in hardware mode
    HARDWARE_MODE = 0
    ## Operate I<sup>2</sup>C bus in software (bit banging) mode
    SOFTWARE_MODE = 1
    ## Default Bus (or I2cID on Pico) - bus for default Pins
    DEFAULT_BUS = 1
    if isPico():
        ## Default Pin number for sda (Different for different architectures)
        DEFAULT_DATA_PIN = 8
        ## Default Pin number for scl (Different for different architectures)
        DEFAULT_CLOCK_PIN = 9
        ## Default operating mode on the Pico is hardware so as not to
        ## overburden the CPU with tasks the hardware can do
        DEFAULT_MODE = HARDWARE_MODE
        ## Number of I/O attempts in I/O methods before throwing an exception
        ATTEMPTS = 1
        ## Default frequency for I<sup>2</sup>C bus communications on the
        ## Raspberry Pi Pico is 100 kHz
        DEFAULT_I2C_FREQ = 100000
    else:
        DEFAULT_DATA_PIN = 'GPIO2'
        DEFAULT_CLOCK_PIN = 'GPIO3'
        if cpuInfo()['chip'] == 'BCM2835':
            ## The BCM2835 chip or the standard Raspberry Pi driver smbus is
            ## broken, and the default operating mode for it is therefore set to
            ## software, which reauires pigpio and is therefore not availabel on
            ## the Raspberry Pi 5, whether the hardware is broken or not.
            DEFAULT_MODE = SOFTWARE_MODE
            ## Number of I/O attempts in I/O methods before throwing exception
            ## and since this is also not super reliable, we set it to 5
            ATTEMPTS = 5
            ## Default frequency for I<sup>2</sup>C bus communications for
            ## software mode on this chip is set to 75 kHz
            DEFAULT_I2C_FREQ = 75000
        else:
            # TODO test if this is fixed on RB Pi 4 and 5
            DEFAULT_MODE = HARDWARE_MODE
            ## Number of I/O attempts in I/O methods before throwing exception
            ATTEMPTS = 1
            ## Default frequency for I<sup>2</sup>C bus communications on chips
            ## other than the BCM2835 is 100 kHz
            DEFAULT_I2C_FREQ = 100000


    def __init__( self,
                  sdaPin: Optional[Union[int, str]]=DEFAULT_DATA_PIN,
                  sclPin: Optional[Union[int, str]]=DEFAULT_CLOCK_PIN,
                  mode: Optional[int]=DEFAULT_MODE,
                  frequency: Optional[Union[float,object]]=DEFAULT_I2C_FREQ,
                  attempts: Optional[int]=ATTEMPTS,
                  usePEC: Optional[bool]=False ):
        """!
        @brief Constructor for class I<sup>2</sup>Cbus.

        @param sdaPin GPIO Pin number for I<sup>2</sup>C data (default GPIO2 on
               Raspberry Pi and 8 on Raspberry Pi Pico)
        @param sclPin GPIO Pin number for I<sup>2</sup>C clock (default GPIO3 on
               Raspberry Pi and 9 on Raspberry Pi Pico)
        @param mode one of I2<Cbus.HARDWARE_MODE or I2Cbus.SOFTWARE_MODE
               AKA bit banging (default I2Cbus.SOFTWARE for Raspberry Pi and
               I2Cbus.HARDWARE for Raspberry Pi Pico)
        @param frequency I<sup>2</sup>C frequency in Hz (default 75 kHz for
               Raspberry Pi in Software mode and 100 kHz for Raspbberry Pi Pico
               in all modes).  This parameter is ignored for Raspberry Pi in
               hardeware mode, where the frequency is always 100 kHz.
        @param attempts number of read or write attempts before throwing an
               exception (default 1 for Pico and 5 for Pi software)
        @param usePEC set True to use Packet Error Checking (default False).
               This parameter is ignored when PEC is not supported.
        """
        # store our incoming parameters
        self.__sdaPin = argToLine( sdaPin )
        self.__sclPin = argToLine( sclPin )
        self.__mode = mode
        self.__usePEC = usePEC
        try:
            if str( frequency.unit ) != 'Hz':
                raise GPIOError( 'Wrong frequency object specified: {0}'
                                 .format( frequency ) )
        except AttributeError:
            pass
        self.__frequency = float( frequency )
        self.__attempts = attempts
        self.__failedAttempts = 0
        self.__open = False

        self.__i2cObj = None

        # initialize host-specific libraries and hardware
        if isPico():
            self.__setupRPPico()
        else:
            self.__setupRP()

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
        modeStr = ['HW', 'SW']
        return 'sda Pin: {0}, scl Pin: {1}, mode: {2}, f: {3} kHz, '\
               'num. attempts: {4}, PEC: {5}' \
               ''.format( self.__sdaPin,
                          self.__sclPin,
                          modeStr[self.__mode],
                          self.__frequency / 1000.,
                          self.__attempts,
                          self.__usePEC )


    def close( self ):
        """!
        @brief On the Raspberry Pi, it is important to call this method to
               properly close the pigpio object in software mode.
        """
        if self.__open:
            if isPico():
                try:
                    self.__i2cObj.deinit()
                except AttributeError:
                    pass
            else:
                if self.__mode == self.SOFTWARE_MODE:
                    try:
                        self.__i2cObj.bb_i2c_close( self.__sdaPin )
                    except:
                        pass
                    self.__i2cObj.stop()
                else:
                    self.__i2cObj.close()
            self.__open = False
        return


    def __setupRP( self ):
        """!
        @brief Private method to set up hardware of the Raspberry Pi as well as
        lambda functions to read from and write to an I<sup>2</sup>C bus.
        """

        # if bit banging buses are left open they cause problems
        # also for hardware I2C operations
        if not isPi5():
            import pigpio
            i2cObj = pigpio.pi()
            try:
                i2cObj.bb_i2c_close( 2 )
                i2cObj.stop()
            except Exception:
                pass

        if self.__mode == self.HARDWARE_MODE:
            # in hardware mode, use SMBus - prefer smbus2 over smbus
            try:
                from smbus2 import SMBus
            except ModuleNotFoundError:
                from smbus import SMBus

            if self.__sdaPin == 0 and self.__sclPin == 1:
                i2cBus = 0
            elif self.__sdaPin == 2 and self.__sclPin == 3:
                i2cBus = 1
            else:
                raise GPIOError( 'Wrong I2C Pins specified' )
            # SMBus's __init__() does an open() internally
            self.__i2cObj = SMBus( i2cBus )
            try:
                self.__i2cObj.enable_pec( self.__usePEC )
            except IOError:
                self.__usePEC = False
            # on Raspberry Pi in HW mode the frequency is fixed at 100 kHz
            self.__frequency = 100000

            # override the i2c duds with corresponding smbus methods
            # (they are 100 % compatible)
            self.__readByte = self.__i2cObj.read_byte
            self.__readByteReg = self.__i2cObj.read_byte_data
            self.__readBlockReg = self.__i2cObj.read_i2c_block_data
            self.__writeQuick = self.__i2cObj.write_quick
            self.__writeByte = self.__i2cObj.write_byte
            self.__writeByteReg = self.__i2cObj.write_byte_data
            self.__writeBlockReg = self.__i2cObj.write_i2c_block_data

        elif self.__mode == self.SOFTWARE_MODE:
            if isPi5():
                raise GPIOError( 'Software mode not yet implemented '
                                 'for RB Pi 5' )
            self.__i2cObj = pigpio.pi()
            if not self.__i2cObj.connected:
                raise GPIOError( 'Could not connect to GPIO' )
            try:
                # in case somebody didn't close it properly...
                self.__i2cObj.bb_i2c_close( self.__sdaPin )
            except:
                pass

            # bb_i2c_zip commands:
            END = 0
            START = 2
            RESTART = 2
            STOP = 3
            ADDRESS = 4
            READ = 6
            WRITE = 7

            try:
                if self.__i2cObj.bb_i2c_open( self.__sdaPin,
                                              self.__sclPin,
                                              self.__frequency ) != 0:
                    raise GPIOError( 'Opening Software I2C failed' )
                self.__usePEC = False
            except Exception as e:
                raise GPIOError( str( e ) )

            # override the i2c duds with corresponding bb_i2c_zip calls
            self.__readByte = \
                (lambda addr: list(
                    self.__i2cObj.bb_i2c_zip(
                        self.__sdaPin,
                        [START,
                         ADDRESS, addr,
                         READ, 1,
                         STOP,
                         END] )[1] )[0])
            self.__readByteReg = \
                (lambda addr, reg: list(
                    self.__i2cObj.bb_i2c_zip(
                        self.__sdaPin,
                        [START,
                         ADDRESS, addr,
                         WRITE, 1, reg,
                         RESTART,
                         ADDRESS, addr,
                         READ, 1,
                         STOP,
                         END] )[1] )[0])
            self.__readBlockReg = \
                (lambda addr, reg, length: list(
                    self.__i2cObj.bb_i2c_zip(
                        self.__sdaPin,
                        [START,
                         ADDRESS, addr,
                         WRITE, 1, reg,
                         RESTART,
                         ADDRESS, addr,
                         READ, length,
                         STOP,
                         END] )[1] ))
            # the following does not work as it does not throw an exception
            # when no acknowledge is sent
            self.__writeQuick = \
                (lambda addr: self.__i2cObj.bb_i2c_zip(
                    self.__sdaPin,
                    [START,
                     ADDRESS, addr,
                     WRITE, 0,
                     STOP,
                     END] ))
            self.__writeByte = \
                (lambda addr, value: self.__i2cObj.bb_i2c_zip(
                    self.__sdaPin,
                    [START,
                     ADDRESS, addr,
                     WRITE, 1, value,
                     STOP,
                     END] ))
            self.__writeByteReg = \
                (lambda addr, reg, value: self.__i2cObj.bb_i2c_zip(
                    self.__sdaPin,
                    [START,
                     ADDRESS, addr,
                     WRITE, 2, reg, value,
                     STOP,
                     END] ))
            self.__writeBlockReg = \
                (lambda addr, reg, data: self.__i2cObj.bb_i2c_zip(
                    self.__sdaPin,
                    [START,
                     ADDRESS, addr,
                     WRITE, 1 + len( data ), reg] + data +
                    [STOP,
                     END] ))
        else:
            raise GPIOError( 'Wrong I2Cbus mode specified: '
                             '{0}'.format( self.__mode ) )

        return


    def __setupRPPico( self ):
        """!
        @brief Private method to set up hardware of the Raspberry Pi Pico as
               well as lambda functions to read from and write to an
               I<sup>2</sup>C bus.
        """

        self.__usePEC = False

        if self.__mode == self.SOFTWARE_MODE:
            self.__i2cObj = machine.SoftI2C(
                sda=machine.Pin( self.__sdaPin ),
                scl=machine.Pin( self.__sclPin ),
                freq=self.__frequency )
        elif self.__mode == self.HARDWARE_MODE:
            if self.__sclPin == 3 or self.__sclPin == 7 or \
               self.__sclPin == 11 or self.__sclPin == 15 or \
               self.__sclPin == 19 or self.__sclPin == 27:
                i2cId = 1
            else:
                # Error checking is provided by the machine.I2C constructor
                # so we just default to 0 for all other Pins
                i2cId = 0
            self.__i2cObj = machine.I2C( i2cId,
                                         sda=machine.Pin( self.__sdaPin ),
                                         scl=machine.Pin( self.__sclPin ),
                                         freq=self.__frequency )
        else:
            raise GPIOError( 'Wrong mode specified: '
                             '{0}'.format( self.__mode ) )

        self.__readByte = \
            (lambda addr, reg:
                 list( self.__i2cObj.readfrom( addr, 1 ) )[0])
        self.__readByteReg = \
            (lambda addr, reg:
                 list( self.__i2cObj.readfrom_mem( addr, reg, 1 ) )[0])
        self.__readBlockReg = \
            (lambda addr, reg, count:
                 list( self.__i2cObj.readfrom_mem( addr,reg, count ) ))
        self.__writeQuick = \
            (lambda addr:
             self.__i2cObj.writeto( addr, bytearray( [] ) ))
        self.__writeByte = \
            (lambda addr, value:
             self.__i2cObj.writeto( addr, bytearray( [value] ) ))
        self.__writeByteReg = \
            (lambda addr, reg, value:
             self.__i2cObj.writeto_mem( addr, reg, bytearray( [value] ) ))
        self.__writeBlockReg = \
            (lambda addr, reg, data:
                self.__i2cObj.writeto_mem( addr, reg, bytearray( data ) ))

        return


    def __readId( self, i2cAddress ):
        """!
        @brief Read manufacturer ID, part ID and die revision if supplied.
        @param i2cAddress address of device to probe
        @return tuple with manufacturer ID, device ID and die revision
        @throws exception if device does not reply
        """
        try:
            self.__i2cObj.write_quick( 0x7C )
        except Exception as e:
            # no acknowledge bit causes exception
            pass
        byteList = self.__readBlockReg( i2cAddress, 0x7C, 3 )

        manufacturerId = byteList[1] >> 4 | byteList[1] >> 4
        deviceId = (byteList[1] & 0x0F) << 5 | (byteList[2] & 0xF8) >> 3
        dieRev = byteList[2] & 0x07
        return manufacturerId, deviceId, dieRev


    @property
    def attempts( self ):
        """!
        @brief Obtain the user-supplied number of communication attempts.
        """
        return self.__attempts


    def clearFailedAttempts( self ):
        """!
        @brief Clear the number of internally recorded failed attempts.
        """
        self.__failedAttempts = 0
        return


    @property
    def failedAttempts( self ):
        """!
        @brief Works as read-only property to obtain the number of internally
               recorded failed attempts.
        """
        return self.__failedAttempts


    @property
    def frequency( self ):
        """!
        @brief Works as read-only property to get the frequency the
               I<sup>2</sup>C bus is operating at in Hz.
        """
        return self.__frequency


    @property
    def mode( self ):
        """!
        @brief Works as read-only property to get the I<sup>2</sup>C bus mode
               (I2Cbus.SOFTWARE_MODE or I2Cbus.HARDWARE_MODE).
        """
        return self.__mode


    @property
    def usePEC( self ):
        """!
        @brief Return current status of Packet Error Checking.
        """
        return self.__usePEC


    @usePEC.setter
    def usePEC( self, flag ):
        """!
        @brief Setter for usePEC (Packet Error Checking) property.

        If the I<sup>2</sup>C bus does not support PEC, the method does nothing
        and ignores the request silently.
        @param flag boolean flag to set or unset PEC.
        """
        try:
            self.__i2cObj.enable_pec( flag )
            self.__usePEC = flag
        except:
            self.__usePEC = False
        return


    @property
    def sda( self ):
        """!
        @brief Works as read-only property to get the sda Pin number.
        """
        return self.__sdaPin


    @property
    def scl( self ):
        """!
        @brief Works as read-only property to get the scl Pin number.
        """
        return self.__sclPin


    # The following methods are wrappers around the internal methods allowing
    # for multiple attempts in case of errors, which proved necessary on the
    # Raspberry Pi 3

    def readByte( self, i2cAddress ):
        """!
        @brief Read a single general byte from an I<sup>2</sup>C device.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @return int with byte read
        """
        count = 0
        while count < self.__attempts:
            try:
                return self.__readByte( i2cAddress )
            except Exception as e:
                count += 1
                self.__failedAttempts += 1
                lastException = e
        raise GPIOError( 'exceeded {0} attempts '.format( self.__attempts )
                         + 'in readByte ({0})'.format( lastException ) )


    def readByteReg( self, i2cAddress, register ):
        """!
        @brief Read a single byte from an I<sup>2</sup>C device register.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @param register device register to read from
        @return int with byte read
        """
        count = 0
        while count < self.__attempts:
            try:
                return self.__readByteReg( i2cAddress, register )
            except Exception as e:
                count += 1
                self.__failedAttempts += 1
                lastException = e
        raise GPIOError( 'exceeded {0} attempts '.format( self.__attempts )
                         + 'in readByteReg ({0})'.format( lastException ) )


    def readBlockReg( self, i2cAddress, register, length ):
        """!
        @brief Read a block of bytes from an I<sup>2</sup>C device register.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @param register device register to start reading
        @param length number of bytes to be read
        @return list of ints with bytes read
        """
        count = 0
        while count < self.__attempts:
            try:
                return self.__readBlockReg( i2cAddress, register,  length )
            except Exception as e:
                count += 1
                self.__failedAttempts += 1
                lastException = e
        raise GPIOError( 'exceeded {0} attempts '.format( self.__attempts )
                         + 'in readBlockReg ({0})'.format( lastException ) )


    def writeQuick( self, i2cAddress ):
        """!
        @brief Issue an I<sup>2</sup>C  device address with the write bit set
        and check the acknowledge signal but do not write anything else.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        """
        count = 0
        while count < self.__attempts:
            try:
                self.__writeQuick( i2cAddress )
                return
            except Exception as e:
                count += 1
                self.__failedAttempts += 1
                lastException = e
        raise GPIOError( 'exceeded {0} attempts '.format( self.__attempts )
                         + 'in writeQuick ({0})'.format( lastException ) )


    def writeByte( self, i2cAddress, value ):
        """!
        @brief Write a single byte to an I<sup>2</sup>C device.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param value value of byte to be written as an int
        """
        count = 0
        while count < self.__attempts:
            try:
                self.__writeByte( i2cAddress, value )
                return
            except Exception as e:
                count += 1
                self.__failedAttempts += 1
                lastException = e
        raise GPIOError( 'exceeded {0} attempts '.format( self.__attempts )
                         + 'in writeByte ({0})'.format( lastException ) )


    def writeByteReg( self, i2cAddress, register, value ):
        """!
        @brief Write a single byte to an I<sup>2</sup>C device register.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param register device register to start reading
        @param value value of byte to be written as an int
        """
        count = 0
        while count < self.__attempts:
            try:
                self.__writeByteReg( i2cAddress, register, value )
                return
            except Exception as e:
                count += 1
                self.__failedAttempts += 1
                lastException = e
        raise GPIOError( 'exceeded {0} attempts '.format( self.__attempts )
                         + 'in writeByteReg ({0})'.format( lastException ) )


    def writeBlockReg( self, i2cAddress, register, block ):
        """!
        @brief Write a block of bytes to an I<sup>2</sup>C device starting at
               register.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param register device register to start reading
        @param block list of ints with bytes to be written
        """
        count = 0
        while count < self.__attempts:
            try:
                self.__writeBlockReg( i2cAddress, register, block )
                return
            except Exception as e:
                count += 1
                self.__failedAttempts += 1
                lastException = e
        raise GPIOError( 'exceeded {0} attempts '.format( self.__attempts )
                         + 'in writeBlockReg ({0})'.format( lastException ) )


    @property
    def funcs( self ):
        """!
        @brief Obtain the functionality supported by this I<sup>2</sup>C bus.

        If the I<sup>2</sup>C does not support this property, the method
        returns 0.
        """
        try:
            return self.__i2cObj.funcs
        except AttributeError:
            return 0


    def readId( self, i2cAddress ):
        """!
        @brief Read the ID of a device.
        @param i2cAddress address of I<sup>2</sup>C device to read ID from
        """
        count = 0
        while count < self.__attempts:
            try:
                manufacturerId, idBits, dieRev = self.__readId( i2cAddress )
                return manufacturerId, idBits, dieRev
            except Exception as e:
                count += 1
                self.__failedAttempts += 1
                lastException = e
        raise GPIOError( 'exceeded {0} attempts '.format( self.__attempts )
                         + 'in readId ({0})'.format( lastException ) )
