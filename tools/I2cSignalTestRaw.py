# Python Implementation: QADPollTest
##
# @file       I2cSignalTestRaw.py
#
# @version    1.0.0
#
# @par Purpose
# This program is very similar to I2cSignalTest.py as it generates signals on
# the I2C bus suitable for Logic Analyzer investigation to analyze the
# performance of hardware I2C control on the Raspberry Pi.  Again, the CCS811
# sensor is thereby used as a test object but we do not rely on the CCS811 class
# but generate our own signals.  The difference to I2cSignalTest.py is that
# I2cSignalTestRaw.py uses primitive or raw ioctl calls instead of calls to the
# high-level GPIO_AL library, which uses calls to the smbus2 library internally.
# It also uses I2C hardware mode only.  This program can be used as a template
# for a C or C++ program to also call ioctl without the Python interface in
# between.  This code is only intended to run on systems with full fledged Linux
# operating systems, i.e. not on a Raspberry Pi Pico.
#
# @par Comments
# This is Python 3 code!  PEP 8 guidelines are decidedly NOT followed in some
# instances, and guidelines provided by "Coding Style Guidelines" a "Process
# Guidelines" document from WEB Design are used instead where the two differ,
# as the latter span several programming languages and are therefore applicable
# also for projects that require more than one programming language; it also
# provides consistency across hundreds of thousands of lines of legacy code.
# Doing so, ironically, is following PEP 8.
#
# @par Known Bugs
# None
#
# @author
# W. Ekkehard Blanz <Ekkehard.Blanz@gmail.com>
#
# @copyright
# Copyright 2022 W. Ekkehard Blanz
# See NOTICE.md and LICENSE.md files that come with this distribution.

# File history:
#
#      Date         | Author         | Modification
#  -----------------+----------------+------------------------------------------
#   Thu Jun 23 2022 | Ekkehard Blanz | created
#                   |                |

import sys
import os
import time
import struct
from fcntl import ioctl
from ctypes import c_int, c_uint8, c_char, POINTER, Structure, \
                   create_string_buffer
from smbus2 import SMBus


I2C_SLAVE = 0x0703
I2C_SMBUS = 0x0720
I2C_SMBUS_WRITE = 0
I2C_SMBUS_READ = 1
I2C_SMBUS_QUICK = 0
I2C_SMBUS_BYTE = 1
I2C_SMBUS_BYTE_DATA = 2
I2C_SMBUS_WORD_DATA = 3
I2C_SMBUS_PROC_CALL = 4
# This may not be supported by Pure-I2C drivers with SMBUS emulation, like those
# in RaspberryPi, OrangePi, etc :(
I2C_SMBUS_BLOCK_DATA = 5
# Like I2C_SMBUS_BLOCK_DATA, it isn't supported by Pure-I2C drivers either.
I2C_SMBUS_BLOCK_PROC_CALL = 7
I2C_SMBUS_I2C_BLOCK_DATA = 8
I2C_SMBUS_BLOCK_MAX = 32

LP_c_uint8 = POINTER(c_uint8)


class i2cSmbusMsg( Structure ):

    _fields_ = [
        ('read_write', c_char),
        ('command', c_uint8),
        ('size', c_int),
        ('data', LP_c_uint8)]

    __slots__ = [name for name,type in _fields_]


