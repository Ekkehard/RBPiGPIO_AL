# Python Implementation: lsu2c
##
# @file       lsi2c.py
#
# @mainpage   Raspberry Pi list of all attached I2C bus devices
#
# @version    1.0.0
#
# @par Purpose
# More convenient output format then i2cdetect but functionally equivalent.
#
# This code has been tested on a Raspberry Pi 3 and a Raspberry Pi Pico.
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
# Copyright (C) 2022 W. Ekkehard Blanz\n
# See NOTICE.md and LICENSE.md files that come with this distribution.

# File history:
#
#      Date         | Author         | Modification
#  -----------------+----------------+------------------------------------------
#   Thu Apr 28 2022 | Ekkehard Blanz | created
#                   |                |

import sys
try:
    import os.path
    sys.path.append( os.path.join( os.path.dirname( __file__ ),
                                   os.path.pardir ) )
    import pigpio
    havePigpio = True
except (ImportError, ModuleNotFoundError):
    havePigpio = False
try:
    from GPIO_AL import I2Cbus, GPIOError
except ValueError as valexp:
    print( "\nError: {0}\n".format( valexp ) )
    sys.exit( 1 )

debug = False

if __name__ == "__main__":

    def printUsage():
        """!
        @brief Print very simple use message.
        """
        print( "List I2C devices attached to a specified I2C bus.\n" )
        print( "Synopsis:" )
        print( "\tlsi2c [<flags>] [<bus>] [<range>]\n" )
        print( "If not given, bus defaults to {0}. Range is given as two "
               "hexadecimal addresses\nbetween which to list devices with a "
               "hyphen (but no blanks) between them; if not\ngiven '0x03-0x77' "
               "is used as default.".format( I2Cbus.DEFAULT_BUS ) )
        print( "In addition to the flag -l or --long, which lists additional "
               "information about\neach device (if provided), the flags -h and "
               "--help as well as -V and --Version\nare supported as usual." )
        return


    def info( i2cbus, address ):
        """!
        @brief Obtains ID info from device.
        @param i2cbus I2C bus object
        @param address I2C address to probe
        @return string with human-readable device information
        """
        manufacturer = ["NXP Semiconductors",
                        "NXP Semiconductors (reserved)",
                        "NXP Semiconductors (reserved)",
                        "NXP Semiconductors (reserved)",
                        "Ramtron International",
                        "Analog Devices",
                        "STMicroelectronics",
                        "ON Semiconductor",
                        "Sprintek Corporation",
                        "ESPROS Photonics AG",
                        "Fujitsu Semiconductor",
                        "Flir",
                        "O2Micro",
                        "Atmel",
                        "DIODES Incorporated",
                        "Pericom",
                        "Marvell Semiconductors Inc",
                        "ForteMedia",
                        "Sanju LLC",
                        "Intel",
                        "Pericom",
                        "Arctic Sand Technologies",
                        "Micron Technology",
                        "Semtech Corporation",
                        "IDT",
                        "TT Electronics",
                        "Alien Technology",
                        "LAPIS semiconductor",
                        "Qorvo",
                        "Wuxi Chipown Micro-electronics",
                        "KOA CORPORATION",
                        "Prevo Technologies Inc."]

        global debug
        try:
            manufacturerId, deviceId, dieRevision = i2cbus.readId( address )
            return "Manufacturer: {0}, Part ID: 0x{1:02X}, die " \
                   "rev.: 0x{2:02X}".format( manufacturer[manufacturerId],
                                             deviceId,
                                             dieRevision )
        except GPIOError as e:
            if debug:
                return "device info not supplied ({0})".format( e )
            else:
                return "device info not supplied"


    def main():
        """!
        @brief Main program.
        """

        global debug

        # default parameters
        long = False
        bus = I2Cbus.DEFAULT_BUS
        addressLow = 0x03
        addressHigh = 0x77
        mode = I2Cbus.HARDWARE_MODE
        frequency = 100000
        attempts = 1
        usePEC = False

        for arg in sys.argv[1:]:
            if arg in ("-h", "--help"):
                printUsage()
                return 0
            if arg in ("-V", "--Version"):
                print( "lsi2c Rev 1.0.0" )
                return 0
            if arg in ("-d", "--debug"):
                debug = True
            elif arg in ("-l", "--long"):
                long = True
            elif arg.find( "-" ) != -1:
                try:
                    addressLow = int( arg.split( "-" )[0], 16 )
                    addressHigh = int( arg.split( "-" )[1], 16 )
                except ValueError:
                    print( "Error: Wrong parameter specified: {0}"
                           "".format( arg ) )
                    return 1
            elif arg.startswith( "f=" ):
                try:
                    frequency = int( arg[2:] )
                except ValueError:
                    print( "Error: Wrong parameter specified: {0}"
                           "".format( arg ) )
                    return 1
            else:
                try:
                    bus = int( arg )
                except ValueError:
                    print( "Error: Wrong parameter specified: {0}"
                           "".format( arg ) )
                    return 1

        if bus == I2Cbus.DEFAULT_BUS:
            sdaPin = I2Cbus.DEFAULT_DATA_PIN
            sclPin = I2Cbus.DEFAULT_CLOCK_PIN
        elif bus == 0:
            sdaPin = 0
            sclPin = 1
        else:
            print( "Error: Wrong I2C bus specified: {0}".format( bus ) )
            return 1

        try:
            i2cbus = I2Cbus( sdaPin,
                             sclPin,
                             mode,
                             frequency,
                             attempts,
                             usePEC )
        except FileNotFoundError:
            print( "Error: Hardware I2C bus {0} does not exist".format( bus ) )
            return 1

        deviceList = []
        for address in range( addressLow, addressHigh + 1 ):
            try:
                if (0x30 <= address <= 0x37) or (0x50 <= address <= 0x5F):
                    _ = i2cbus.readByte( address )
                else:
                    i2cbus.writeQuick( address )
                deviceList.append( address )
            except GPIOError:
                pass

        if long:
            for address in deviceList:
                print( "0x{0:2X} - {1}".format( address,
                                                info( i2cbus, address ) ) )
        else:
            for i, address in enumerate( deviceList ):
                print( "0x{0:02X}".format( address ), end="  " )
                if ((i + 1) % 10 == 0) or (i == len( deviceList ) - 1):
                    print()
        i2cbus.close()

        return 0

    sys.exit( int( main() or 0 ) )
