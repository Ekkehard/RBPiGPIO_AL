#!/usr/bin/env python3
# Python Implementation: callback
# -*- coding: utf-8 -*-
##
# @version    1.0.0
#
# @par Purpose
#             Sets a pin to input with callback functionality.
#
# @par Comments
#             
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
#   Fri Jan 10 2024 | Ekkehard Blanz | created
#                   |                |
#

import sys
from time import sleep

from GPIO_AL import PinIO





if "__main__" == __name__:


    def myCallback( pinObj ):
        print( 'callback called with pin {0}'
               .format( pinObj ) )
        return


    def main():
        """!
        @brief Main program.
        """
        
        pin = input( 'Enter header pin number to use: ' )
        edge = input( 'Enter trigger edge (FALLING, RISING, or BOTH)')

        if edge[0] == 'F':
            trig = PinIO.Edge.FALLING
        elif edge[0] == 'R':
            trig = PinIO.Edge.RISING
        elif edge[0] == 'B':
            trig = PinIO.Edge.BOTH

        try:
            with PinIO( pin, 
                        PinIO.Mode.INPUT, 
                        myCallback, 
                        trig ) as inputPin:
                print( 'Attach switch with pullup or square wave with ')
                print( 'frequency <= 0.5 Hz at header pin {0}'
                       .format( pin ) )
                print( inputPin )
                while ( True ):
                    sleep( 1.0 )
        except KeyboardInterrupt:
            pass
        print( '\nExiting...\n' )

        return 0

    sys.exit( int( main() or 0 ) )
