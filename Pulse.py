# Python Implementation: Pulse
##
# @file       Pulse.py
#
# @mainpage   Raspberry Pi Pulse Generator
#
# @version    4.0.0
#
# @par Purpose
# This module provides an abstraction layer for the Raspberry Pi General Purpose
# I/O (GPIO) PWM functionality for all models of the regular Raspberry Pi 0 and 
# up as well as the Raspberry Pi Pico.  Using this module, code should run and 
# use the common functionality of the GPIO and the PWM hardware shared by most 
# Raspberry Pi architectures without modifications on all those architectures.
# Where hardware PWM is not available, this class switches automatically to
# software-generated PWM.
#
# THe module contains a class _HWPulse, which is the only class that needs to be
# modified should the RB Pi hardware PWM mechanism ever change.
#
# This code has been tested on a Raspberry Pi 0, 3, 4 and 5 and a Raspberry Pi 
# Pico.
#
# @par Comments
# This is Python 3 code!  PEP 8 guidelines are decidedly NOT followed in some
# instances, and guidelines provided by "Coding Style Guidelines" a "Process
# Guidelines" document from WEB Design are used instead where the two differ,
# as the latter span several programming languages and are therefore applicable
# also for projects that require more than one programming language; it also
# provides consistency across hundreds of thousands of lines of legacy code.
# Doing so, ironically, is following PEP 8 which speaks highly of the wisdom of
# the authors of PEP 8.
#
# @par Known Bugs
# None
#
# @author
# W. Ekkehard Blanz <Ekkehard.Blanz@gmail.com>
#
# @copyright
# Copyright (C) 2021 - 2024 W. Ekkehard Blanz\n
# See NOTICE.md and LICENSE.md files that come with this distribution.

# File history:
#
#      Date         | Author         | Modification
#  -----------------+----------------+------------------------------------------
#   Sat Dec 14 2024 | Ekkehard Blanz | extracted from GPIO_AL.py
#                   |                |

from typing import Union, Optional
from enum import Enum, IntEnum
import time
import threading
import os
from abc import ABC, ABCMeta, abstractmethod
from GPIO_AL.tools import isPi5, argToLine, isHWpulsePin, _hwPulseChip
from GPIO_AL.PinIO import PinIO
from GPIO_AL import GPIOError



    
    
class _PulseAPI( metaclass=ABCMeta ):
    """!
    @brief Abstract base class provides API for pulse classes.
    """

    def __init__( self,
                  pulsePin: Union[int,str,PinIO],
                  frequency: Union[float,object],
                  dutyCycle: Optional[float]=0.5,
                  bursts: Optional[int]=None ):
        """!
        @brief Constructor - sets up common parameter for both modes.
        @param pulsePin integer with pin number in GPIO header, string with
                        GPIO<lineNumber> or PinIO object.
        @param frequency pulse frequency in Hz or a PObject with unit Hz
        @param dutyCycle 0 <= dutyCycle <= 1 duty cycle of pulse (default: 0.5)
        @param bursts number of impulses to generate or None for continuous
                      (default: None)
        """

        self._bursts = bursts
        self._pulsePin = pulsePin
        try:
            if str( frequency.unit ) != 'Hz':
                raise GPIOError( 'Wrong frequency object specified: {0}'
                                 .format( frequency ) )
        except AttributeError:
            pass
        self._orgFreq = frequency
        self._frequency = float( frequency )
        self._dutyCycle = float( dutyCycle )
        if dutyCycle > 1 and dutyCycle <= 100:
            self._dutyCycle = dutyCycle / 100.
        else:
            self._dutyCycle = dutyCycle
        if self._dutyCycle < 0 or self._dutyCycle > 1:
            raise GPIOError( 'Wrong duty cycle specified: {0}'
                             .format( dutyCycle ) )
        self._period = 1 / self._frequency
        self._highTime = self._period * self._dutyCycle
        self._lowTime = self._period *  (1 - self._dutyCycle)
        return
            
    @abstractmethod
    def __del__( self ):
        """!
        @brief Destructor.  To be implemented by child.
        """
        pass
        
    @abstractmethod
    def __str__( self ):
        """!
        @brief String representation of this class - returns all settable
               parameters.  To be implemented by child.
        """
        pass
            
    @abstractmethod
    def start( self ):
        """!
        @brief Method to start any pulse to be implemented by child.
        """
        pass
        
    @abstractmethod
    def stop( self ):
        """!
        @brief Method to stop any pulse to be implemented by child.

        The child class must implement stop() in such a way that it can be
        called repeatedly.
        """
        pass

    @property
    @abstractmethod
    def dutyCycle( self ) -> float:
        """!
        @brief read property to get duty cycle to be implemented by child.
        @return current duty cycle
        """
        pass
  
    @dutyCycle.setter
    @abstractmethod
    def dutyCycle( self, value: float ):
        """!
        @brief setter of a dutyCycle property to be implemented by child.
        @param value new duty cycle to use 0 <= value <= 1
        """
        pass

    @property
    @abstractmethod
    def frequency( self ) -> float:
        """!
        @brief read property to get frequency to be implemented by child.
        @return current duty cycle
        """
        pass
  
    @frequency.setter
    @abstractmethod
    def frequency( self, value: float ):
        """!
        @brief setter of a frequency property to be implemented by child.
        @param value new frequency (note that actors only accept floats)
        """
        pass



