# Python Implementation: tools
##
# @file       tools.py
#
# @version    2.0.0
#
# @par Purpose
# This module provides common tools used throughout this package.
#
# @par Known Bugs
# None
#
# @author
# W. Ekkehard Blanz <Ekkehard.Blanz@gmail.com>
#
# @copyright
# Copyright (C) 2021 - 2025 W. Ekkehard Blanz\n
# See NOTICE.md and LICENSE.md files that come with this distribution.

# File history:
#
#      Date         | Author         | Modification
#  -----------------+----------------+------------------------------------------
#   Wed Dec 25 2021 | Ekkehard Blanz | consolidated from other files
#   Fri Feb 14 2025 | Ekkehard Blanz | major overhaul
#                   |                |
#

# Micro Python does not know function attributes, use global variables instead
_PLATFORM = None
        
def platform() -> str:
    """!
    @brief Obtain the name of the platform we are running on.
    @return content of /sys/firmware/devicetree/base/model on the Pi or the 
            result of uname()[4] on the Raspberry Pi Pico (usually something 
            like 'Raspberry Pi 3 Model B Rev 1.2')
    """
    global _PLATFORM
    if not _PLATFORM:
        from sys import platform as sysplatform
        if sysplatform.lower() == 'rp2':
            from os import uname
            _PLATFORM = uname()[4]
        else:
            try:
                with open( "/sys/firmware/devicetree/base/model",
                           "r",
                           encoding="utf-8" ) as f:
                    _PLATFORM = f.read()
            except FileNotFoundError:
                raise ValueError( 'Not running on a Raspberry Pi or Pico' )
    return _PLATFORM


## isPico() returns True if the host is any Raspberry Pi Pico
isPico = lambda: platform().find( 'Pico' ) != -1

## isPico2() returns True if the host is specifically a Raspberry Pi Pico 2
## This requires that the correct build of the microPython interpreter is loaded
isPico2 = lambda: platform().find( 'Pico2' ) != -1

## isPi5() returns True if the host is a Raspberry Pi 5
isPi5 = lambda: platform().find( 'Pi 5' ) != -1



# header/board pins and their mapping to line numbers differ between Pi and Pico
if isPico():
    # Currently, this is the proper mapping of board pins to Pico GP lines
    _convList = [-9, 0, 1, -1, 2, 3, 4, 5, -1, 6, 7, 8, 9, -1, 10, 11, 12,
                 13, -1, 14, 15, 16, 17, -1, 18, 19, 20, 21, -1, 22, -2, 26, 
                 27, -1, 28, -3, -4, -5, -6, -1, -7, -8]
    
    # minima and maxima of board pin and line numbers
    _GPIO_LINE_MIN = 0
    _GPIO_LINE_MAX = 28
    _GPIO_PIN_MIN = 1
    _GPIO_PIN_MAX = 40
    _gpioRumpName = 'GP'
    _pinConfig = 'board'
else:
    # This section encapsulates the mapping of header pins to GPIO lines.  
    _convList = [-9, -2, -3, 2, -3, 3, -1, 4, 14, -1, 15, 17, 18, 27, -1, 22, 
                 23, -4, 24, 10, -1, 9, 25, 11, 8, -1, 7, -5, 6, 5, -1, 6, 12, 
                 13, -1, 19, 16, 26, 20, -1, 21]

    # minima and maxima of header pin and line numbers
    _GPIO_LINE_MIN = 2
    _GPIO_LINE_MAX = 27
    _GPIO_PIN_MIN = 1
    _GPIO_PIN_MAX = 40
    _gpioRumpName = 'GPIO'
    _pinConfig = 'header'


_CPU_INFO = None        # Struct with cpu info