class SMBusRaw( object ):

    def __init__( self, bus=1 ):
        self.__fd = None
        self.__addr = None
        self.open( bus )
        return


    def open( self, bus ):
        if isinstance( bus, int ):
            filepath = '/dev/i2c-{}'.format( bus )
        elif isinstance( bus, str ):
            filepath = bus
        else:
            raise TypeError( 'Unexpected type(bus)={}'.format( type( bus ) ) )
        self.__fd = os.open( filepath, os.O_RDWR )
        self.__addr = None
        return


    def close( self ):
        try:
            os.close( self.__fd )
        except:
            pass
        self.__fd = None
        self.__addr = None
        return


    def __setAddr( self, addr, force ):
        if self.__addr != addr or force:
            ioctl( self.__fd, I2C_SLAVE, addr )
            self.__addr = addr
        return


    def write_byte( self, addr, value, force=None ):
        self.__setAddr( addr, force )
        dataPtr = LP_c_uint8( c_uint8() )
        msg = i2cSmbusMsg( read_write=I2C_SMBUS_WRITE,
                           command=value,
                           size=I2C_SMBUS_BYTE,
                           data=dataPtr )
        ioctl( self.__fd, I2C_SMBUS, msg )
        return


    def write_byte_data( self, addr, register, value, force=None ):
        """Write a single byte to a designated register."""
        self.__setAddr( addr, force )
        dataPtr = LP_c_uint8( c_uint8( value ) )
        msg = i2cSmbusMsg( read_write=I2C_SMBUS_WRITE,
                           command=register,
                           size=I2C_SMBUS_BYTE_DATA,
                           data=dataPtr )
        ioctl( self.__fd, I2C_SMBUS, msg )
        return


    def read_byte_data( self, addr, register, force=None ):
        """Read a single byte from a designated register."""
        self.__setAddr( addr, force )
        dataPtr = LP_c_uint8( c_uint8() )
        msg = i2cSmbusMsg( read_write=I2C_SMBUS_READ,
                           command=register,
                           size=I2C_SMBUS_BYTE_DATA,
                           data=dataPtr )
        ioctl( self.__fd, I2C_SMBUS, msg )
        [result] = struct.unpack( "@b", dataPtr.contents )
        return result


    def write_block_data( self, addr, register, data, force=None ):
        """Write a single byte to a designated register."""
        self.__setAddr( addr, force )
        length = len( data )
        buffer = create_string_buffer( length + 1 )
        buffer[0] = length
        buffer[1:length+1] = data
        dataPtr = LP_c_uint8( buffer )
        msg = i2cSmbusMsg( read_write=I2C_SMBUS_WRITE,
                           command=register,
                           size=I2C_SMBUS_BLOCK_DATA,
                           data=dataPtr)
        ioctl( self.__fd, I2C_SMBUS, msg )
        return


    def read_block_data( self, addr, register, force=None ):
        """Read a single byte from a designated register."""
        self.__setAddr( addr, force )
        buffer = create_string_buffer( 34 )
        dataPtr = LP_c_uint8( buffer )
        msg = i2cSmbusMsg( read_write=I2C_SMBUS_READ,
                           command=register,
                           size=I2C_SMBUS_BLOCK_DATA,
                           data=dataPtr )
        ioctl( self.__fd, I2C_SMBUS, msg )
        length = buffer[0]
        return list( buffer[1:length+1] )


# Constants for CCS811 chip (from CCS811 class)
CCS811_ADDR = 0x5B
HW_ID_REG = 0x20
HW_ID = 0x81
STATUS_REG = 0x00
APP_VALID_BIT = 4
APP_START_REG = 0xF4
POLL_MODE = 0
MEAS_INT_1 = 1
DRIVE_MODE_BIT = 4
MEAS_MODE_REG = 0x01
INT_DATARDY_BIT = 3
DATA_READY_BIT = 3
ALG_RESULT_DATA_REG = 0x02
MEAS_INT_IDLE = 0
SW_RESET_REG = 0xFF
ERROR_BIT = 0
ERROR_ID_REG = 0xE0

