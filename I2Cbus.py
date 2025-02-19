# Python Implementation: I2Cbus
# -*- coding: utf-8 -*-
##
# @file       I2Cbus.py
#
# @version    2.0.0
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
#   Mon Jan 27 2025 | Ekkehard Blanz | split into _I2CbusAPI.py, I2Cbus.py.
#                   |                | _PiI2Cbus.py, and _PicoI2Cbus.py
#                   |                |
#

from GPIO_AL.tools import isPico, isPi5, isHWI2CPinPair
from GPIO_AL.GPIOError import GPIOError
from GPIO_AL._I2CbusAPI import _I2CbusAPI
if not isPico():
    from typing import Union



class I2Cbus( _I2CbusAPI ):
    """!
    @brief Class to handle I<sup>2</sup>C bus communication.

    The GPIO Pins on the Raspberry Pi are GPIO2 for I<sup>2</sup>C data and
    GPIO3 for I<sup>2</sup>C clock for hardware I<sup>2</sup>C and freely
    selectable for software I<sup>2</sup>C (bit banging); on the Raspberry Pi
    Pico, the GPIO Pins for I<sup>2</sup>C communication are also freely
    selectable under software I<sup>2</sup>C, they are restricted to GPIO1 for
    data and GPIO2 for clock, GPIO4 for data and GPIO5 for clock, GPIO6
    for data and GPIO7 for clock, GPIO9 for data and GPIO10 for clock,
    GPIO11 for data and GPIO12 for clock, GPIO14 for data and GPIO15 for
    clock, GPIO16 for data and GPIO17 for clock, GPIO19 for data and GPIO20 for
    clock, GPIO21 for data and GPIO22 for clock, GPIO24 for data and GPIO25 for
    clock, GPIO26 for data and GPIO27 for clock, or GPIO31 for data and GPIO32
    for clock.

    Since many targets can be connected on an I<sup>2</sup>C bus, one I2Cbus
    object must be able to handle them all.  Therefore, I2Cbus objects are
    created one per I<sup>2</sup>C bus, which is uniquely defined by the sda
    and scl Pins - NOT one such object per target device on that bus.  Every
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

    Also, on Raspberry Pi systems other than the Raspberry Pi 5 running under 
    an operating system, the pigpiod daemon needs to run to use the software 
    mode, which is strongly recommended on Raspberry Pis other than Raspberry 
    Pi 5 (see below).  Either use
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
    between different systems.  This is because either the Broadcom BCM2835 
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
    
    ## Operating mode either Mode.HARDWARE or Mode.SOFTWARE as Enum
    Mode = _I2CbusAPI._Mode
    
    def __init__( self, *args, **kwargs ):
        """!
        @brief Constructor for class I2Cbus.
        @param sdaPin header pin or GPIO line number for I<sup>2</sup>C data 
               (default GPIO2 on Raspberry Pi and 8 on Raspberry Pi Pico).
               Ints are interpreted as header header pin numbers, strings 
               starting with GPIO on the Raspberry Pi and GP on the Pico as line
               numbers.
        @param sclPin header pin or GPIO line number for I<sup>2</sup>C clock 
               (default GPIO3 on Raspberry Pi and 9 on Raspberry Pi Pico).
               Ints are interpreted as header header pin numbers, strings 
               starting with GPIO on the Raspberry Pi and GP on the Pico as line
               numbers.
        @param mode one of I2Cbus.Mode.HARDWARE or I2Cbus.Mode.SOFTWARE
               AKA bit banging (default I2Cbus.Mode.SOFTWARE for Raspberry Pi 
               other than Raspberry Pi 5 and I2Cbus.Mode.HARDWARE for Raspberry 
               Pi Pico)
        @param frequency I<sup>2</sup>C frequency in Hz (default 75 kHz for
               Software mode and 100 kHz for hardware mode and Raspberry Pi 
               Pico in all modes).  This parameter is ignored for Raspberry Pis 
               in hardware mode, where the frequency is always 100 kHz.
               Also accepts PObjects of Unit Hz.
        @param attempts number of read or write attempts before throwing an
               exception (default 1 for Pico in all modes and 5 for all Pis in 
               software mode)
        @param usePEC set True to use Packet Error Checking (default False).
               This parameter is ignored when PEC is not supported.
        @throws GPIOException in case of parameter error
        """

        self.__actor = None
        
        if isPico():
            from _I2CbusPico import _I2CbusPico
            self.__actor = _I2CbusPico( *args, **kwargs )
        else:
            # for RB Pis we must get or infer mode as we'll call specific actors
            if len( args ) > 2:
                mode = args[2]
            else:
                try:
                    mode = kwargs['mode']
                except KeyError:
                    # mode is not given in parameters - check Pins
                    sda = None
                    scl = None
                    if len( args ) > 1:
                        sda = args[0]
                        scl = args[1]
                    else:
                        try:
                            sda = kwargs['sdaPin']
                            scl = kwargs['sclPin']
                        except KeyError:
                            pass
                    # if pins are not given they default to HW pins
                    hwPins = (sda is None and scl is None) or \
                             isHWI2CPinPair( sda, scl )
                    if hwPins and isPi5():
                        mode = self.Mode.HARDWARE
                    else:
                        # RB Pis other than Pi 5 default to software mode
                        mode = self.Mode.SOFTWARE
            if not isinstance( mode, self.Mode ):
                raise GPIOError( 'Wrong mode specified: {0}'.format( mode ) )
            if mode == self.Mode.SOFTWARE:
                from GPIO_AL._I2CbusPi import _I2CPiSW
                self.__actor = _I2CPiSW( *args, **kwargs )
            else:
                from GPIO_AL._I2CbusPi import _I2CPiHW
                self.__actor = _I2CPiHW( *args, **kwargs )
        self.__failedAttempts = 0
        return

    def __del__( self ):
        """!
        @brief Destructor.
        Also closes the software I<sup>2</sup>C bus on the Raspberry Pi.
        """
        self.close()
        if self.__actor:
            del self.__actor
            self.__actor = None
        return

    def  __enter__( self ):
        """!
        @brief Enter method for context management.
        @return an object that is used in the "as" construct, here it is self
        """
        return self

    def __exit__( self, excType, excValue, excTraceback ):
        """!
        @brief Exit method for context management.
        @param excType type of exception ending the context
        @param excValue value of the exception ending the context
        @param excTraceback traceback of exception ending the context
        @return False (will re-raise the exception)
        """
        self.close()
        return False
        
    def close( self ):
        """!
        @brief On the Raspberry Pi, it is important to call this method to 
               properly close the pigpio object in software mode.
        """
        # In case of an emergency stop, the actor may not even exist (anymore)
        if self.__actor: self.__actor.close()
        return

    def readId( self, i2cAddress: int ) -> tuple:
        """!
        @brief Read the ID tuple of a device consisting of manufacturer ID,
               device ID, and die revision.
        @param i2cAddress address of I<sup>2</sup>C device to read ID from
        @return tuple of (manufacturerId, deviceId, dieRev)
        @throws GPIOError in case of an error
        """
        count = 0
        while count < self.__actor.attempts:
            try:
                self.__actor.readId( i2cAddress )
            except Exception as e:
                count += 1
                self.__failedAttempts += 1
                lastException = e
        raise GPIOError( 'exceeded {0} attempts '.format( self.__actor.attempts )
                         + 'in readId ({0})'.format( lastException ) )

    def readByte( self, i2cAddress: int ) -> int:
        """!
        @brief Read a single general byte from an I<sup>2</sup>C device.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @return byte read as an int
        @throws GPIOError in case of an error
        """
        count = 0
        while count < self.__actor.attempts:
            try:
                return self.__actor.readByte( i2cAddress )
            except Exception as e:
                count += 1
                self.__failedAttempts += 1
                lastException = e
        raise GPIOError( 'exceeded {0} attempts '.format( self.__actor.attempts )
                         + 'in readByte ({0})'.format( lastException ) )
        
    def readByteReg( self, i2cAddress: int, register: int ) -> int:
        """!
        @brief Read a single byte from an I<sup>2</sup>C device register.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @param register device register to read from
        @return byte read as an int
        @throws GPIOError in case of an error
        """
        count = 0
        while count < self.__actor.attempts:
            try:
                return self.__actor.readByteReg( i2cAddress, register )
            except Exception as e:
                count += 1
                self.__failedAttempts += 1
                lastException = e
        raise GPIOError( 'exceeded {0} attempts '.format( self.__actor.attempts )
                         + 'in readByte ({0})'.format( lastException ) )
        

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
        @throws GPIOError in case of an error
        """
        count = 0
        while count < self.__actor.attempts:
            try:
                return self.__actor.readBlockReg( i2cAddress,
                                                  register,
                                                  length )
            except Exception as e:
                count += 1
                self.__failedAttempts += 1
                lastException = e
        raise GPIOError( 'exceeded {0} attempts '.format( self.__actor.attempts )
                         + 'in readByte ({0})'.format( lastException ) )
        

    def writeQuick( self, i2cAddress: int ):
        """!
        @brief Issue an I<sup>2</sup>C device address with the write bit set
               and check the acknowledge signal but do not write anything else.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @throws GPIOError in case of an error
        """
        count = 0
        while count < self.__actor.attempts:
            try:
                self.__actor.writeQuick( i2cAddress )
                return
            except Exception as e:
                count += 1
                self.__failedAttempts += 1
                lastException = e
        raise GPIOError( 'exceeded {0} attempts '.format( self.__actor.attempts )
                         + 'in readByte ({0})'.format( lastException ) )

    def writeByte( self, i2cAddress: int, value: int ):
        """!
        @brief Write a single byte to an I<sup>2</sup>C device.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param value value of byte to be written as an int
        @throws GPIOError in case of an error
        """
        count = 0
        while count < self.__actor.attempts:
            try:
                self.__actor.writeByte( i2cAddress, value )
                return
            except Exception as e:
                count += 1
                self.__failedAttempts += 1
                lastException = e
        raise GPIOError( 'exceeded {0} attempts '.format( self.__actor.attempts )
                         + 'in readByte ({0})'.format( lastException ) )

    def writeByteReg( self, i2cAddress: int, register: int, value: int ):
        """!
        @brief Write a single byte to an I<sup>2</sup>C device register.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param register device register to write to
        @param value value of byte to be written as an int
        @throws GPIOError in case of an error
        """
        count = 0
        while count < self.__actor.attempts:
            try:
                self.__actor.writeByteReg( i2cAddress, register, value )
                return
            except Exception as e:
                count += 1
                self.__failedAttempts += 1
                lastException = e
        raise GPIOError( 'exceeded {0} attempts '.format( self.__actor.attempts )
                         + 'in readByte ({0})'.format( lastException ) )
        
    def writeBlockReg( self, i2cAddress: int, register: int, block: list ):
        """!
        @brief Write a block of bytes to an I<sup>2</sup>C device starting at
               register.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param register device register to start writing
        @param block list of ints with bytes to be written
        @throws GPIOError in case of an error
        """
        count = 0
        while count < self.__actor.attempts:
            try:
                self.__actor.writeBlockReg( i2cAddress, register, block )
                return
            except Exception as e:
                count += 1
                self.__failedAttempts += 1
                lastException = e
        raise GPIOError( 'exceeded {0} attempts '.format( self.__actor.attempts )
                         + 'in readByte ({0})'.format( lastException ) )

    @property
    def sda( self ) -> int:
        """!
        @brief Works as read-only property to get the sda line number.
        """
        return self.__actor.sda

    @property
    def scl( self ) -> int:
        """!
        @brief Works as read-only property to get the scl line number.
        """
        return self.__actor.scl

    @property
    def mode( self ) -> Mode:
        """!
        @brief Works as read-only property to get the I<sup>2</sup>C bus mode
               (I2Cbus.Mode.SOFTWARE or I2Cbus.Mode.HARDWARE).
        """
        return self.__actor.mode

    @property
    def frequency( self ) -> Union[float, object]:
        """!
        @brief Works as read-only property to get the frequency the
               I<sup>2</sup>C bus is operating at.
        """
        return self.__actor.frequency

    @property
    def attempts( self ) -> int:
        """!
        @brief Obtain the user-supplied number of communication attempts.
        """
        return self.__actor.attempts

    @property
    def usePEC( self ) -> bool:
        """!
        @brief Return current status of Packet Error Checking.
        """
        return self.__actor.usePEC
    
    def clearFailedAttempts( self ):
        """!
        @brief Clear the number of internally recorded failed attempts.
        """
        self.__failedAttempts = 0
        return

    @property
    def failedAttempts( self ) -> int:
        """!
        @brief Works as read-only property to obtain the number of internally
               recorded failed attempts.
        """
        return self.__failedAttempts


if "__main__" == __name__:
    import sys
    
    def main() -> int:
        """!
        @brief No unit test - coarse Python syntax test only.
        """
        
        b1 = I2Cbus( 'GPIO2', 'GPIO3' )
        print( b1 )
        del b1
                
        try:
            b2 = I2Cbus( 'GPIO2', 'GPIO3', I2Cbus.Mode.SOFTWARE )
            print( b2 )
            del b2
        except GPIOError as e:
            # on Pi 5 software mode may not yet be implemented
            if isPi5():
                print( 'Software mode could not be tested on RB Pi 5' )
            else:
                raise e
        
        print( '\nSUCCESS: no Python syntax errors detected\n' )
        
        return 0

    sys.exit( int( main() or 0 ) )