def cpuInfo() -> dict:
    """!
    @brief Get some information about the CPU.
    @return cpuInfo dict with the following keys:
            numCores - number of processor cores
            processor - name of processor architecture
            bitDepth - bit depth of this architecture
            chip - name of the CPU/SoC chip
    """
    global _CPU_INFO

    # the first time we get called we construct the "static constant" _CPU_INFO
    if not _CPU_INFO:
        _CPU_INFO = {'numCores': 0,
                     'processor': '',
                     'bitDepth': 0,
                     'chip': ''}

        if isPico2():
            _CPU_INFO['numCores'] = 2 # 2 cores of each
            _CPU_INFO['processor'] = 'ARM Cortex-M33/RISC-V Hazard3'
            _CPU_INFO['bitDepth'] = 32
            _CPU_INFO['chip'] = 'RP2350'
        elif isPico():
            _CPU_INFO['numCores'] = 2
            _CPU_INFO['processor'] = 'ARM Cortex-M0+'
            _CPU_INFO['bitDepth'] = 32
            _CPU_INFO['chip'] = 'RP2040'
        else:
            def getRevision():
                """
                Returns Raspberry Pi Revision Code
                """
                with open( '/proc/device-tree/system/linux,revision', 
                           'rb' ) as fp:
                    return int.from_bytes( fp.read(4), 'big' )

            chipList = ['BCM2835', 'BCM2836', 'BCM2837', 'BCM2711', 'BCM2712']
            archList = {'BCM2835': 'ARM 1176JZF-S', 
                        'BCM2836': 'ARM Cortex-A7',
                        'BCM2837': 'ARM Cortex-A53', 
                        'BCM2711': 'ARM Cortex-A72',
                        'BCM2712': 'ARM Cortex-A76'}
            _CPU_INFO['chip'] = chipList[(getRevision() >> 12) & 7]
            _CPU_INFO['processor'] = archList[_CPU_INFO['chip']]

            import platform as plt
            _CPU_INFO["bitDepth"] = \
                int( plt.architecture()[0][:-3] )

            with open( '/proc/cpuinfo', 'r', encoding='utf-8' ) as f:
                for line in f:
                    if line.startswith( 'processor' ):
                        _CPU_INFO['numCores'] = \
                            max( _CPU_INFO['numCores'],
                                 int( line.split( ':' )[1].strip() ) )
            # so far we only got the highest core ID, which is 0-based
            _CPU_INFO['numCores'] += 1
    return _CPU_INFO


if not isPico():
    from typing import Union


def argToLine( pinArg: Union[int, str] ) -> int:
    if isinstance( pinArg, int ):
        try:
            retval = _convList[pinArg]
            if retval < _GPIO_PIN_MIN or retval > _GPIO_PIN_MAX:
                # exclude all the power pins
                raise IndexError
        except IndexError:
            raise ValueError( '\n\nwrong {3}} pin argument specified: {0}'
                            '\nIf the argument is given as an integer, it '
                            'needs to be in the range {1} to {2} and\n'
                            'correspond to a {3} pin number.\n'
                            .format( pinArg, _GPIO_PIN_MIN, _GPIO_PIN_MAX, 
                                     _pinConfig ) )
    elif isinstance( pinArg, str ):
        try:
            if pinArg.startswith( _gpioRumpName ):
                retval = int( pinArg.replace( _gpioRumpName, '' ) )
                if retval < _GPIO_LINE_MIN or retval > _GPIO_LINE_MAX: 
                    raise IndexError
            else:
                raise IndexError
        except IndexError:
            raise ValueError( '\n\nwrong line argument specified: {0}\n'
                            'If the argument is given as a string, it needs'
                            ' to be of the form \'{3}<n>\''
                            'where n ranges from {1} to {2}\nand represents'
                            ' a {3} line number.\n'
                            .format( pinArg, _GPIO_LINE_MIN, _GPIO_LINE_MAX,
                                     _gpioRumpName ) )
    else:
        raise ValueError( '\n\nwrong pin argument given: {0}'
                            .format( pinArg ) )
    return retval


def argToPin( pinArg: Union[int, str] ) -> int:
    """!
    @brief Convert a GPIO_AL pin argument to an RB Pi header Pin number
            (1 .. 40). The argument can be an integer, in which case it is 
            assumed that this integer represents a GPIO header pin number 
            already.  The argument can also be a string, in which case it is
            interpreted as a line number if it starts with the string 
            'GPIO'; otherwise it will be interpreted as representing an 
            integer header pin number.

    @param pinArg GPIO argument representing pin or line number
    @return header pin number
    """
    line = argToLine( pinArg )
    for retval in range( _GPIO_PIN_MAX ):
        if _convList[retval] == line:
            return retval
    raise ValueError( '\n\nwrong pin argument given: {0}'
                      .format( pinArg ) )


def gpioChipPath( line: int ) -> str:
        """!
        @brief Obtain the path to a GPIO chip that contains a given line.  The 
               function will ignore lines that are used.  Note that the argument
               is a line or offset number NOT a GPIO header pin number!  (@see 
               argToLine())

        As long as the GPIO line names all start with GPIO and are followed by
        the line number, this function does not need to be changed if the 
        architecture changes.

        Raspberry Pi versions before RB Pi 5 used the GPIO chip /dev/gpiochip0 
        to address all GPIO lines (offsets).  Early versions of RB Pi 5 used
        /dev/gpiochip4, which later was reversed to gpiochip0 while gpiochip4
        still existed as a symbolic link to gpiochip0.  To stay above all this
        mess, and even accommodate an architecture where GPIO lines are split
        across several GPIO chips, this code attempts to find the right chip for
        a given line programmatically.  This approach has the additional
        advantage, that it will also work on all Linux machines (e.g. also on a
        Jetson Nano running gpiod v2.2 and above).

        @param line GPIO line (offset) to search for in the GPIO chips
        @return path to GPIO chip containing that (unused) line as a string
        """
        if isPico():
            # Pico has no OS and no device files
            return ""

        import glob, os.path, gpiod
        for path in glob.glob( '/dev/*' ):
            if os.path.islink( path ) or not gpiod.is_gpiochip_device( path ):
                # this is to work around the gpiochip4 debacle on the RB Pi 5
                continue
            with gpiod.Chip( path ) as chip:
                for i in range( chip.get_info().num_lines ):
                    if chip.get_line_info( i ).name.startswith( 'GPIO' ) and \
                    not chip.get_line_info( i ).used:
                        if int( chip.get_line_info( i ).name[4:] ) == line:
                            return path
        
        raise ValueError( '\n\ncannot find GPIO chip for line GPIO{0}\n'
                          '(line may be in use)'.format( line ) )