class Pulse( _PulseAPI ):
    """!
    @brief Class to create arbitrary pulses on arbitrary pins.

    This class allows the generation of pulses of a large range of frequencies 
    and duty cycles as well as bursts with a specified amount of impulses on any
    pin of the GPIO.  Some pins support hardware-generated pulses.  If this 
    class detects that the requested pin is one of those pins and that the 
    necessary kernel modules are loaded, it will use hardware to generate the 
    pulses; otherwise, the pulses will be generated via software.  The software 
    to generate the pulses will run in the background with minimal overhead.  It
    is noted, however, that the Raspbian (Debian) operating system is not a 
    real-time operating system, and pulse parameters for software-generated 
    pulses are therefore not guaranteed to be stable and not meant for precise 
    measurements.  In particular, if the pulses are used to control servo
    motors, software-generated pulses can cause the motors to move erratically,
    especially under heavy CPU load on the Raspberry Pi.
    
    This module can provide a list of pins that support hardware-generated 
    pulses, if they exist and the needed modules are loaded.  Minimal and 
    maximal frequencies are vastly different for hardware and software 
    generated pulses and this class won't accept out-of-reach frequencies as 
    parameters.  In particular, hardware-generated pulses can oscillate from 
    0.1 Hz up to about 5 MHz, while software-generated pulses can oscillate from
    arbitrarily low frequencies up to about 2 kHz.  For hardware-generated 
    pulses to work, the module pwm-2chan needs to be loaded by putting the line
    @code
        dtoverlay=pwm-2chan
    @endcode
    or
    @code
        dtoverlay=pwm-2chan,pin=18,func=2,pin2=19,func2=2
    @endcode
    in the file config.txt in /boot/firmware.  If that module is not loaded, 
    this class will only use software-generated pulses.  Usually, GPIO18 
    (pin 12) and GPIO19 (pin 35) are used for hardware pulses, but if the line
    @code
        dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4
    @endcode
    is placed in config.txt instead of one of the previously mentioned lines,
    the pins GPIO12 (pin 32) and GPIO13 (pin 33) are used for hardware pulses
    instead.  This class is aware of the content of the file config.txt and 
    checks if the system has been booted with that exact config.txt in place
    and that config.txt has not changed since then.
    
    The class is initiated with a pulsePin parameter that is either an int, a 
    string, or a PinIO object.  If it is given as an int, it is assumed that
    this represents the Pin number on the GPIO header of the Raspberry Pi, not
    the GPIO line number.  If it is given as a string, it must be of the form
    GPIO<line> where line is the GPIO line number.  Lastly, the parameter can be
    given as a PinIO object.  In this case, this object is used to generate
    software-timed pulses, even if it is a PinIO object for Pins that are
    capable of generating hardware pulses.
    
    This class can be initiated with a frequency in Hz given as a float or
    with a PObject (-derived object) with unit 'Hz'. 
    
    When operating in burst mode, there are a few additional restrictions.  The 
    time the bursts can last is a minimum of 0.75 ms in hardware mode; in 
    software mode there is no restriction.  Additionally, the maximal frequency
    in burst mode is limited to 10 kHz in hardware mode; in software mode, all 
    frequency that this mode can operate with are also available in burst mode.
    Please note that in hardware mode the burst mechanism is controlled via 
    software timing and all restrictions with respect to software timing on 
    non-real-time operating systems apply for hardware bursts too.
    The class will properly dispose of all objects that are created internally.
    However, if an external PinIO object was provided, it will not be destroyed
    by this class upon termination.
    """

    def __init__( self,
                  pulsePin: Union[int, str, PinIO],
                  frequency: Union[float,object],
                  dutyCycle: Optional[float]=0.5,
                  bursts: Optional[int]=None ):
        """!
        @brief Constructor - sets up parameters and determines mode (hard- or
               software)
        This class merely provides a common API to both hardware and software
        generated pulses and selects the proper one of the two.
        @param pulsePin integer with pin number in GPIO header or string of the
                        form 'GPIO<lineNumber>'
        @param frequency pulse frequency in Hz as float or PObject with unit Hz
        @param dutyCycle 0 <= dutyCycle <= 1 duty cycle of pulse (default: 0.5)
        @param bursts number of impulses to generate or None for continuous
                      operation (default: None)
        """
        self.__actor = None
        if isinstance( pulsePin, PinIO ) or not isHWpulsePin( pulsePin ):
            self.__actor = _SWPulse( pulsePin, frequency, dutyCycle, bursts )
        else:
            self.__actor = _HWPulse( pulsePin, frequency, dutyCycle, bursts )
        return

    def __del__( self ):
        """!
        @brief Destructor - only meaningful on the Raspberry Pi and
               potentially during Unit Tests on the Raspberry Pi Pico.

        Closes the pin.
        """
        self.stop()
        if self.__actor: 
            del self.__actor
            self.__actor = None
        return

    def  __enter__( self ):
        """!
        @brief Enter method for conext management.
        @return an object that is used in the "as" construct, here it is self
        """
        return self

    def __exit__( self, excType, excValue, excTraceback ):
        """!
        @brief Exit method for context management.
        @param excType type of exception ending the context
        @param excValue value of the exception ending the context
        @param excTraceback traceback of excweption ending the context
        @return False (will re-raise the exception)
        """
        # we could just let the destruction of the classes take care of properly
        # closing all the devices and timers, but we can also call the stop() 
        # method to come to a coordinated halt.  This requires that the "actor"
        # classes can tolerate repeated stop commands.
        self.stop()
        return False

    def __str__( self ):
        """!
        @brief String representation of this class - returns all settable
               parameters.
        """
        return self.__actor.__str__()

    def start( self ):
        """!
        @brief Method to start any pulse.
        """
        self.__actor.start()
        return

    def stop( self ):
        """!
        @brief Method to stop any pulse.
        """
        # In case of an emergency stop, the actor may not even exist (anymore)
        if self.__actor: self.__actor.stop()
        return

    @property
    def dutyCycle( self ):
        """!
        @brief Works as read/write property to get the current duty cycle.
        @return current duty cycle
        """
        return self.__actor.dutyCycle

    @dutyCycle.setter
    def dutyCycle( self, value: float ):
        """!
        @brief Works as the setter of a read/write property to set the duty
               cycle
        @param value new duty cycle to use 0 <= value <= 1
        """
        # silently handle percent values between 1 and 100
        if value > 1 and value <= 100: val = value / 100.
        else: val = value
        if val < 0 or val > 1:
            raise GPIOError( 'Wrong duty cycle specified: {0}'
                             .format( value ) )
        self.__actor.dutyCycle = val
        return

    @property
    def frequency( self ):
        """!
        @brief Implements read property of frequency to be implemented by actor.
        @return current duty cycle
        """
        return self._frequency
  
    @frequency.setter
    def frequency( self, value: Union[float,object] ):
        """!
        @brief setter of a frequency property to be implemented by actor.
        @param value new duty cycle to use 0 <= value <= 1
        """
        self._orgFreq = value
        self.__actor.frequency = float( frequency )
        return


