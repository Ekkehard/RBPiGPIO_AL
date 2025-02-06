#!/usr/bin/env python3
# Python Implementation: pullupdown
# -*- coding: utf-8 -*-
##
# @version    1.1.0
#
# @par Purpose
#             Sets a pin to input with pullup or pulldown and probes its state.
#             After setup, the pin can be externally pulled down with a 
#             (variable) resistor to observe the effect of the internal pullup.
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
#             Copyright (C) 2024-2025 W. Ekkehard Blanz
#             See NOTICE.md and LICENSE.md files that come with this
#             distribution.

# File history:
#
#     Date          | Author         | Modification
#  -----------------+----------------+------------------------------------------
#   Mon Nov 04 2024 | Ekkehard Blanz | created
#   Tue Feb 04 2025 | Ekkehard Blanz | added pulldown functionality
#

import sys
from time import sleep

from GPIO_AL import PinIO

if "__main__" == __name__:

    def main():
        """!
        @brief Main program.
        """

        pull = 'up'

        
        pin = input( 'Enter header pin number to use: ' )
        pull = input( 'pull u[p], pull d[own], or n[one]:' )

        if pull[0] == 'u':
            pull = PinIO.Mode.INPUT_PULLUP
        elif pull[0] == 'd':
            pull = PinIO.Mode.INPUT_PULLDOWN
        else:
            pull = PinIO.Mode.INPUT
        print( 'Using {0} on input pin {1}...'.format( pull, pin ) )

        inputPin = PinIO( pin, pull )
        
        print( 'now externally pull the pin in the opposite direction with'
               'a (variable)\nresistor and observe the effect of the internal '
               'pulling.' )

        try:
            currentLevel = inputPin.level
            print( 'Level: {0}'.format( currentLevel ) )
            while ( True ):
                if currentLevel != inputPin.level:
                    currentLevel = inputPin.level
                    print( 'Level: {0}'.format( currentLevel ) )
                sleep( 0.1 )
        except KeyboardInterrupt:
            inputPin.close()
            print( '\nExiting...\n' )

        return 0

    sys.exit( int( main() or 0 ) )
