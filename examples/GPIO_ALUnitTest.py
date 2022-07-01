# Python Implementation: GPIO_ALUnitTest
##
# @file       GPIO_ALUnitTest.py
#
# @version    1.0.0
#
# @par Purpose
# This module provides the Unit Test for the GPIO_AL module.  It has been
# separated from the GPIO_AL module to conserve some resources, as this code is
# intended to also run on an Raspberry Pi Pico MCU.  On this architecture, it is
# mandatory that the GPIO_AL.py file reside in the Raspberry Pi Pico's flash
# drive.
#
# Because of the nature of the class under test, this Unit Test cannot be
# completely automated and requires user interaction to set voltage levels on
# GPIO Pins or measure them with appropriate instruments.
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
# Copyright (C) 2021 W. Ekkehard Blanz\n
# See NOTICE.md and LICENSE.md files that come with this distribution.

# File history:
#
#      Date         | Author         | Modification
#  -----------------+----------------+------------------------------------------
#   Fri Oct 29 2021 | Ekkehard Blanz | separated from GPIO_AL.py
#                   |                |

from GPIO_AL import *


if __name__ == "__main__":

    import sys

    try:
        import traceback
        exitChar = 'Ctrl-C'
    except (ImportError, ModuleNotFoundError):
        traceback = None
        # keyboard interrupt on Raspberry Pi Pico is broken and gets "stuck"
        # so new inputs are also interrupted - use 'q' instead
        exitChar = 'q'

    DEBUG = True


    def callback( pin, level=None, tick=None ):
        """!
        @brief Simple callback method to test callback functionality.
        """
        print( '\nreceived interrupt on pin {0}'.format( pin ), end='' )
        if level is not None:
            print( 'level = {0}'.format( level ), end='' )
        if tick is not None:
            print( 'tick = {0}'.format( tick ), end='' )
        print( '\n' )
        return


    def main():
        """!
        @brief Unit Test for GPIO_AL.
        """
        print( '\nBegin IOpin test' )
        print( '----------------' )
        print( 'Enter {0} to end each level of this test '
               'and proceed to test with a different\n'
               'Pin object or to the I2C bus test'.format( exitChar ) )
        try:
            while True:
                pin = int( input( '\nPin for Pin I/O testing: ' ) )
                print( 'regular input mode  {0}'.format( IOpin.INPUT ) )
                print( 'input with pullup   {0}'.format( IOpin.INPUT_PULLUP ) )
                print( 'input with pulldown {0}'
                       ''.format( IOpin.INPUT_PULLDOWN ) )
                print( 'output mode         {0}'.format( IOpin.OUTPUT ) )
                print( 'open drain          {0}'.format( IOpin.OPEN_DRAIN))
                mode = int( input( '> ') )
                answer = input( 'Trigger interrupt [y/N]: ' )
                if answer == 'y' or answer == 'Y':
                    isr = callback
                    print( 'Trigger on' )
                    print( 'falling edge {0}'.format( IOpin.FALLING ) )
                    print( 'rising edge  {0}'.format( IOpin.RISING ) )
                    edge = int( input( '> ' ) )
                else:
                    isr = None
                    edge = None
                ioPin = IOpin( pin, mode, callback=isr, edge=edge )
                print( '\nPin is: {0}\n'.format( ioPin ) )
                try:
                    while True:
                        if mode < IOpin.OUTPUT:
                            q = input( 'Establish external voltage level at '
                                       'Pin {0}, and hit Enter when '
                                       'done '.format( pin ) )
                            if q == 'q':
                                break
                            print( 'Level at Pin {0} is '
                                   '{1}'.format( pin, ioPin.level ) )
                            try:
                                ioPin.level = 0
                                raise ValueError( 'Failed to detect write to '
                                                  'read only Pin' )
                            except GPIOError:
                                pass
                        else:
                            level = int( input( 'Enter level to set Pin '
                                                '{0} to: '.format( pin ) ) )
                            ioPin.level = level
                            if mode == IOpin.OPEN_DRAIN:
                                print( 'Level at Pin {0} is '
                                       '{1}'.format( pin, ioPin.level ) )
                                if level == IOpin.HIGH:
                                    q = input( 'Establish external voltage '
                                               'level at Pin {0}, and hit '
                                               'Enter when done '
                                               ''.format( pin ) )
                                    if q == 'q':
                                        break
                                    print( 'Level at Pin {0} is '
                                           '{1}'.format( pin, ioPin.level ) )
                            else:
                                try:
                                    _ = ioPin.level
                                    raise ValueError( 'Failed to detect read '
                                                      'from write only Pin' )
                                except GPIOError:
                                    pass
                except (KeyboardInterrupt, ValueError):
                    print()
                ioPin.close()
        except (KeyboardInterrupt, ValueError):
            print()
        except GPIOError as e:
            print( '\nGPIO ERROR: {0}'.format( e ) )
        except Exception as e:
            if DEBUG and traceback is not None:
                traceback.print_exc()
            else:
                print( '\nGeneral ERROR: {0}'.format( e ) )

        try:
            while True:
                print( '\nBegin I2C bus test' )
                print(   '------------------' )
                print( 'Again, enter {0} to end all tests an return '
                       'to the next higher test level'.format( exitChar ) )
                sdaPin = int( input( '\nsda Pin ({0}): '
                                     ''.format( I2Cbus.DEFAULT_DATA_PIN ) ) )
                sclPin = int( input( 'scl Pin ({0}): '
                                     ''.format( I2Cbus.DEFAULT_CLOCK_PIN ) ) )
                mode = int( input( 'mode (HW {0}, SW {1} - '
                                   ' HW not recommended for Raspberry Pi): '
                                   ''.format( I2Cbus.HARDWARE_MODE,
                                              I2Cbus.SOFTWARE_MODE ) ) )
                if mode == I2Cbus.SOFTWARE_MODE or isPico():
                    frequency = int( input( 'frequency in Hz: ' ) )
                else:
                    frequency = 100000
                attempts = int( input( 'number of read/write attempts: ' ) )
                usePEC = bool( input( 'Use PEC: ' ) )
                print( '\nChoices made:' )
                print( 'sda Pin: {0}'.format( i2cBus.sda ) )
                print( 'scl Pin: {0}'.format( i2cBus.scl ) )
                print( 'operating in ', end='' )
                if i2cBus.mode == I2Cbus.HARDWARE_MODE:
                    print( 'hard', end='' )
                else:
                    print( 'soft', end='' )
                print( 'ware mode' )
                print( 'at {0} kHz'.format( i2cBus.frequency / 1000. ) )
                if not usePEC:
                    print( 'not ', end='' )
                print( 'requesting PEC\n' )

                i2cBus = I2Cbus( sdaPin,
                                 sclPin,
                                 mode,
                                 frequency,
                                 attempts,
                                 usePEC )
                print( 'I2C Bus set up as {0}\n'.format( i2cBus ) )
                print( 'I2C Functions: 0x{0:08X}'.format( i2cBus.funcs ) )

                try:
                    while True:
                        deviceAddr = int( input( '\nEnter new I2C device '
                                                 'address in hex: '), 16 )
                        print( 'I2C address for next operations: '
                               '0x{0:02X}'.format( deviceAddr ) )
                        try:
                            while True:
                                print( '\nEnter next operation:' )
                                print( 'read general byte         0' )
                                print( 'read byte from register   1' )
                                print( 'read block from register  2' )
                                print( 'write general byte        3' )
                                print( 'write byte to register    4' )
                                print( 'write block to register   5' )
                                choice = int( input( '> ') )
                                if choice < 0 or choice > 5:
                                    continue
                                if choice != 0 and choice != 3:
                                    reg = int( input( 'register (hex): ' ), 16 )
                                else:
                                    reg = None
                                print( 'I/O operation: {0}'.format( choice ) )
                                if choice != 0 and choice != 3:
                                    print( 'device reg: '
                                           '0x{0:02X}'.format( reg ) )
                                if choice == 0 or choice == 1:
                                    if choice == 0:
                                        b = i2cBus.readByte( deviceAddr )
                                    else:
                                        b = i2cBus.readByteReg( deviceAddr,
                                                                reg )
                                    print( '\nread byte: '
                                           '0x{0:02X}'.format( b ) )
                                elif choice == 2:
                                    length = int( input( 'number of bytes '
                                                         ' to be read: ' ) )
                                    block = i2cBus.readBlockReg( deviceAddr,
                                                                 reg,
                                                                 length )
                                    print( '\nread block:' )
                                    for b in block:
                                        print( '  0x{0:02X}'.format( b ) )
                                elif choice == 3 or choice == 4:
                                    b = int( input( 'enter byte value '
                                                    'in hex: ' ), 16 )
                                    if choice == 3:
                                        i2cBus.writeByte( deviceAddr, b )
                                    else:
                                        i2cBus.writeByteReg( deviceAddr,
                                                             reg,
                                                             b )
                                elif choice == 5:
                                    length = int( input( 'number of bytes '
                                                         ' to be written: ' ) )
                                    block = []
                                    print( 'enter individual bytes in hex' )
                                    for _i in range( length ):
                                        b = int( input( '> ' ), 16 )
                                        block.append( b )
                                    i2cBus.writeBlockReg( deviceAddr,
                                                          reg,
                                                          block )
                        except (KeyboardInterrupt, ValueError):
                            print()
                        except GPIOError as e:
                            print( '\nGPIO ERROR: {0}'.format( e ) )
                        except Exception as e:
                            if DEBUG and traceback is not None:
                                traceback.print_exc()
                            else:
                                print( '\nGeneral ERROR: {0}'.format( e ) )
                            i2cBus.close()
                            break
                except (KeyboardInterrupt, ValueError):
                    print()
                    i2cBus.close()
                    print( '\nFailed attempts: {0}'
                           ''.format( i2cBus.failedAttempts ) )
                    print()
        except (KeyboardInterrupt, ValueError):
            print()

        print( '\nExiting...\n' )
        return 0


    sys.exit( int( main() or 0 ) )