class _HWPulse( _PulseAPI ):
    """!
    @brief Internal child class to implement hardware PWM pulses.
    
    If the RB Pi hardware PWM support changes, this is the only class that needs
    to be touched.  Be mindful to keep the API determined by PulseAPI as is. 
    """
    def __init__( self,
                  pulsePin: Union[int, str],
                  frequency: Union[float,object],
                  dutyCycle: float,
                  bursts: Union[int, None] ):
        """!
        @brief Constructor - sets up parameters.
        @param pulsePin integer with pin number in GPIO header or string with
                        GPIO<lineNumber>
        @param frequency in Hz as float or PObject with unit Hz
        @param duty cycle 0 <= dutyCylce <= 1
        @param bursts number of burts or None for continuous operation
        """
        super().__init__( pulsePin, frequency, dutyCycle, bursts )
        self.__burstTime = None
        self.__burstTimer = None
        if bursts and self._frequency > 10000:
            raise GPIOError( 'Maximal frequency for hardware bursts is 10 kHz' )
        line = argToLine( pulsePin )
        self.__channel = self.__lineToPWMChannel( line )
        self.__deviceDir = os.path.join( '/sys/class/pwm',
                                         _hwPulseChip(),
                                         'pwm{0}'.format( self.__channel) )
        shortestBurstTime = 0.000750
        if self._bursts:
            self.__burstTime = self._bursts * self._period - self._lowTime / 2
            if self.__burstTime < shortestBurstTime:
                raise GPIOError( 'Time bursts must last longer than {0} s'
                                .format( shortestBurstTime ) )
            self.__burstTime -= shortestBurstTime
        if not os.path.isdir( self.__deviceDir ):
            try:
                with open( os.path.join( '/sys/class/pwm',
                                        _hwPulseChip(),
                                        'export' ), 'w' ) as f:
                    f.write( str( self.__channel ) )
            except Exception as e:
                raise GPIOError( 'Cannot create HW pulse device (' +
                                 str( e ) + ')' )
        time.sleep( 1.0 )
        # just to make sure...
        if not os.path.isdir( self.__deviceDir ):
            raise GPIOError( 'Did not create device {0}'
                             .format( self.__deviceDir ) )
        # pin will be set to LOW
        try:
            self.__writeDevice( 'enable', 0 )
        except OSError:
            # sometimes, this device needs a little extra convincing...
            try:
                time.sleep( 0.5 )
                periodNs = 1000000000 / self._frequency
                self.__writeDevice( 'period', periodNs )
                self.__writeDevice( 'enable', 0 )
            except OSError:
                raise GPIOError( 'Could not establish device' )
        time.sleep( 0.5 )
        return

    def __del__( self ):
        """!
        @brief Destructor - stops everything and even unexports the pwm device
               for this channel on the Pi.
        """
        self.stop()
        with open( os.path.join( '/sys/class/pwm',
                                _hwPulseChip(),
                                'unexport' ), 'w' ) as f:
            f.write( str( self.__channel ) )
        return

    def __str__( self ):
        """!
        @brief String representation of this class - returns all settable
               parameters.
        """
        return 'pin: {0}, frequency: {1}, duty cycle: {2}, bursts: {3}, ' \
               'mode: HARDWARE' \
               .format( self._pulsePin,
                        self._orgFreq,
                        self._dutyCycle,
                        self._bursts )

    def __writeDevice( self, device: str, param: int ):
        """!
        @brief write a given parameter to a given PWM device.
        @param device one of 'period', 'duty_cycle, or 'enable'
        @param numerical parameter
        """
        with open( os.path.join( self.__deviceDir, device ), 'w' ) as f:
            f.write( '{0}\n'.format( round( param ) ) )
        return

    def __lineToPWMChannel( self, line: int ) -> int:
        """!
        @brief Determine the PWM channel on a chip for a given GPIO line.
        @param line GPIO line
        @return channel PWM chip channel
        """
        if line in [12, 13]:
            channel = line - 12
        elif isPi5():
            channel = line - 16
        else:
            channel = line - 18
        allowedList = [0, 1]
        if isPi5(): allowedList.extend( [2, 3] )
        if channel not in allowedList:
            raise GPIOError( 'Wrong GPIO line specified (GPIO{0})'
                             .format( line ) )
        return channel

    def start( self ):
        """!
        @brief Method to start a HW pulse.
        """
        if self.__burstTime:
            self.__burstTimer = threading.Timer( self.__burstTime,
                                                 self.stop )
        # this also sets the duty cycle
        self.frequency = self._frequency

        self.__writeDevice( 'enable', 1 )

        if self.__burstTimer:
            self.__burstTimer.start()
        return

    def stop( self ):
        """!
        @brief Method to stop the HW pulse; destroys the burst timer object if
               present.
        """
        if self.__burstTimer:
            self.__burstTimer.cancel()
            self.__burstTimer = None
        # the following looks messy---and it is.  There are sometimes glitches
        # with these devices
        try:
            self.__writeDevice( 'duty_cycle', 0 )
        except OSError:
            pass
        try:
            self.__writeDevice( 'enable', 0 )
        except OSError:
            pass
        return

    @property
    def dutyCycle( self ):
        """!
        @brief Works as read/write property to get the current duty cycle.
        @return current duty cycle
        """
        return self._dutyCycle

    @dutyCycle.setter
    def dutyCycle( self, value: float ):
        """!
        @brief Works as the setter of a read/write property to set the duty
               cycle.
        @param value new duty cycle to use 0 <= value <= 1
        """
        self._dutyCycle = value
        self.__writeDevice( 'duty_cycle',
                            self.__periodNs * self._dutyCycle )
        return

    @property
    def frequency( self ) -> float:
        """!
        @brief read property to get frequency to be implemented by child.
        @return current duty cycle
        """
        return self._frequency
  
    @frequency.setter
    def frequency( self, value: float ):
        """!
        @brief setter of a freqyency property to be implemented by child.
        @param value new frequency to use
        """
        self._frequency = value
        if self._frequency > 5000000:
            raise GPIOError( 'frequency {0} exceeds max frequency for hardware '
                             'pulse mode'.format( self._orgFreq ) )
        elif self._frequency < 0.1:
            raise GPIOError( 'frequency {0} below min frequency for hardware '
                             'pulse mode'.format( self._orgFreq ) )
        self._period = 1 / self._frequency
        self.__periodNs = self._period * 1000000000
        self.__writeDevice( 'duty_cycle', 0 )
        self.__writeDevice( 'period', self.__periodNs )
        self.__writeDevice( 'duty_cycle', self.__periodNs * self._dutyCycle )
        return


