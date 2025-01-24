# Python Implementation: GPIO_AL
# -*- coding: utf-8 -*-
##
# @file       __init__.py
#
# @mainpage   Raspberry Pi GPIO Abstraction Layer
#
# This module provides a Python abstraction layer for the Raspberry Pi General 
# Purpose I/O (GPIO) functionality for all models of the regular Raspberry Pi 
# from RP0 0 and up as well as the Raspberry Pi Pico.  Using this module, higher
# level code, including user space Python device drivers, should run and use the
# common API of the GPIO_AL shared by all Raspberry Pi architectures without 
# modifications on all those architectures.
#
# The main purpose for the creation of this module was the recognition of a dire 
# need for a stable API in spite of the changing platform, inherent to the 
# evolving Raspberry Pi hardware ecosystem.  Unfortunately, the various existing 
# Python packages dealing with GPIO functionality could not keep up with the 
# sometimes rather drastic changes in the Raspberry Pi hardware architecture as 
# they fell apart when the hardware changed and the register bit-banging no 
# longer worked.  Therefore, this code is restricted to standard-Linux device 
# file interfaces in the hope, that they prove to be more stable than register-
# based operations and generaly does not rely on other packages to do so.  The 
# only exception is the direct bit-I/O where this package relies on the libgpiod
# standard Linux library and its Python binding gpiod.  This Python binding in 
# particular has undergone drastic API changes in rev. 2.0, but the hope is that 
# it, like the Linux device-file interface will remain relatively stable from 
# here on forward.  Only the future can tell whether this hope was justified.
# As far as this package is concerned, its API has been upward compatible since 
# its inception.
#
# This package consists of three major parts, general Bit-I/O, pulse generation,
# and serial bus communication.  The first part is subdivided into single bit and
# parallel I/O, the second one in software and hardware-generated pulses, and the
# third one provides software to handle standard serial busses.  Currently, only 
# the I<sup>2</sup>C bus is supported, but more busses will be implemented as the 
# need arises.
#
# This code has been tested on a Raspberry Pi 0, 3, 4 and 5 and a Raspberry Pi 
# Pico.
#
# @version    2.0.0
#
# @par Comments
# This is Python 3 code!  PEP 8 guidelines are decidedly NOT followed in some
# instances, and guidelines provided by "Coding Style Guidelines" a "Process
# Guidelines" document from WEB Design are used instead where the two differ,
# as the latter span several programming languages and are therefore also 
# applicable to projects that require more than one programming language; it 
# also provides consistency across hundreds of thousands of lines of legacy 
# code.  Doing so, ironically, is following PEP 8, which speaks highly of the 
# wisdom of the authors of PEP 8.
# @par Known Bugs
# None
#
# @author
# W. Ekkehard Blanz <Ekkehard.Blanz@gmail.com>
#
# @copyright
# Copyright (C) 2021 - 2025 W. Ekkehard Blanz\n

#      Date         | Author         | Modification
#   ----------------+----------------+------------------------------------------
#   Fri Nov 15 2024 | Ekkehard Blanz | created
#   Mon Jan 13 2025 | Ekkehard Blanz | Doxygen documentation added
#                   |                |

"""
This module provides a Python abstraction layer for the Raspberry Pi General 
Purpose I/O (GPIO) functionality for all models of the regular Raspberry Pi 
from RP0 0 and up as well as the Raspberry Pi Pico.  Using this module, higher
level code, including user space Python device drivers, should run and use the
common API of the GPIO_AL shared by all Raspberry Pi architectures without 
modifications on all those architectures.

This package consists of three major parts, general Bit-I/O, pulse generation,
and serial bus communication.  The first part is subdivided into single bit and
parallel I/O, the second one in software and hardware-generated pulses, and the
third one provides software to handle standard serial busses.  Currently, only 
the I<sup>2</sup>C bus is supported, but more busses will be implemented as the 
need arises.
"""

from .GPIOError import GPIOError
from .PinIO import PinIO
from .Pulse import Pulse
from .I2Cbus import I2Cbus
from .tools import platform, isPico, isPi5, cpuInfo, isHWpulsePin, hwPWMlines