if __name__ == "__main__":


    def errorText( i2cBus, force=None ):
        """!
        @brief Return error text as a string.
        """
        errorCode = i2cBus.read_byte_data( CCS811_ADDR, ERROR_ID_REG, force )
        if (errorCode & 0x1F) == 0x1F:
            return 'All error bits set (0x{0:02X})'.format( errorCode )
        message = ''
        if errorCode & (1 << 0):
            message += 'Write request to wrong register received '
        if errorCode & (1 << 1):
            message += 'Read request for wrong register received '
        if errorCode & (1 << 2):
            message += 'Invalid MeasMode received '
        if errorCode & (1 << 3):
            message += 'Sensor resistance reached max resistance '
        if errorCode & (1 << 4):
            message += 'Heater Current is not in range '
        if errorCode & (1 << 5):
            message += 'Heater supply voltage is not applied correctly '
        return message[:-1]


    def errorCondition( i2cBus, force=None ):
        """!
        @brief return the error condition of the CCS811.
        """
        try:
            status = i2cBus.read_byte_data( CCS811_ADDR, STATUS_REG, force )
            print( 'Read status: 0x{0:02X}'.format( status ) )
            if (status & (1 << ERROR_BIT)) == 0:
                return False
            return True
        except Exception:
            return True


    def resetCCS811( i2cBus, force=None ):
        """!
        @brief Perform software reset on the CCS811 chip.
        """
        try:
            i2cBus.write_block_data( CCS811_ADDR,
                                     SW_RESET_REG,
                                     [0x11, 0xE5, 0x72, 0x8A],
                                     force )
            time.sleep( 5.0E-03 )
        except:
            pass
        return



    def main():
        """!
        @brief main program - I2C bus Signal Generator for Logic Analyzer.
        """

        _ = input( 'Arm Logic Analyzer - hit Enter when done' )
        print()

        co2List = []
        vocList = []

        try:
            # open the I2C bus
            i2cBus = SMBus( 1 )
        except (OSError, IOError, TypeError) as e:
            print( 'Error: opening the I2C bus failed: {0}'.format( e ) )
            return 1

        # initialize the CCS811 chip
        try:

            # 1st reset the device - write [0x11, 0xE5, 0x72, 0x8A] to
            # register 0xFF
            resetCCS811( i2cBus )
            print( 'SW reset completed' )
            # 2nd read HW-ID register 0x20 and assure it reads 0x81
            if i2cBus.read_byte_data( CCS811_ADDR, HW_ID_REG ) != HW_ID:
                print( 'CCS811 not found at I2C address '
                       '0x{0:02X}'.format( CCS811_ADDR ) )
                resetCCS811( i2cBus )
                i2cBus.close()
                return 1
            print( 'HW ID register reads OK' )
            # 3rd read status register 0x00
            status = i2cBus.read_byte_data( CCS811_ADDR, STATUS_REG )
            print( 'Read status: 0x{0:02X}'.format( status ) )
            # assure Bit 0 is not set
            if (status & (1 << ERROR_BIT)) != 0:
                print( 'Error: Error bit set after Software Reset - ' +
                       errorText( i2cBus ) )
                i2cBus.close()
                return 1
            # assure Bit 4 is set
            if not status & (1 << APP_VALID_BIT):
                print( 'Error: CCS811 internal App not valid.' )
                resetCCS811( i2cBus )
                i2cBus.close()
                return 1
            print( 'App status checks out OK' )
            # 4th write 0xF4 to device to put it in start mode
            # THIS FAILS ON RASPBERRY PI 3 - it is the only call to this method
            i2cBus.write_byte( CCS811_ADDR, APP_START_REG )
            time.sleep( 2.E-03 )
            # 5th read status register 0x00 and assure Bit 0 is not set
            if errorCondition( i2cBus ):
                print( 'Error: Error bit set after start mode write - '
                       + errorText( i2cBus ) )
                resetCCS811( i2cBus )
                i2cBus.close()
                return 1
            print( 'Device put in start mode' )
            # 6th write 0x10 to register 0x01 to select 1 s interval
            modeReg = MEAS_INT_1 << DRIVE_MODE_BIT
            modeReg |= POLL_MODE << INT_DATARDY_BIT
            i2cBus.write_byte_data( CCS811_ADDR,
                                 MEAS_MODE_REG,
                                 modeReg )
            # 7th read status register 0x00 and assure Bit 0 is not set
            if errorCondition( i2cBus ):
                print( 'Error: Error condition set after mode reg. write - ' +
                       errorText( i2cBus ) )
                resetCCS811( i2cBus )
                i2cBus.close()
                return 1
            print( 'wrote mode register to select 1 s measurement interval' )
        except (OSError, IOError, ValueError) as e:
            print( 'Error: could not initialize CCS811 sensor ({0})'
                   ''.format( e ) )
            resetCCS811( i2cBus )
            i2cBus.close()
            return 1

        print( '\nDevice initialized - ready to read data...\n' )
        error = False
        try:
            for i in range( n ):
                dataReady = False
                while not dataReady:
                    # repeatedly read status register 0x00 ...
                    status = i2cBus.read_byte_data( CCS811_ADDR,
                                                 STATUS_REG )
                    if (status & (1 << ERROR_BIT)) != 0:
                        print( 'Error condition set after reading status '
                               'reg in reading data in data set No. {0} - '
                               ''.format( i )  + errorText( i2cBus ) )
                        i2cBus.close()
                        return 1
                    # ... until Bit 3 is set
                    dataReady = (status & (1 << DATA_READY_BIT)) != 0
                # read 4 bytes from register 0x02
                data = i2cBus.read_block_data( CCS811_ADDR,
                                            ALG_RESULT_DATA_REG,
                                            4 )
                # read status register 0x00 to check error condition
                if errorCondition( i2cBus ):
                    print( 'Error condition set after reading data '
                           'in data set No. {0} - '.format( i ) +
                           errorText( i2cBus ) )
                    i2cBus.close()
                    return 1
                co2List.append( (data[0] << 8) | data[1] )
                vocList.append( (data[2] << 8) | data[3] )
        except (IOError, ValueError) as e:
            print( 'Error reading data: {0}'.format( e ) )
            error = True

        # close the CCS811 device
        if not error:
            print( '\nRead all requested data - closing device...\n' )
        resetCCS811( i2cBus )
        i2cBus.close()

        if not error:
            for i in range( len( co2List ) ):
                print( 'CO2: {0} ppm, total VOC: {1} ppb'
                       ''.format( co2List[i], vocList[i] ) )
        print( '\nExiting...' )

        return 0


    sys.exit( int( main() or 0 ) )
