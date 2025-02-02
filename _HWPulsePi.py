# Python Implementation: _HWPulsePi
##
# @file       _HWPulsePi.py
#
# @version    2.0.0
#
# @par Purpose
# Provide hardware generated pulses for the Pulse class of the GPIO_AL module.
#
# This code has been tested on a Raspberry Pi 0, 3, 4 and 5 and a Raspberry Pi 
# Pico.
#
# This class is the only class that needs to be modified should the RB Pi 
# hardware PWM mechanism ever change.
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
#   Fri Jan 31 2025 | Ekkehard Blanz | extracted from Pulse.py
#                   |                |

import os
import time
from GPIO_AL.tools import isPi5, argToLine, _hwPulseChip
from GPIO_AL.GPIOError import GPIOError
from GPIO_AL._PulseAPI import _PulseAPI

class _HWPulsePi( _PulseAPI ):
    """!
    @brief Internal child class to implement hardware PWM pulses on a Raspbery 
           Pi.
    
    If the RB Pi hardware PWM support changes, this is the only class that needs
    to be touched.  Be mindful to keep the API determined by PulseAPI as is. 
    """
    def __init__( self,
                  pulsePin,
                  frequency,
                  dutyCycle,
                  bursts ):
        """!
        @brief Constructor - sets up parameters.
        @param pulsePin integer with pin number in GPIO header or string with
                        GPIO<lineNumber>
        @param frequency in Hz as float or PObject with unit Hz
        @param dutyCycle duty cycle 0 <= dutyCylce <= 1
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

    def __writeDevice( self, device, param ):
        """!
        @brief write a given parameter to a given PWM device.
        @param device one of 'period', 'duty_cycle, or 'enable'
        @param numerical parameter
        """
        with open( os.path.join( self.__deviceDir, device ), 'w' ) as f:
            f.write( '{0}\n'.format( round( param ) ) )
        return

    def __lineToPWMChannel( self, line ):
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
    def dutyCycle( self, value ):
        """!
        @brief Works as the setter of a read/write property to set the duty
               cycle.
        @param value new duty cycle to use 0 <= value <= 1
        """
        if value > 1 and value <= 100:
            self._dutyCycle = value / 100.
        else:
            self._dutyCycle = value
        if self._dutyCycle < 0 or self._dutyCycle > 1:
            raise GPIOError( 'Wrong duty cycle specified: {0}'
                             .format( dutyCycle ) )
        self.__writeDevice( 'duty_cycle',
                            self.__periodNs * self._dutyCycle )
        return

    @property
    def frequency( self ):
        """!
        @brief read property to get frequency.
        @return current duty cycle
        """
        return self._orgFreq
  
    @frequency.setter
    def frequency( self, value ):
        """!
        @brief setter of a freqyency property.
        @param value new frequency to use
        """
        try:
            if str( value.unit ) != 'Hz':
                raise GPIOError( 'Wrong frequency object specified: {0}'
                                 .format( value ) )
        except AttributeError:
            pass
        if float( value ) > 5000000:
            raise GPIOError( 'frequency {0} exceeds max frequency for hardware '
                             'pulse mode'.format( value ) )
        elif float( value ) < 0.1:
            raise GPIOError( 'frequency {0} below min frequency for hardware '
                             'pulse mode'.format( value ) )
        self._frequency = float( value )
        self._orgFreq = value
        self._period = 1 / self._frequency
        self.__periodNs = self._period * 1000000000
        self.__writeDevice( 'duty_cycle', 0 )
        self.__writeDevice( 'period', self.__periodNs )
        self.__writeDevice( 'duty_cycle', self.__periodNs * self._dutyCycle )
        return