class _SWPulse( _PulseAPI ):
    """!
    @brief Internal child class to implement software PWM pulses.
    """
    def __init__( self,
                  pulsePin: Union[int, str, PinIO],
                  frequency: Union[float,object],
                  dutyCycle: float,
                  bursts: Union[int, None] ):
        """!
        @brief Constructor - sets up parameters.
        @param pulsePin integer with pin number in GPIO header or string with
                        GPIO<lineNumber>
        @param frequency in Hz as float or PObject with unit Hz
        @param duty cycle 0 < dutyCylce < 1
        @param bursts number of burts or None for continuous operation
        """
        self.__swTimer = None
        self.__pin = None
        self.__burstCount = 0
        super().__init__( pulsePin, frequency, dutyCycle, bursts )
        if self._bursts is None:
            self._bursts = -1
        if isinstance( pulsePin, PinIO ):
            if pulsePin.mode != PinIO.Mode.OUTPUT and \
               pulsePin.mode != PinIO.Mode.OPEN_DRAIN:
                raise GPIOError ( 'pulsePin must be in OUTPUT or OPEN_DRAIN '
                                  'mode' )
            self.__pin = pulsePin
        else:
            # TODO can we initialize that at level LOW?
            self.__pin = PinIO( pulsePin, PinIO.Mode.OUTPUT )
        self.__done = False
        return
        
    def __del__( self ):
        """!
        @brief Destructor - only meaningful on the Raspberry Pi and
               potentially during Unit Tests on the Raspberry Pi Pico.

        Properly destroys all objects that have been created by this class.
        """
        self.stop()
        if not isinstance( self._pulsePin, PinIO ):
            # We did not get the PinIO object fomr someone else
            # so we have to destroy it ourselves
            if self.__pin:
                self.__pin = None
        if self.__swTimer:
            self.__swTimer = None
        return

    def __str__( self ):
        """!
        @brief String representation of this class - returns all settable
               parametrs.
        """
        if self._bursts == -1:
            bursts = None
        else:
            bursts = self._bursts
        return 'pin: {0}, frequency: {1}, duty cycle: {2}, bursts: {3}, ' \
               'mode: SOFTWARE' \
               .format( self._pulsePin,
                        self._orgFreq,
                        self._dutyCycle,
                        bursts )

    def __runHigh( self ):
        """!
        @brief internal function to handle the "high" part of a software pulse.
        """
        if self.__done:
            return
        self.__nextTrigger += self._highTime
        self.__pin.level = PinIO.Level.HIGH
        self.__swTimer = threading.Timer( self.__nextTrigger - time.time(),
                                          self.__runLow )
        self.__swTimer.start()
        self.__burstCount += 1
        return

    def __runLow( self ):
        """!
        @brief internal function to handle the "low" part of a software pulse.
        """
        if self.__done:
            return
        self.__nextTrigger += self._lowTime
        self.__pin.level = PinIO.Level.LOW
        if self.__burstCount == self._bursts:
            self.__done = True
        self.__swTimer = threading.Timer( self.__nextTrigger - time.time(),
                                          self.__runHigh )
        self.__swTimer.start()
        return

    def start( self ):
        """!
        @brief Method to start the software pulse.
        """
        firstTimeCorrection = 0.000440
        self.frequency = self._frequency
        self.__nextTrigger = time.time() - firstTimeCorrection

        # we have to start with low, as the software pulse mechanism takes some 
        # time to "settle" - it is still not perfect, but the best we can do
        self.__runHigh()
        return

    def stop( self ):
        """!
        @brief Method to stop the software pulse.
        Closes and destroys the pin object, and, if present, the burst timer
        object.
        """
        
        self.__done = True
        if self.__swTimer: 
            self.__swTimer.cancel()
            self.__swTimer = None
        if self.__pin:
            self.__pin.level = PinIO.Level.LOW
        return

    @property
    def dutyCycle( self ):
        """!
        @brief Works as read/write property to get the current duty cycle.
        @return current duty cycle
        """
        return self._dutyCycle

    @dutyCycle.setter
    def dutyCycle( self, value: float ):
        """!
        @brief Works as the setter of a read/write property to set the duty
               cycle
        @param value new duty cycle to use 0 <= value <= 1
        """
        if self.__burstTime:
            raise GPIOError( 'Cannot set duty cycle during a burst in SW mode' )
        self._dutyCycle = value
        if value == 0: 
            self.__pin.level = PinIO.Level.LOW
        elif value == 1:
            self.__pin.level = PinIO.Level.HIGH
        else:
            self.__high = 1. / self._frequency * self._dutyCycle
            self.__low = 1. / self._frequency * (1. - self._dutyCycle)
        return

    @property
    def frequency( self ) -> float:
        """!
        @brief read property to get frequency to be implemented by child.
        @return current duty cycle
        """
        return self._frequency
  
    @frequency.setter
    def frequency( self, value: float ):
        """!
        @brief setter of a freqyency property to be implemented by child.
        @param value new duty cycle to use 0 <= value <= 1
        """
        if self._frequency > 2000:
            raise GPIOError( 'frequency {0} exceeds max frequency for '
                             'software mode'.format( self._orgFreq ) )
        self._frequency = value
        self._period = 1. / value
        self.__high = self._period * self._dutyCycle
        self.__low = self._period * (1. - self._dutyCycle)
        return




if "__main__" == __name__:
    import sys
    
    def main():
        """!
        @brief Unit test - coarse Python syntax test only.
        """
        
        o1 = Pulse( 'GPIO12', 1000 )
        o2 = Pulse( 'GPIO18', 1000 )
        
        del o1
        del o2
        
        print( '\nSUCCESS: no Python syntax errors detected\n' )
        
        return 0

    sys.exit( int( main() or 0 ) )
