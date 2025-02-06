#!/usr/bin/env python3
# Python Implementation: readPin
# -*- coding: utf-8 -*-
##
# @version    1.0.0
#
# @par Purpose
#             Reads a  value from a specified pin in GPIO.
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
            with PinIO( pin, PinIO.Mode.INPUT ) as readPin:
                currentLevel = readPin.level
                print( 'Level: {0}'.format( currentLevel ) )
                while ( True ):
                    if currentLevel != readPin.level:
                        currentLevel = readPin.level
                        print( 'Level: {0}'.format( currentLevel ) )
                    sleep( 0.1 )
        except KeyboardInterrupt:
            readPin.close()
            print( '\nExiting...\n' )

        return 0

    sys.exit( int( main() or 0 ) )