def _hwPulseChip() -> str:
    """!
    @brief internal function to obtain the PWM chip number of a given Raspberry 
    Pi.
    """
    if isPi5():
        chipNo = 2
    else:
        chipNo = 0

    return 'pwmchip{0}'.format( chipNo )


def hwPWMlines() -> list:
    """!
    @brief Obtain a list of lines that support hardware PWM.
    This function is aware of whether or not the correct pwm overlay was loaded.
    @return list of GPIO lines that support hardware PWM
    @throws ValueError if config.txt was not used during startup
    """
    if isPico():
        # every line can be a HW PWM line
        lineList = list( range( 0, 23 ) ) + list( range( 26, 29 ) )
    else:
        import psutil
        import os
        configPath = '/boot/firmware/config.txt'
        if os.path.getmtime( configPath ) > psutil.boot_time():
            raise ValueError( 'config.txt was modified since last reboot\n'
                              'please reboot your system and try again' )
                            
        configModified = False
        with open( configPath, 'r' ) as f:
            for line in f:
                if line.strip() == \
                'dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4':
                    configModified = True
                    break
        if configModified:
            lineList = [12, 13]
        else:
            lineList = [18, 19]
    return lineList


def isHWpulsePin( pin: Union[int, str] ) -> bool:
    """!
    @brief Determine whether a given pin is capable of producing HW pulses
    @param pin GPIO argument representing pin or line number (int is pin number
               in GPIO header, GPIO{n} is line number)
    @return True if given pin is capable of HW pulses, False otherwise
    """
    if not isPico():
        # on the RB Pi, we need to check whether the correct module is loaded
        import os
        if not os.path.isdir( '/sys/class/pwm/{0}'
                              .format( _hwPulseChip() ) ):
            # pwm-2chan module not loaded - no pin can produce HW pulses
            return False
            
    return argToLine( pin ) in hwPWMlines()


def hwI2CLinePairs() -> list:
    """!
    @brief Obtain a list of line pairs that support hardware I2C.
    @return list of GPIO line pairs that support hardware PWM
    """
    if not isPico():
        result = [[2, 3]]
    else:
        # we only report standard I2C bus line pairs
        result = [[0, 1], [2, 3], [4, 5], [6, 7], [8,9], [10, 11], [12, 13],
                  [14, 15], [16, 17], [18, 19], [20, 21], [26, 27]]
    return result


def isHWI2CPinPair( sdaPin: Union[int, str], sclPin: Union[int,str] ) -> bool:
    """!
    @brief Determine whether a given pin is capable of producing HW pulses
    @param sdaPin GPIO argument representing pin or line number (int is pin 
           number in GPIO header, GPIO{n} is line number) os sda
    @param sclPin GPIO argument representing pin or line number (int is pin 
           number in GPIO header, GPIO{n} is line number) of scl
    @return True if given pin is capable of HW I2C, False otherwise
    """
    return [argToLine( sdaPin ), argToLine( sclPin )] in hwI2CLinePairs()


def lineToStr( line: int ) -> str:
    """!
    @brief Convert a line number into a platform-specific string, i.e. into the
           string 'GPIO<number>' for Raspberry Pi and 'GP<number>' for Raspberry
           Pi Pico.
    @param line GPIO or GP line number as an int
    @return platform specific string representation of line number
    """
    return '{0}{1}'.format( _gpioRumpName, line )





#  main program - NO Unit Test - Unit Test is in separate file

if __name__ == "__main__":

    import sys

    def main() -> int:
        """!
        @brief Main program - to save some resources, we do not include the
               Unit Test here.
        """
        print( 'platform: {0}'.format( platform() ) )
        print( 'cpu info: {0}'.format( cpuInfo() ) )
        print( 'gpio chip path: {0}'.format( gpioChipPath( 5 ) ) )
        print( 'Please use included GPIO_ALUnitTest.py for Unit Test' )
        return 0

    sys.exit( int( main() or 0 ) )