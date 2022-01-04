# Python Implementation: GPIO_AL
##
# @file       GPIO_AL.py
#
# @mainpage   Raspberry Pi GPIO Abstraction Layer
#
# @version    2.0.0
#
# @par Purpose
# This module provides an abstraction layer for the Raspberry Pi General Purpose
# I/O (GPIO) functionality for all models of the regular Raspberry Pi 3 as
# well as the Raspberry Pi Pico.  Using this module, code should run and use the
# common functionality of the GPIO shared by all Raspberry Pi architectures
# without modifications on all Raspberry Pi architectures.
#
# This code has been tested on a Raspberry Pi 3 and a Raspberry Pi Pico.
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
# Copyright (C) 2021 - 2022 W. Ekkehard Blanz\n
# See NOTICE.md and LICENSE.md files that come with this distribution.

# File history:
#
#      Date         | Author         | Modification
#  -----------------+----------------+------------------------------------------
#   Wed Oct 27 2021 | Ekkehard Blanz | created
#   Thu Dec 09 2021 | Ekkehard Blanz | changed default mode for I2Cbus for
#                   |                | Raspberry Pi to Software
#   Sat Dec 18 2021 | Ekkehard Blanz | fixed bug in writeByteReg and 
#                   |                | writeBlockReg for RB Pi Software I2C
#   Sun Jan 02 2022 | Ekkehard Blanz | replaced ARCHITECTURE with CPU_INFO
#                   |                |

# first define our exception class so we can throw it from anywhere
class GPIOError( Exception ):
    """!
    @brief Exception class to be thrown by the GPIO_AL module, or modules that
           use it.

    The class only has a constructor, a __str__ method, which produces the
    string with which it was instantiated and a severity property, which returns
    the severity with which it was instantiated.
    """

    ## Warning only
    WARNING = 0
    ## Regular error
    ERROR = 1
    ## Fatal error from which one cannot recover
    FATAL = 2

    def __init__( self, value, severity=ERROR ):
        """!
        @brief Constructor - accepts and internally stores error message as well
               as a severity of the error.
        @param value error message for this instance
        @param severity GPIOError.WARNING, GPIOError.ERROR or GPIOError.FATAL -
               default is GPIOError.ERROR
        """
        self.__value = value
        self.__severity = severity


    def __str__( self ):
        """!
        @brief Serialize the error message.
        """
        return str( self.__value )


    @property
    def severity( self ):
        """!
        @brief Works as a property to obtain severity of the error that caused
               the exception.
        """
        return self.__severity



def _cpuInfo():
    """!
    @brief Get some information from /proc/cpuinfo.

    If more information needs to be extracted from /proc/cpuinfo, this can be
    easily done.  However, existing keys should be kept for backward
    compatibility with other modules.
    @return cpuInfo dict - description see below
    """
    cpuInfo = {'numCores' : None,
               'processor' : None,
               'chip' : None,
               'revision' : None,
               'model' : None}
    
    from sys import platform
    if platform == 'rp2':
        cpuInfo['numCores'] = 2
        cpuInfo['processor'] = 'Arm Cortex-M0+'
        cpuInfo['chip'] = 'RP2040'
        cpuInfo['revision'] = ''
        cpuInfo['model'] = 'Raspberry Pi Pico'
    else:
        try:
            f = open( '/proc/cpuinfo', 'r' )
        except FileNotFoundError:
            return cpuInfo
        for line in f:
            if line.startswith( 'processor' ):
                cpuInfo['numCores'] = int( line.split( ':' )[1].strip() )
            elif line.startswith( 'model name' ):
                cpuInfo['processor'] = line.split( ':' )[1].strip()
            elif line.startswith( 'Hardware' ):
                cpuInfo['chip'] = line.split( ':' )[1].strip()
            elif line.startswith( 'Revision' ):
                cpuInfo['revision'] = line.split( ':' )[1].strip()
            elif line.startswith( 'Model' ):
                cpuInfo['model'] = line.split( ':' )[1].strip()
        f.close()
        cpuInfo['numCores'] += 1
        
    return cpuInfo

## CPU_INFO dict has the following str keys:
#   - 'numCores'  - number of processor cores as int
#   - 'processor' - name of the processor architecture as str
#   - 'chip'      - name of the processor chip as str
#   - 'revision'  - revision of the processor chip as str
#   - 'model'     - Raspberry Pi model as str
CPU_INFO = _cpuInfo()

