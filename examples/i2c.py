#!/usr/bin/env python3
# Python Implementation: i2c
##
# @file       i2c.py
#
# @version    1.0.0
#
# @par Purpose
# This program demonstrates a simple use case of class I2C of the GPIO_AL 
# package.  It reads the manufacturer ID, device ID and die revision of a device
# with a given device address connected to the I2C bus.
#
# @par Comments
#
# @par Known Bugs
# None
#
# @author
# W. Ekkehard Blanz <Ekkehard.Blanz@gmail.com>
#
# @copyright
# Copyright 2025 W. Ekkehard Blanz
# See NOTICE.md and LICENSE.md files that come with this distribution.

# File history:
#
#      Date         | Author         | Modification
#  -----------------+----------------+------------------------------------------
#   Wed Mar 05 2025 | Ekkehard Blanz | created
#                   |                |

import sys
from GPIO_AL import GPIOError, I2C


if __name__ == "__main__":


    def main():
        """!
        @brief main program - I2C bus example.
        """

        # This device address is that of the CCS811 environmental sensor
        deviceAddr = 0x5B

        try:
            # initiate the I2C Bus with all default parameters
            with I2C() as i2cBus:
                print( 'I2C bus opened successfully:' )
                print( i2cBus )
                deviceIdTuple = i2cBus.readId( deviceAddr )
                print()
                print( 'manufacturer ID: {0}. device ID: {1}, die revision: {2}'
                       .format( deviceIdTuple[0], 
                                deviceIdTuple[1], 
                                deviceIdTuple[2] ) )
        except GPIOError as e:
            print( 'Error: {0}'.format( e ) )
            return 1
        return 0


    sys.exit( int( main() or 0 ) )
