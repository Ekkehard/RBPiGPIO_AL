# Python Implementation: QADPollTest
##
# @file       I2cSignalTest.py
#
# @version    1.0.0
#
# @par Purpose
# This program generates signals on the I2C bus suitable for Logic Analyzer
# investigation to analyze the performance of hardware I2C control and
# software I2C control (bit banging) on the Raspberry Pi.  The CCS811 sensor
# is thereby used as a test object but we do not rely on the CCS811 class but
# generate our own signals.
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
#   Thu May 26 2022 | Ekkehard Blanz | created
#                   |                |

import sys
import time

try:
    import os.path
    import os

    sys.path.append( os.path.join( os.path.dirname( __file__ ),
                                   os.pardir ) )
    sys.path.append( os.path.join( os.path.dirname( __file__ ),
                                   os.pardir,
                                   os.pardir,
                                   'GPIO_AL' ) )
except ImportError:
    # on the Pico there is no os.path but all modules are in the same directory
    pass

from GPIO_AL import GPIOError, I2Cbus

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


    def errorText( i2cBus ):
        """!
        @brief Return error text as a string.
        """
        errorCode = i2cBus.readByteReg( CCS811_ADDR, ERROR_ID_REG )
        if errorCode & 0x1F:
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


    def errorCondition( i2cBus ):
        """!
        @brief return the error condition of the CCS811.
        """
        try:
            for _ in range( i2cBus.attempts ):
                status = i2cBus.readByteReg( CCS811_ADDR, STATUS_REG )
                if (status & (1 << ERROR_BIT)) == 0:
                    return False
            return True
        except Exception:
            return True


    def resetCCS811( i2cBus ):
        """!
        @brief Perform software reset on the CCS811 chip.
        """
        try:
            i2cBus.writeBlockReg( CCS811_ADDR,
                                  SW_RESET_REG,
                                  [0x11, 0xE5, 0x72, 0x8A] )
            time.sleep( 5.0E-03 )
        except:
            pass
        return



    def main():
        """!
        @brief main program - I2C bus Signal Generator for Logic Analyzer.
        """
        frequency = int( input( 'Enter I2C bus frequency in Hz: ' ) )
        mode = int( input( 'Enter mode ({0} hardware mode, {1} software mode): '
                           ''.format( I2Cbus.HARDWARE_MODE,
                                      I2Cbus.SOFTWARE_MODE ) ) )
        attempts = int( input( 'Enter number of communication attempts to be '
                               'made: ' ) )
        n = int( input( 'Enter number of reads to be made: ' ) )

        _ = input( 'Arm Logic Analyzer - hit Enter when done' )
        print()

        co2List = []
        vocList = []

        try:
            # open the I2C bus with user-supplied parameters
            i2cBus = I2Cbus( I2Cbus.DEFAULT_DATA_PIN,
                             I2Cbus.DEFAULT_CLOCK_PIN,
                             frequency,
                             mode,
                             attempts )
        except GPIOError as e:
            print( 'Error: opening the I2C bus failed: {0}'.format( e ) )
            return 1

        # initialize the CCS811 chip
        try:

            # 1st reset the device - write four bytes to register 0xFF
            resetCCS811( i2cBus )
            print( 'SW reset completed' )
            # 2nd read HW-ID register 0x20 and assure it reads 0x81
            if i2cBus.readByteReg( CCS811_ADDR, HW_ID_REG ) != HW_ID:
                print( 'CCS811 not found at I2C address '
                       '0x{0:02X}'.format( CCS811_ADDR ) )
                resetCCS811( i2cBus )
                i2cBus.close()
                return 1
            print( 'HW ID register reads OK' )
            # 3rd read status register 0x00
            status = i2cBus.readByteReg( CCS811_ADDR, STATUS_REG )
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
            i2cBus.writeByte( CCS811_ADDR, APP_START_REG )
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
            i2cBus.writeByteReg( CCS811_ADDR,
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
        except (GPIOError, ValueError) as e:
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
                    status = i2cBus.readByteReg( CCS811_ADDR,
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
                data = i2cBus.readBlockReg( CCS811_ADDR,
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
        except (GPIOError, ValueError) as e:
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
