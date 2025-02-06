#!/usr/bin/env python3
# Python Implementation: writePin
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
#             Copyright (C) 2024 W. Ekkehard Blanz
#             See NOTICE.md and LICENSE.md files that come with this
#             distribution.

# File history:
#
#     Date          | Author         | Modification
#  -----------------+----------------+------------------------------------------
#   Thu Nov 14 2024 | Ekkehard Blanz | created
#

import sys
from time import sleep

from GPIO_AL import PinIO

if "__main__" == __name__:
    def main():
        """!
        @brief Main program.
        """

        pin = int( input( 'Enter header pin to use: ' ) )
        level = int( input( 'Enter level to set pin {0} to: '
                            .format( pin ) ) )

        try:
            with PinIO( pin, PinIO.Mode.OUTPUT ) as writePin:
                print( writePin )
                print()

                print( 'writing {0} to GPIO pin {1}'.format( level, pin ) )
                writePin.level = level
                print( 'Hit Ctrl-C to exit' )
                while True:
                    sleep( 1 )
        except KeyboardInterrupt:
            print( '\nKeyboard interrupt detected...' )
        print( 'pin should be switched to low and input without pullups again' )

        return 0

    sys.exit( int( main() or 0 ) )
