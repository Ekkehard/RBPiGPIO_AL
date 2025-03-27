#!/usr/bin/env python3
# Python Implementation: readAnalogSignal
# -*- coding: utf-8 -*-
##
# @version    1.0.0
#
# @par Purpose
#             Reads an analog signal from an external ADC chip.
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
#   Fri Mar 21 2025 | Ekkehard Blanz | created
#                   |                |

import sys
from time import sleep

from GPIO_AL import AnalogInput

if "__main__" == __name__:



    def main():
        """!
        @brief Main program.
        """
        
        channel = 0 # select channel 0 of the ADC chip

        with AnalogInput( channel ) as adc:
            try:
                while True:
                    print( 'signal = {0}'.format( adc.level ) )
                    sleep( 0.5 )
            except KeyboardInterrupt:
                print( 'Exiting on keyboard interrupt' )
                rc = 0
            except Exception as e:
                print( 'Exception: {0}'.format( e ) )
                rc = 1


        return rc

    sys.exit( int( main() or 0 ) )
