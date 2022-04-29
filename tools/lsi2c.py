#!/usr/bin/env python3
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
from GPIO_AL import I2Cbus, platform, GPIOError

if __name__ == "__main__":

    def printUsage():
        """!
        @brief Print very simple use message.
        """
        print( "Synopsis:\n" )
        print( "\tlsi2c [<flags>] [<bus>]" )
        print( "if not given, bus defaults to 1." )
        print( "\nthe flags -h and --help as well as -V and --Version "
               "are supported as usual." )
        return



    def main():
        """!
        @brief Main program.
        """
        if len( sys.argv ) > 1:
            arg = sys.argv[1]
            if arg in ("-h", "--help"):
                printUsage()
                return 0
            if arg in ("-V", "--Version"):
                print( "lsi2c Rev 1.00" )
                return 0
            try:
                bus = int( arg )
            except ValueError:
                print( "Wrong I2C bus specified" )
                return 1
        else:
            bus = 1

        if bus == 0:
            sdaPin = 0
            sclPin = 1
        elif bus == 1:
            sdaPin = 2
            sclPin = 3
        else:
            print( "Wrong I2C bus specified" )
            return 1

        i2cbus = I2Cbus( sdaPin,
                         sclPin,
                         100000,
                         I2Cbus.HARDWARE_MODE,
                         1 )

        for address in range( 0x03, 0x78 ):
            try:
                _ = i2cbus.readByte( address )
                print( "0x{0:02X}".format( address ) )
            except GPIOError:
                pass

        i2cbus.close()

        return 0

    sys.exit( int( main() or 0 ) )