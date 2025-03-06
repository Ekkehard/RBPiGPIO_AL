# Python Implementation: I2C
# -*- coding: utf-8 -*-
##
# @file       I2C.py
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
#   Mon Mar 03 2025 | Ekkehard Blanz | renamed into I2C.py _I2CAPI.py,
#                   |                | _I2PicoHW.py, _I2CPicoSW.py,
#                   |                | _I2CPiHW.py, and _I2CPiSW.py
#   Wed Mar 05 2025 | Ekkehard Blanz | added warning to documentation
#                   |                |
#

from GPIO_AL.tools import isPico, isPi5, isHWI2CPinPair, argToPin
from GPIO_AL.GPIOError import GPIOError
from GPIO_AL._I2CAPI import _I2CAPI
if not isPico():
    from typing import Union, Optional



class I2C( _I2CAPI ):
    """!
    @brief Class to handle I<sup>2</sup>C bus communication.
    
    I<sup>2</sup>C bus communication is a sore point on the Raspberry Pi.  This 
    is because on Raspberries other than the RB Pi 5 and Pico it just doesn't 
    work!  The reason is the Broadcom BCM2835 chip, which Raspberry Pis 0, 3, 
    and 4 use for hardware I<sup>2</sup>C.  It is broken and does not correctly 
    support clock stretching.  This is fixed on the Raspberry Pi 5; the Pico 
    never was plagued by this.  The remedy usually applied is to use 
    "bit-banging," i.e. software-controlled pulses for I<sup>2</sup>C 
    communication.  Unfortunately, software-controlled pulses are not very 
    stable and cannot operate at the speeds that most I<sup>2</sup>C devices 
    expect the pulses to be delivered.  Moreover, the pigpio software used for 
    bit banging appears to be less than robust and sometimes results in 
    Exceptions due to accessing elements of None-type objects.  Therefore, also 
    I<sup>2</sup>C in software mode does not work very reliably and not at all 
    on the Raspberry Pi 5.  If I<sup>2</sup>C bus communication is a 
    requirement, the user is strongly advised to use a Raspberry Pi Pico or a 
    Raspberry Pi 5 or higher.  For more details and implication on this software 
    see below. 

    The GPIO Pins on the Raspberry Pi are GPIO2 for I<sup>2</sup>C data and
    GPIO3 for I<sup>2</sup>C clock for hardware I<sup>2</sup>C and freely
    selectable for software I<sup>2</sup>C (bit banging); on the Raspberry Pi
    Pico, the GPIO Pins for I<sup>2</sup>C communication are also freely
    selectable under software I<sup>2</sup>C, they are restricted to GP1 for
    data and GP2 for clock, GP4 for data and GP5 for clock, GP6
    for data and GP7 for clock, GP9 for data and GP10 for clock,
    GP11 for data and GP12 for clock, GP14 for data and GP15 for
    clock, GP16 for data and GP17 for clock, GP19 for data and GP20 for
    clock, GP21 for data and GP22 for clock, GP24 for data and GP25 for
    clock, GP26 for data and GP27 for clock, or GP31 for data and GP32
    for clock.

    Since many targets can be connected on an I<sup>2</sup>C bus, one I2C
    object must be able to handle them all.  Therefore, I2C objects are
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
    Pi 5 (see above).  Either use
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

    It is worth noting that because of the problems with the Broadcom BCM2835 
    chip mentioned above, the defaults for the operating mode are different for 
    different systems.  The problems with that chip were found through
    experimentation and measurements and also confirmed online at
    https://www.advamation.com/knowhow/raspberrypi/rpi-i2c-bug.html.  The pigpio
    software mode supports clock stretching properly on the Raspberry Pi 0, 3, 
    and 4, but pigpio is broken on the Raspberry Pi 5.  Therefore, software
    mode is not supported on the Raspberry Pi 5.  Naturally, even when 
    supported, the software-generated I<sup>2</sup>C clock on a non-real-time OS 
    is not very consistent, but targets will tolerate a non-consistent clock 
    better, albeit not always completely, than a broken clock-stretch mechanism 
    when they need it.  Therefore, the default operating mode on a Raspberry Pi 
    0, 3, and 4 is software, but since other systems work just fine with 
    hardware I<sup>2</sup>C, the default operating mode there is hardware to 
    free the CPU from the task of generating I<sup>2</sup>C signals.  This 
    software still allows the caller to select hardware mode also on the 
    Raspberry Pi 0, 3, and 4, but the user is strongly advised to make sure that 
    no target on the I<sup>2</sup>C bus requires clock stretching in such cases.
    Moreover, the user is much more likely to run into error conditions on a 
    Raspberry Pi 0, 3, and 4 I<sup>2</sup>C bus than on any other system, and it 
    is a very good idea to write "robust" code that checks error conditions 
    continuously and deals with them appropriately on a Raspberry Pi other than 
    5 (and above) and Pico, even in software mode.
    """
    
    ## Operating mode either Mode.HARDWARE or Mode.SOFTWARE as Enum
    Mode = _I2CAPI._Mode
    
    def __init__( self,
                  sdaPin: Optional[Union[int, str]]=None,
                  sclPin: Optional[Union[int, str]]=None,
                  mode: Optional[Mode]=None,
                  frequency: Optional[Union[float, object]]=None,
                  attempts: int=3,
                  usePEC: bool=False ):
        """!
        @brief Constructor for class I2C.
        @param sdaPin header pin number or GP(IO) line string for I<sup>2</sup>C 
               data (default GPIO2 on Raspberry Pi and 8 on Raspberry Pi Pico).
               Ints are interpreted as header or board pin numbers, strings 
               starting with GPIO on the Raspberry Pi and GP on the Pico as line
               numbers.
        @param sclPin header pin number or GP(IO) line string for I<sup>2</sup>C 
               clock  (default GPIO3 on Raspberry Pi and 9 on Raspberry Pi Pico).
               Ints are interpreted as header or board pin numbers, strings 
               starting with GPIO on the Raspberry Pi and GP on the Pico as line
               numbers.
        @param mode one of I2C.Mode.HARDWARE or I2C.Mode.SOFTWARE
               AKA bit banging (default I2C.Mode.SOFTWARE for Raspberry Pi 
               other than Raspberry Pi 5 and I2C.Mode.HARDWARE for Raspberry 
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

        if isPico():
            if sdaPin is None:
                sdaPin = 1
            if sclPin is None:
                sclPin = argToPin( sdaPin ) + 1
            if mode is None:
                if isHWI2CPinPair( sdaPin, sclPin ):
                    mode = self.Mode.HARDWARE # type: ignore
                else:
                    mode = self.Mode.SOFTWARE # type: ignore
            if frequency is None:
                frequency = 100000.0
        else:
            if sdaPin is None:
                sdaPin = 3
            if sclPin is None:
                sclPin = argToPin( sdaPin ) + 2
            if mode is None:
                if isHWI2CPinPair( sdaPin, sclPin ):
                    mode = self.Mode.HARDWARE # type: ignore
                else:
                    mode = self.Mode.SOFTWARE # type: ignore
            if frequency is None:
                if mode == self.Mode.SOFTWARE:
                    frequency = 75000.0
                else:
                    frequency = 100000.0
        self.__actor = None
        # for RB Pis we must get or infer mode as we'll call specific actors
     
        if not isinstance( mode, self.Mode ):
            raise GPIOError( 'Wrong mode specified: {0}'.format( mode ) )
        if mode == self.Mode.SOFTWARE:
            if isPico():
                from GPIO_AL._I2CPicoSW import _I2CPicoSW
                self.__actor = _I2CPicoSW( sdaPin,
                                           sclPin,
                                           mode,
                                           frequency,
                                           attempts,
                                           usePEC  )
            else:
                from GPIO_AL._I2CPiSW import _I2CPiSW
                self.__actor = _I2CPiSW( sdaPin,
                                         sclPin,
                                         mode,
                                         frequency,
                                         attempts,
                                         usePEC )
        else:
            if not isHWI2CPinPair( sdaPin, sclPin ):
                raise GPIOError( 'Wrong hardware I2C Pins specified' )
            if isPico():
                from GPIO_AL._I2CPicoHW import _I2CPicoHW
                self.__actor = _I2CPicoHW( sdaPin,
                                           sclPin,
                                           mode,
                                           frequency,
                                           attempts,
                                           usePEC )
            else:
                from GPIO_AL._I2CPiHW import _I2CPiHW
                self.__actor = _I2CPiHW( sdaPin,
                                         sclPin,
                                         mode,
                                         frequency,
                                         attempts,
                                         usePEC )
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
        if self.__actor is None:
            raise GPIOError( 'No I2C actor available' )
        count = 0
        lastException = 0
        while count < self.__actor.attempts:
            try:
                return self.__actor.readId( i2cAddress )
            except Exception as e:
                count += 1
                self.__failedAttempts += 1
                lastException = e
        raise GPIOError( 'exceeded {0} attempts '.format( self.__actor.attempts )
                         + 'in readId( {0} ) ({1})'
                           .format( i2cAddress, lastException ) )

    def readByte( self, i2cAddress: int ) -> int:
        """!
        @brief Read a single general byte from an I<sup>2</sup>C device.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @return byte read as an int
        @throws GPIOError in case of an error
        """
        if self.__actor is None:
            raise GPIOError( 'No I2C actor available' )
        count = 0
        lastException = 0
        while count < self.__actor.attempts:
            try:
                return int( self.__actor.readByte( i2cAddress ) )
            except Exception as e:
                count += 1
                self.__failedAttempts += 1
                lastException = e
        raise GPIOError( 'exceeded {0} attempts '
                         .format( self.__actor.attempts )
                         + 'in readByte( {0} ) ({1})'
                           .format( i2cAddress, lastException ) )
        
    def readByteReg( self, i2cAddress: int, register: int ) -> int:
        """!
        @brief Read a single byte from an I<sup>2</sup>C device register.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @param register device register to read from
        @return byte read as an int
        @throws GPIOError in case of an error
        """
        if self.__actor is None:
            raise GPIOError( 'No I2C actor available' )
        count = 0
        lastException = 0
        while count < self.__actor.attempts:
            try:
                return int( self.__actor.readByteReg( i2cAddress, register ) )
            except Exception as e:
                count += 1
                self.__failedAttempts += 1
                lastException = e
        raise GPIOError( 'exceeded {0} attempts '.format( self.__actor.attempts )
                         + 
                         'in readByteReg( {0}, {1} ) ({2})'
                         .format( i2cAddress, register, lastException ) )
        

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
        if self.__actor is None:
            raise GPIOError( 'No I2C actor available' )
        count = 0
        lastException = 0
        while count < self.__actor.attempts:
            try:
                return self.__actor.readBlockReg( i2cAddress,
                                                  register,
                                                  length ) # type: ignore
            except Exception as e:
                count += 1
                self.__failedAttempts += 1
                lastException = e
        raise GPIOError( 'exceeded {0} attempts '.format( self.__actor.attempts )
                         + 'in readBlockReg( {0}, {1}, {2} ) ({3})'
                           .format( i2cAddress, 
                                    register, 
                                    length, 
                                    lastException ) )
        

    def writeQuick( self, i2cAddress: int ):
        """!
        @brief Issue an I<sup>2</sup>C device address with the write bit set
               and check the acknowledge signal but do not write anything else.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @throws GPIOError in case of an error
        """
        if self.__actor is None:
            raise GPIOError( 'No I2C actor available' )
        count = 0
        lastException = 0
        while count < self.__actor.attempts:
            try:
                self.__actor.writeQuick( i2cAddress )
                return
            except Exception as e:
                count += 1
                self.__failedAttempts += 1
                lastException = e
        raise GPIOError( 'exceeded {0} attempts '
                         .format( self.__actor.attempts )
                         + 'in writeQuick( {0} ) ({1})'
                           .format( i2cAddress, lastException ) )

    def writeByte( self, i2cAddress: int, value: int ):
        """!
        @brief Write a single byte to an I<sup>2</sup>C device.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param value value of byte to be written as an int
        @throws GPIOError in case of an error
        """
        if self.__actor is None:
            raise GPIOError( 'No I2C actor available' )
        count = 0
        lastException = 0
        while count < self.__actor.attempts:
            try:
                self.__actor.writeByte( i2cAddress, value )
                return
            except Exception as e:
                count += 1
                self.__failedAttempts += 1
                lastException = e
        raise GPIOError( 'exceeded {0} attempts '.format( self.__actor.attempts )
                         + 'in writeByte( {0}, {1} ) ({2})'
                           .format( i2cAddress, value, lastException ) )

    def writeByteReg( self, i2cAddress: int, register: int, value: int ):
        """!
        @brief Write a single byte to an I<sup>2</sup>C device register.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param register device register to write to
        @param value value of byte to be written as an int
        @throws GPIOError in case of an error
        """
        if self.__actor is None:
            raise GPIOError( 'No I2C actor available' )
        count = 0
        lastException = 0
        while count < self.__actor.attempts:
            try:
                self.__actor.writeByteReg( i2cAddress, register, value )
                return
            except Exception as e:
                count += 1
                self.__failedAttempts += 1
                lastException = e
        raise GPIOError( 'exceeded {0} attempts '.format( self.__actor.attempts )
                         + 'in writeByteReg( {0}, {1}, {2} ) ({3})'
                           .format( i2cAddress, 
                                    register, 
                                    value, 
                                    lastException ) )
        
    def writeBlockReg( self, i2cAddress: int, register: int, block: list ):
        """!
        @brief Write a block of bytes to an I<sup>2</sup>C device starting at
               register.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param register device register to start writing
        @param block list of ints with bytes to be written
        @throws GPIOError in case of an error
        """
        if self.__actor is None:
            raise GPIOError( 'No I2C actor available' )
        count = 0
        lastException = 0
        while count < self.__actor.attempts:
            try:
                self.__actor.writeBlockReg( i2cAddress, register, block )
                return
            except Exception as e:
                count += 1
                self.__failedAttempts += 1
                lastException = e
        raise GPIOError( 'exceeded {0} attempts '.format( self.__actor.attempts )
                         + 'in writeBlockReg( {0}, {1}, {2} ) ({3})'
                           .format( i2cAddress,
                                    register,
                                    block,
                                    lastException ) )

    @property
    def sda( self ) -> str:
        """!
        @brief Works as read-only property to get the sda line number.
        """
        if self.__actor is None:
            raise GPIOError( 'No I2C actor available' )
        return self.__actor.sda

    @property
    def scl( self ) -> str:
        """!
        @brief Works as read-only property to get the scl line number.
        """
        if self.__actor is None:
            raise GPIOError( 'No I2C actor available' )
        return self.__actor.scl

    @property
    def mode( self ) -> Mode:
        """!
        @brief Works as read-only property to get the I<sup>2</sup>C bus mode
               (I2C.Mode.SOFTWARE or I2C.Mode.HARDWARE).
        """
        if self.__actor is None:
            raise GPIOError( 'No I2C actor available' )
        return self.__actor.mode

    @property
    def frequency( self ) -> Union[float, object]:
        """!
        @brief Works as read-only property to get the frequency the
               I<sup>2</sup>C bus is operating at.
        """
        if self.__actor is None:
            raise GPIOError( 'No I2C actor available' )
        return self.__actor.frequency

    @property
    def attempts( self ) -> int:
        """!
        @brief Obtain the user-supplied number of communication attempts.
        """
        if self.__actor is None:
            raise GPIOError( 'No I2C actor available' )
        return self.__actor.attempts

    @property
    def usePEC( self ) -> bool:
        """!
        @brief Return current status of Packet Error Checking.
        """
        if self.__actor is None:
            raise GPIOError( 'No I2C actor available' )
        return self.__actor.usePEC
    
    def clearFailedAttempts( self ):
        """!
        @brief Clear the number of internally recorded failed attempts.
        """
        if self.__actor is None:
            raise GPIOError( 'No I2C actor available' )
        self.__failedAttempts = 0
        return

    @property
    def failedAttempts( self ) -> int:
        """!
        @brief Works as read-only property to obtain the number of internally
               recorded failed attempts.
        """
        if self.__actor is None:
            raise GPIOError( 'No I2C actor available' )
        return self.__failedAttempts


if "__main__" == __name__:
    import sys
    
    def main() -> int:
        """!
        @brief No unit test - coarse Python syntax test only.
        """
        
        b1 = I2C( 'GPIO2', 'GPIO3' )
        print( b1 )
        del b1
                
        try:
            b2 = I2C( 'GPIO2', 'GPIO3', I2C.Mode.SOFTWARE )  # type: ignore
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