# determine platform and import appropriate module for GPIO access
if not CPU_INFO['model']:
    raise GPIOError( 'Current architecture not supported by GPIO_AI' )
elif CPU_INFO['model'].find( 'Pico' ) != -1:
    import machine
else:
    import pigpio


class IOpin( object ):
    """!
    @brief Class to encapsulate single Pin I/O.

    This class allows a given Pin to be configured as an input Pin with or
    without pull up or pull down resistors, as a regular output Pin, or as an
    open drain Pin, in which case only setting its level to IOpin.LOW will
    actually drive it low and setting its level to IOpin.HIGH will put the Pin
    in input mode with a pullup resistor.  Levels of Pins that have been set to
    any input mode cannot be set; levels of Pins that have been set to output
    mode cannot be read; levels of Pins that have been set to open drain mode
    can be set and read.

    Moreover, the class allows an interrupt service routine to be specified as
    well as the trigger edge for that interrupt; both can be None, in which case
    no interrupt functionality is provided for the selected Pin.  Interrupt
    service routines must be provided by the user in the form
    @code
        def myCallback( pin, level=None, tick=None ):
            ...
            return
    @endcode
    to work on all Raspberry Pi architectures.
    
    Pins' voltage levels are examined and set via setters and getters for the
    level property of this class, i.e. if myPin is an IOpin object via the
    statements
    @code
        value = myPin.level
    @endcode
    to examine the Pin's voltage level and store it in the variable value, and
    @code
        myPin.level = value
    @endcode
    to set the voltage level of the Pin to whatever the variable value contains,
    which should be either IOpin.HIGH or IOpin.LOW.
    
    Also, the pigpiod daemon needs to run on Raspberry Pis running under an
    operating system in order to use GPIO Pins.  Either use
    @code
        sudo pigpiod
    @endcode
    whenever you want to use it or enable the daemon at boot time using
    @code
        sudo systemctl enable pigpiod
    @endcode
    to have the GPIO daemon start every time the Raspberry Pi OS boots.
    """

    ## Input mode without resistors pulling up or down
    INPUT = 0
    ## Input mode with pullup resistor
    INPUT_PULLUP = 1
    ## Input mode with pulldown resistor
    INPUT_PULLDOWN = 2
    ## Regular output mode
    OUTPUT = 3
    ## Open drain mode - implemented in software on hardware that does not
    ## support it
    OPEN_DRAIN = 4

    ## Low voltage level
    LOW = 0
    ## High voltage level
    HIGH = 1

    ## Trigger on falling edge
    FALLING = 0
    ## Trigger on rising edge
    RISING = 1

    def __init__( self, pin, mode, callback=None, edge=None ):
        """!
        @brief Constructor - sets Pin properties, including interrupt
               capabilities.
        @param pin I/O Pin number to associate with object
        @param mode I/O mode - one of IOpin.INPUT, IOpin.INPUT_PULLUP,
               IOpin.INPUT_PULLDOWN, IOpin.OUTPUT, or IOpin.OPEN_DRAIN
        @param callback interrupt service routine for this Pin or None (default)
        @param edge edge on which to trigger the interrupt, one of
               IOpin.FALLING, IOpin.RISING - defaults to None
        """
        self.__pin = pin
        if mode != self.INPUT \
           and mode != self.INPUT_PULLUP \
           and mode != self.INPUT_PULLDOWN \
           and mode != self.OUTPUT \
           and mode != self.OPEN_DRAIN:
            raise GPIOError( 'Wrong mode specified: {0}'.format( mode ) )
        self.__mode = mode
        if callback is not None and not callable( callback ):
            raise GPIOError( 'Wrong interrupt service routine specified' )
        self.__isr = callback
        if edge is not None \
           and edge != self.FALLING \
           and edge != self.RISING:
            raise GPIOError( 'Wrong triggerEdge specified: '
                             '{0}'.format( edge ) )
        if (callback is not None and edge is None) or \
           (callback is None and edge is not None):
            raise GPIOError( 'Either both callback and edge must be specified '
                             'or none of them' )
        self.__triggerEdge = edge

        self.__pinObj = None    # will be set by setup methods

        if self.__mode < self.OUTPUT:
            self.__set = (lambda _level: self.__error( 'Cannot set level on '
                                                       'input Pins' ) )
        elif self.__mode == self.OUTPUT:
            self.__level = (lambda : self.__error( 'Cannot read level from '
                                                   'output Pins' ) )

        # initialize host-specific libraries and hardware
        if CPU_INFO['model'].find( 'Pico' ) != -1:
            self.__setupRPPico()
        else:
            self.__setupRP()

        self.__open = True

        return


    def __del__( self ):
        """!
        @brief Destructor - only meaningful on the Raspberry Pi and
               potentially during Unit Tests on the Raspberry Pi Pico.

        Closes the Pin on the Raspberry Pi.
        """
        self.close()
        return


    def __str__( self ):
        """!
        @brief String representation of this class - returns all settable
               parametrs.
        """
        modeStr = ['INPUT', 'INPUT_PULLUP', 'INPUT_PULLDOWN', 'OUTPUT',
                   'OPEN_DRAIN']
        trigStr = ['FALLING', 'RISING']
        if self.triggerEdge is not None:
            triggerEdge = trigStr[self.triggerEdge]
        else:
            triggerEdge = ''
        return 'pin: {0}, mode: {1}, callback: {2}, edge: {3}' \
               ''.format( self.pin,
                          modeStr[self.mode],
                          self.callback,
                          triggerEdge )


    def __error( self, text ):
        """!
        @brief Private method that throws an exception.

        Raising an exception alone is a statement - not an expression - in a
        lambda function we need an expression, and this is it.
        @param text string of text to throw GPIOError exception with
        """
        raise GPIOError( text )


    def __setupRP( self ):
        """!
        @brief Private method to set up hardware of the Raspberry Pi as well as
        lambda functions to read from and write to single I/O Pins.
        """
        self.__pinObj = pigpio.pi()

        if self.__mode < self.OUTPUT:
            self.__pinObj.set_mode( self.__pin, pigpio.INPUT )
            if self.__mode == self.INPUT_PULLUP:
                self.__pinObj.set_pull_up_down( self.__pin, pigpio.PUD_UP )
            elif self.__mode == self.INPUT_PULLDOWN:
                self.__pinObj.set_pull_up_down( self.__pin, pigpio.PUD_DOWN )
            else:
                self.__pinObj.set_pull_up_down( self.__pin, pigpio.PUD_OFF )
            self.__level = (lambda: self.__pinObj.read( self.__pin ))
        else:
            self.__pinObj.set_mode( self.__pin, pigpio.OUTPUT )
            if self.__mode == self.OUTPUT:
                self.__set = (lambda level: self.__pinObj.write( self.__pin,
                                                                 level ))
            else:
                self.__set = self.__softwareOpenDrainSet
                self.__level = (lambda: self.__pinObj.read( self.__pin ))

        self.__close = self.__pinObj.stop

        if self.__isr is not None:
            if self.__triggerEdge == self.FALLING:
                triggerEdge = pigpio.FALLING_EDGE
            elif self.__triggerEdge == self.RISING:
                triggerEdge = pigpio.RISING_EDGE
            else:
                raise GPIOError( 'Internal error' )
            self.__pinObj.callback( self.__pin, triggerEdge, self.__isr )

        return


    def __setupRPPico( self ):
        """!
        @brief Private method to set up hardware of the Raspberry Pi Pico as
        well as lambda functions to read from and write to single I/O Pins.
        """
        pull = None
        if self.__mode == self.INPUT:
            mode = machine.Pin.IN
        elif self.__mode == self.INPUT_PULLUP:
            mode = machine.Pin.IN
            pull = machine.Pin.PULL_UP
        elif self.__mode == self.INPUT_PULLDOWN:
            mode = machine.Pin.IN
            pull = machine.Pin.PULL_DOWN
        elif self.__mode == self.OUTPUT:
            mode = machine.Pin.OUT
        elif self.__mode == self.OPEN_DRAIN:
            mode = machine.Pin.OPEN_DRAIN
            pull = machine.Pin.PULL_UP
        else:
            raise GPIOError( 'Internal error' )
        self.__pinObj = machine.Pin( self.__pin, mode, pull )

        self.__close = (lambda:
                        self.__pinObj.init( self.__pin, machine.Pin.IN ))

        if self.__mode >= self.OUTPUT:
            self.__set = (lambda level: self.__pinObj.value( level ) )

        if self.__mode == self.OUTPUT or self.__mode == self.OPEN_DRAIN:
            self.__level = (lambda: self.__pinObj.value())

        if self.__isr is not None:
            if self.__triggerEdge == self.FALLING:
                triggerEdge = machine.Pin.IRQ_FALLING
            elif self.__triggerEdge == self.RISING:
                triggerEdge = machine.Pin.IRQ_RISING
            else:
                raise GPIOError( 'Internal error' )
            self.__pinObj.irq( self.__isr, triggerEdge )

        return


    def __softwareOpenDrainSet( self, level ):
        """!
        @brief Private method to simulate an open drain circuit on a Raspberry
               Pi that doesn't offer hardware support for it.
        @param level level to set Pin to - one of IOpin.HIGH or IOpin.LOW
        """
        if level == self.HIGH:
            # output is never driven high - just pulled up in input mode
            self.__pinObj.set_mode( self.__pin, pigpio.INPUT )
            self.__pinObj.set_pull_up_down( self.__pin, pigpio.PUD_UP )
        else:
            # output is actively driven low
            self.__pinObj.set_mode( self.__pin, pigpio.OUTPUT )
            self.__pinObj.write( self.__pin, level )

        return


    def close( self ):
        """!
        @brief Close the Pin - set it to input (high impedance) without pulling
               up or down.
        """
        if self.__open:
            self.__close()
            self.__open = False
        return
    
    
    @property
    def pin( self ):
        """!
        @brief Works as read-only property to get the GPIO Pin number
        associated with this class.
        @return pin number associated with this class
        """
        return self.__pin
    
    
    @property
    def mode( self ):
        """!
        @brief Works as read-only property to get I/O mode of that Pin as an
               int.
        @return mode of that Pin as IOpin.INPUT, IOpin.INPUT_PULLUP,
                IOpin.INPUT_PULLDOWN, IOpin.OUTPUT or IOpin.OPEN_DRAIN
        """
        return self.__mode
    
    
    @property
    def callback( self ):
        """!
        @brief Works as read-only property to get the name of callback function
               as a string.
        @return interrupt callback function name or emtpy string
        """
        if self.__isr is not None:
            return self.__isr.__name__
        else:
            return ''
        
        
    @property
    def triggerEdge( self ):
        """!
        @brief Works as read-only property to get the interrupt trigger edge
               as an int.
        @return trigger edge as IOpin.FALLING, IOpin.RISING or None
        """
        return self.__triggerEdge


    @property
    def level( self ):
        """!
        @brief Works as read/write property to get the current voltage level
               of a Pin as an int.
        @return IOpin.HIGH or IOpin.LOW
        """
        # The dud self.__level() will be overridden by setup methods.
        return self.__level()


    @level.setter
    def level( self, level ):
        """!
        @brief Works as the setter of a read/write property to set the Pin to a
               given voltage level.
        @param level level to set Pin to - one of IOpin.HIGH and IOpin.LOW
        """
        # The dud self.__set() will be overridden by setup methods.
        self.__set( level )
        return



