#!/usr/bin/env python3
# Python Implementation: togglePin
# -*- coding: utf-8 -*-
##
# @version    1.0.0
#
# @par Purpose
#             Toggles a specified pin in GPIO at high rate.
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

        pin = int( input( 'Enter header pin to use: ' ) )

        try:
            with PinIO( pin, PinIO.Mode.OUTPUT ) as writePin:
                print( writePin )
                print( 'observe changing signal (about 150 kHz) with a scope' )
                print( 'Hit Ctrl-C to exit' )
                while True:
                    writePin.toggle()
        except KeyboardInterrupt:
            print( '\nKeyboard interrupt detected...' )
        print( 'pin should be switched to low and input without pullups again' )

        return 0

    sys.exit( int( main() or 0 ) )
