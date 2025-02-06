#!/usr/bin/env python3
# Python Implementation: openDrainBus
# -*- coding: utf-8 -*-
##
# @version    1.0.0
#
# @par Purpose
#             Writes a given value to a specified pin in GPIO.
#
# @par Comments
#             None
#
# @par Known Bugs
#             None
#
# @author     W. Ekkehard Blanz <Ekkehard.Blanz@gmail.com>
#
# @copyright
#             Copyright (C) 2025 W. Ekkehard Blanz
#             See NOTICE.md and LICENSE.md files that come with this
#             distribution.

# File history:
#
#     Date          | Author         | Modification
#  -----------------+----------------+------------------------------------------
#   Tue Feb 04 2025 | Ekkehard Blanz | created
#

import sys
from time import sleep

from GPIO_AL import PinIO

if "__main__" == __name__:
    def main():
        """!
        @brief Main program.
        """

        pin1 = int( input( 'Enter first header pin to use: ' ) )
        pin2 = int( input( 'Enter second header pin to use: ' ) )

        print( 'Now connect pin {0} and pin {1} with a wire to form a bus'
               .format( pin1, pin2 ) )
        print( 'Also connect a pullup resistor of about 4.7 kOhm to the bus' )
        _ = input( 'Hit Enter when done' )
        print( 'Observe the bus with a scope or LED' )

        try:
            pin1 = PinIO( pin1, PinIO.Mode.OPEN_DRAIN )
            pin2 = PinIO( pin2, PinIO.Mode.OPEN_DRAIN )
            print( pin1 )
            print( pin2 )

            print( 'Level at Pin1: {0} and at Pin2: {1}'
                   .format( pin1.level, pin2.level ) )
            print( 'Hit Ctrl-C to exit' )
            pin1.level = 0
            print( 'level at pin2: {0} (should be 0)'.format( pin2.level ) )
            sleep( 0.5 )
            pin1.level = 1
            print( 'level at pin2: {0} (should be 1)'.format( pin2.level ) )
            sleep( 0.5 )
            pin2.level = 0
            print( 'level at pin1: {0} (should be 0)'.format( pin1.level ) )
            sleep( 0.5 )
            pin2.level = 1
            print( 'level at pin1: {0} (should be 1)'.format( pin1.level ) )
            sleep( 0.5 )
        except:
            print( 'Error' )
        pin1.close()
        pin2.close()
        print( 'pins should be switched to low and input without pullups' )

        return 0

    sys.exit( int( main() or 0 ) )