class I2Cbus( object ):
    """!
    @brief Class to handle I<sup>2</sup>C bus communication.

    The GPIO Pins on the Raspberry Pi are GPIO 2 for I<sup>2</sup>C data and
    GPIO 3 for I<sup>2</sup>C clock for hardware I<sup>2</sup>C and freely
    selectable for software I<sup>2</sup>C (bit banging); on the Raspberry Pi
    Pico, the GPIO Pins for I<sup>2</sup>C communication are also freely
    selectable under software I<sup>2</sup>C, they are restricted to GPIO 1 for
    data and GPIO 2 for clock, GPIO 4 for data and GPIO 5 for clock, GPIO 6
    for data and GPIO 7 for clock, GPIO 9 for data and GPIO 10 for clock,
    GPIO 11 for data and GOPI 12 for clock, GPIO 14 for data and GOPI 15 for
    clock, GPIO 16 for data and GPIO 17 for clock, GPIO 19 for data and GPIO
    20 for clock, GPIO 21 for data and GPIO 22 for clock, GPIO 24 for data
    and GPIO 25 for clock, GPIO 26 for data and GPIO 27 for clock, or GPIO 31
    for data and GPIO 32 for clock.
    
    Since many targets can be connected on  an I<sup>2</sup>C bus, one I2Cbus
    object must be able to handle them all.  Therefore, I2Cbus objects are
    created one per I<sup>2</sup>C bus, which is uniquely defined by the sda
    and scl Pins - NOT one such object per target on that bus.  Every
    I<sup>2</sup>C I/O operation therefore needs to be given the
    I<sup>2</sup>C address of the target this communication is meant for.
    
    On the Raspberries running under Linux-like operating systems, it is 
    mandatory that the user be part of the group i2c to be able to use the
    I<sup>2</sup>C bus.  This can be accomplished by issuing the command (in a
    terminal window)
    @code
        sudo usermod -a -G i2c <user name>
    @endcode
    and then logging out and back in again.  Otherwise, access to the
    I<sup>2</sup>C device requires elevated privileges (sudo), and the
    practice of using those when not strictly necessary is strongly discouraged.
    
    Also, the pigpiod daemon needs to run on Raspberry Pis running under an
    operating system in order to use GPIO Pins.  Either use
    @code
        sudo pigpiod
    @endcode
    whenever you want to use it or enable the daemon at boot time using
    @code
        sudo systemctl enable pigpiod
    @endcode
    to have the GPIO daemon start every time the Raspberry Pi OS boots.
        
    It is worth noting that the defaults for the operating mode are different
    between the Raspberry Pi 3 and the Raspberry Pi Pico.  This is because
    the Broadcomm BCM2835 chip, which the Raspberry Pi 3 uses for hardware
    I<sup>2</sup>C, is broken and does not (reliably) support clock
    stretching when requested by a target.  This was found through
    measurements and also confirmed online at
    https://www.advamation.com/knowhow/raspberrypi/rpi-i2c-bug.html.  The
    software mode supports clock stretching properly on the Raspberry Pi 3.
    Naturally, the software-generated I<sup>2</sup>C clock on a non-real-time
    OS is not very consistent, but targets will tolerate a non-consistent
    clock better, albeit not always completely, than a broken clock-stretch
    mechanism when they need it.  Therefore, the default operating mode on a
    Raspberry Pi 3 is software, but since the Raspberry Pi Pico works just
    fine with hardware I<sup>2</sup>C, the default operating mode there is
    hardware to free the CPU from the task of generating I<sup>2</sup>C
    signals.  This software still allows the caller to select hardware mode
    also on the Raspberry Pi 3, but the user is strongly advised to make sure
    that no target on the I<sup>2</sup>C bus requires clock stretching in
    such cases.  Moreover, the user is much more likely to run into error
    conditions on a Raspberry Pi 3 I<sup>2</sup>C bus than on any other
    system, and it is a very good idea to write "robust" code that checks
    error conditions continuously and deals with them appropriately when the
    I<sup>2</sup>C bus and clock stretching has to be used on a Raspberry Pi 3,
    even in software mode.
    """

    ## Operate I<sup>2</sup>C bus in hardware mode
    HARDWARE_MODE = 0
    ## Operate I<sup>2</sup>C bus in software (bit banging) mode
    SOFTWARE_MODE = 1
    ## Number of I/O attempts in I/O methods before throwing an exception
    ATTEMPTS = 5
    if CPU_INFO['model'].find( 'Pico' ) != -1:
        ## Default Pin number for sda (Different for different architectures)
        DEFAULT_DATA_PIN = 8
        ## Default Pin number for scl (Different for different architectures)
        DEFAULT_CLOCK_PIN = 9
        ## Default operating mode on the Pico is software so as not to
        ## overburden the CPU with thasks the hardware can do
        DEFAULT_MODE = HARDWARE_MODE
        ## Default frequency for I<sup>2</sup>C bus communications on the
        ## Raspberry Pi Pico is 100 kHz
        DEFAULT_I2C_FREQ = 100000
    else:
        DEFAULT_DATA_PIN = 2
        DEFAULT_CLOCK_PIN = 3
        if CPU_INFO['chip'] == 'BCM2835':
            ## The BCM2835 chip is broken and the default operating mode for it
            ## is therefore set to software
            DEFAULT_MODE = SOFTWARE_MODE
            ## Default frequency for I<sup>2</sup>C bus communications with this
            ## chip is reduced to 75 kHz
            DEFAULT_I2C_FREQ = 75000
        else:
            # TODO is that Raspberry Pi 4?
            DEFAULT_MODE = HARDWARE_MODE
            ## Default frequency for I<sup>2</sup>C bus communications on chips
            ## other than the BCM2835 is 100 kHz
            DEFAULT_I2C_FREQ = 100000



    def __init__( self,
                  sdaPin=DEFAULT_DATA_PIN,
                  sclPin=DEFAULT_CLOCK_PIN,
                  frequency=DEFAULT_I2C_FREQ,
                  mode=DEFAULT_MODE ):
        """!
        @brief Constructor for class I<sup>2</sup>Cbus.

        @param sdaPin GPIO Pin number for I<sup>2</sup>C data (default 1 on
               Raspberry Pi and 8 on Raspberry Pi Pico)
        @param sclPin GPIO Pin number for I<sup>2</sup>C clock (default 2 on
               Raspberry Pi and 9 on Raspberry Pi Pico)
        @param frequency I<sup>2</sup>C frequency in Hz (default 75 kHz for
               Raspberry Pi and 100 kHz for Raspbberry Pi Pico)
        @param mode one of I2<Cbus.HARDWARE_MODE or I2Cbus.SOFTWARE_MODE
               AKA bit banging (default I2Cbus.SOFTWARE for Raspberry Pi and
               I2Cbus.HARDWARE for Raspberry Pi Pico)
        """
        # store our incoming parameters
        self.__sdaPin = sdaPin
        self.__sclPin = sclPin
        self.__frequency = frequency
        self.__mode = mode
        self.__attempts = self.ATTEMPTS
        self.__failedAttempts = 0

        self.__i2cObj = None

        # initialize host-specific libraries and hardware
        if CPU_INFO['model'].find( 'Pico' ) != -1:
            self.__setupRPPico()
        else:
            self.__setupRP()

        self.__open = True
        return


    def __del__( self ):
        """!
        @brief Destructor - only meaningful on the Raspberry Pi and
               potentially during Unit Tests on the Raspberry Pi Pico.

        Closes the software I<sup>2</sup>C bus on the Raspberry Pi.
        """
        self.close()
        return


    def __str__( self ):
        """!
        @brief String representing initialization parameters used by this class.
        """
        modeStr = ['HW', 'SW']
        return 'sda Pin: {0}, scl Pin: {1}, f: {2} kHz, mode: {3}' \
               ''.format( self.__sdaPin,
                          self.__sclPin,
                          self.__frequency / 1000.,
                          modeStr[self.__mode] )
    

    def close( self ):
        """!
        @brief On the Raspberry Pi, it is important to call this method to
               properly close the pigpio object in software mode.
        """
        if self.__open:
            if CPU_INFO['model'].find( 'Pico' ) != -1:
                try:
                    self.__i2cObj.deinit()
                except AttributeError:
                    pass
            else:
                if self.__mode == self.SOFTWARE_MODE:
                    self.__i2cObj.bb_i2c_close( self.__sdaPin )
                    self.__i2cObj.stop()
                else:
                    self.__i2cObj.close()
            self.__open = False
        return


    def __setupRP( self ):
        """!
        @brief Private method to set up hardware of the Raspberry Pi as well as
        lambda functions to read from and write to an I<sup>2</sup>C bus.
        """
        if self.__mode == self.HARDWARE_MODE:
            # in hardware mode, use SMBus - prefer smbus2 over smbus
            try:
                from smbus2 import SMBus
            except ModuleNotFoundError:
                from smbus import SMBus

            if self.__sdaPin == 0 and self.__sclPin == 1:
                i2cBus = 0
            elif self.__sdaPin == 2 and self.__sclPin == 3:
                i2cBus = 1
            else:
                raise GPIOError( 'Wrong I2C Pins specified' )
            # __init__() does an open() internally
            self.__i2cObj = SMBus( i2cBus )

            # override the i2c duds with corresponding smbus methods
            # (they are 100 % compatible)
            self.__readByte = self.__i2cObj.read_byte
            self.__readByteReg = self.__i2cObj.read_byte_data
            self.__readBlockReg = self.__i2cObj.read_i2c_block_data
            self.__writeByte = self.__i2cObj.write_byte
            self.__writeByteReg = self.__i2cObj.write_byte_data
            self.__writeBlockReg = self.__i2cObj.write_i2c_block_data

        elif self.__mode == self.SOFTWARE_MODE:
            self.__i2cObj = pigpio.pi()
            if not self.__i2cObj.connected:
                raise GPIOError( 'Could not connect to GPIO' )
            try:
                # in case somebody didn't close it properly...
                self.__i2cObj.bb_i2c_close( self.__sdaPin )
            except:
                pass

            # bb_i2c_zip commands:
            END = 0
            START = 2
            RESTART = 2
            STOP = 3
            ADDRESS = 4
            READ = 6
            WRITE = 7

            try:
                if self.__i2cObj.bb_i2c_open( self.__sdaPin,
                                              self.__sclPin,
                                              self.__frequency ) != 0:
                    raise GPIOError( 'Opening Software I2C failed' )
            except Exception as e:
                raise GPIOError( str( e ) )
                    

            # override the i2c duds with corresponding bb_i2c_zip calls
            self.__readByte = \
                (lambda addr: list(
                    self.__i2cObj.bb_i2c_zip(
                        self.__sdaPin,
                        [START, ADDRESS, addr, READ,
                         1,
                         STOP,
                         END] )[1] )[0])
            self.__readByteReg = \
                (lambda addr, reg: list(
                    self.__i2cObj.bb_i2c_zip(
                        self.__sdaPin,
                        [START, ADDRESS, addr, WRITE,
                         1,
                         reg,
                         RESTART, ADDRESS, addr, READ,
                         1,
                         STOP,
                         END] )[1] )[0])
            self.__readBlockReg = \
                (lambda addr, reg, length: list(
                    self.__i2cObj.bb_i2c_zip(
                        self.__sdaPin,
                        [START, ADDRESS, addr, WRITE,
                         1,
                         reg,
                         RESTART, ADDRESS, addr, READ,
                         length,
                         STOP,
                         END] )[1] ))
            self.__writeByte = \
                (lambda addr, value: self.__i2cObj.bb_i2c_zip(
                    self.__sdaPin,
                    [START, ADDRESS, addr, WRITE,
                     1,
                     value,
                     STOP,
                     END] ))
            self.__writeByteReg = \
                (lambda addr, reg, value: self.__i2cObj.bb_i2c_zip(
                    self.__sdaPin,
                    [START, ADDRESS, addr, WRITE,
                     2,
                     reg, value,
                     STOP,
                     END] ))
            self.__writeBlockReg = \
                (lambda addr, reg, data: self.__i2cObj.bb_i2c_zip(
                    self.__sdaPin,
                    [START, ADDRESS, addr, WRITE,
                     1 + len( data ),
                     reg] + data +
                    [STOP,
                     END] ))
        else:
            raise GPIOError( 'Wrong I2Cbus mode specified: '
                             '{0}'.format( self.__mode ) )

        return


    def __setupRPPico( self ):
        """!
        @brief Private method to set up hardware of the Raspberry Pi Pico as
               well as lambda functions to read from and write to an
               I<sup>2</sup>C bus.
        """
        if self.__mode == self.SOFTWARE_MODE:
            self.__i2cObj = machine.SoftI2C(
                sda=machine.Pin( self.__sdaPin ),
                scl=machine.Pin( self.__sclPin ),
                freq=self.__frequency )
        elif self.__mode == self.HARDWARE_MODE:
            if self.__sclPin == 3 or self.__sclPin == 7 or \
               self.__sclPin == 11 or self.__sclPin == 15 or \
               self.__sclPin == 19 or self.__sclPin == 27:
                i2cId = 1
            else:
                # Error checking is provided by the machine.I2C constructor
                # so we just default to 0 for all other Pins
                i2cId = 0
            self.__i2cObj = machine.I2C( i2cId,
                                         sda=machine.Pin( self.__sdaPin ),
                                         scl=machine.Pin( self.__sclPin ),
                                         freq=self.__frequency )
        else:
            raise GPIOError( 'Wrong mode specified: '
                             '{0}'.format( self.__mode ) )

        self.__readByte = \
            (lambda addr, reg:
                 list( self.__i2cObj.readfrom( addr, 1 ) )[0])
        self.__readByteReg = \
            (lambda addr, reg:
                 list( self.__i2cObj.readfrom_mem( addr, reg, 1 ) )[0])
        self.__readBlockReg = \
            (lambda addr, reg, count:
                 list( self.__i2cObj.readfrom_mem( addr,reg, count ) ))
        self.__writeByte = \
            (lambda addr, value:
             self.__i2cObj.writeto( addr, bytearray( [value] ) ))
        self.__writeByteReg = \
            (lambda addr, reg, value:
             self.__i2cObj.writeto_mem( addr, reg, bytearray( [value] ) ))
        self.__writeBlockReg = \
            (lambda addr, reg, data:
                self.__i2cObj.writeto_mem( addr, reg, bytearray( data ) ))

        return
    
    
    def clearFailedAttempts( self ):
        """!
        @brief Clear the number of internally recorded failed attempts.
        """
        self.__failedAttempts = 0
    
    
    @property
    def failedAttempts( self ):
        """!
        @brief Works as read-only property to obtain the number of internally
               recorded failed attempts.
        """
        return self.__failedAttempts
    
    
    @property
    def frequency( self ):
        """!
        @brief Works as read-only property to get the frequency the I<sup>2</sup>C bus is
               operating at in Hz.
        """
        return self.__frequency
    
    
    @property
    def mode( self ):
        """!
        @brief Works as read-only property to get the I2Cbus mode
               (I2Cbus.SOFTWARE_MODE or I2Cbus.HARDWARE_MODE).
        """
        return self.__mode
    
    
    @property
    def sda( self ):
        """!
        @brief Works as read-only property to get the sda Pin number.
        """
        return self.__sdaPin
    
    
    @property
    def scl( self ):
        """!
        @brief Works as read-only property to get the scl Pin number.
        """
        return self.__sclPin


    # The following methods are wrappers around the internal methods allowing
    # for multiple attempts in case of errors, which proved necessary on the
    # Raspberry Pi
    
    def readByte( self, i2cAddress ):
        """!
        @brief Read a single general byte from an I<sup>2</sup>C device.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @return int with byte read
        """
        count = 0
        errorText = ''
        while count < self.__attempts:
            try:
                return self.__readByte( i2cAddress )
            except Exception:
                count += 1
                self.__failedAttempts += 1
        raise GPIOError( 'exceeded {0} attempts '.format( self.__attempts )
                         + 'in readByte' )
    

    def readByteReg( self, i2cAddress, register ):
        """!
        @brief Read a single byte from an I<sup>2</sup>C device register.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @param register device register to read from
        @return int with byte read
        """
        count = 0
        errorText = ''
        while count < self.__attempts:
            try:
                return self.__readByteReg( i2cAddress, register )
            except Exception:
                count += 1
                self.__failedAttempts += 1
        raise GPIOError( 'exceeded {0} attempts '.format( self.__attempts )
                         + 'in readByteReg' )


    def readBlockReg( self, i2cAddress, register, length ):
        """!
        @brief Read a block of bytes from an I<sup>2</sup>C device register.
        @param i2cAddress address of I<sup>2</sup>C device to be read from
        @param register device register to start reading
        @param length number of bytes to be read
        @return list of ints with bytes read
        """
        count = 0
        errorText = ''
        while count < self.__attempts:
            try:
                return self.__readBlockReg( i2cAddress, register,  length )
            except Exception:
                count += 1
                self.__failedAttempts += 1
        raise GPIOError( 'exceeded {0} attempts '.format( self.__attempts )
                         + 'in readBlockReg' )


    def writeByte( self, i2cAddress, value ):
        """!
        @brief Write a single byte to an I<sup>2</sup>C device.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param value value of byte to be written as an int
        """
        count = 0
        errorText = ''
        while count < self.__attempts:
            try:
                self.__writeByte( i2cAddress, value )
                return
            except Exception:
                count += 1
                self.__failedAttempts += 1
        raise GPIOError( 'exceeded {0} attempts '.format( self.__attempts )
                         + 'in writeByte' )


    def writeByteReg( self, i2cAddress, register, value ):
        """!
        @brief Write a single byte to an I<sup>2</sup>C device register.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param register device register to start reading
        @param value value of byte to be written as an int
        """
        count = 0
        errorText = ''
        while count < self.__attempts:
            try:
                self.__writeByteReg( i2cAddress, register, value )
                return
            except Exception:
                count += 1
                self.__failedAttempts += 1
        raise GPIOError( 'exceeded {0} attempts '.format( self.__attempts )
                         + 'in writeByteReg' )


    def writeBlockReg( self, i2cAddress, register, block ):
        """!
        @brief Write a block of bytes to an I<sup>2</sup>C device starting at
               register.
        @param i2cAddress address of I<sup>2</sup>C device to be written to
        @param register device register to start reading
        @param block list of ints with bytes to be written
        """
        count = 0
        errorText = ''
        while count < self.__attempts:
            try:
                self.__writeBlockReg( i2cAddress, register, block )
                return
            except Exception:
                count += 1
                self.__failedAttempts += 1
        raise GPIOError( 'exceeded {0} attempts '.format( self.__attempts )
                         + 'in writeBlockReg' )


#  main program - NO Unit Test - Unit Test is in separate file

if __name__ == "__main__":
    
    import sys

    def main():
        """!
        @brief Main program - to save some resources, we do not include the 
               Unit Test here.
        """
        print( 'cpu info: {0}\n'.format( CPU_INFO ) )
        print( 'Please use included GPIO_ALUnitTest.py for Unit Test' )
        return 0

    
    sys.exit( int( main() or 0 ) )
