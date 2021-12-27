A Python GPIO Abstraction Layer for the Raspberry Pi Family of Processors
=========================================================================

The Raspberry Pi family of processors consists mostly of inexpensive but
full-featured single-board computers running a Linux operating system; 
others are stand-alone Micro Computer Units (MCUs) not running any Operating 
System (OS) at all.  But Raspberry Pi computers also contain a set of General 
Purpose Input and Output (GPIO) Pins that allow "physical computing", i.e. 
the direct interaction of these computers with their physical environment 
via electrical signals that are both fully programmable and readable under 
program control.  To aid in the programming and examination of these electrical 
signals in Python, the go-to-programming-language on the Raspberry Pi, there 
exist several Python packages, such as pigpio, smbus, and smbus2, to name 
just the most popular ones.  All do more or less the same thing, have their 
own strengths and weaknesses but usually also have different Application 
Programming Interfaces (APIs).  Some of them are aptly documented; others 
are not.  There is basically no guidance for the uninitiated as to when to 
use which, and, in fact, depending on which GPIO functionality one needs, 
different packages have advantages over others, so it is often not possible 
to work with only one Python package.  To make matters worse, the Raspberry 
Pi family of processors also contains an MCU, the Raspberry Pi Pico, which 
has its own set of packages to handle GPIO, of course again with their own 
API.  To help navigate this "freedom of choice," which is highly praised in 
some parts of the Free and Open Source Software (FOSS) community, but 
otherwise often just referred to as mess, this GPIO_AL package was designed. 
It provides a common API across all Raspberry Pi platforms, including the 
Raspberry Pi Pico, and uses the most appropriate packages for each 
individual task "under the cover" and completely transparently for the 
programmer of higher level applications.  In other words, it forms an 
Abstraction Layer (AL) above the hardware and the plethora of its drivers 
with a consistent API across all platforms.  Thus, a particular "physical 
computing" application can be coded on one Raspberry Pi platform and then 
transferred to another without any code modifications.

In its humble beginnings, this GPIO_AL package consists of a class to handle the
configuration of I/O Pins, setting and reading their voltage levels, and the
ability to have user-code called whenever the voltage at those Pins changes.  It
further contains a class to handle I<sup>2</sup>C bus communication with 
peripheral devices, a communication scheme that has become vastly popular in 
recent years for a plethora of sensors.  Lastly, it contains an exception 
class to indicate that something went wrong and detailing exactly what and 
how severe it was.

For a complete documentation of this Python module, please see the docs 
directory https://ekkehard.github.io/RBPiGPIO_AL/.


Version History
---------------
* Rev. 1.0.0 -- Initial commit

License Information
-------------------
This code is _**Free and Open Source Software**_! 

Please see the LICENSE.md and COPYING.md files for more detailed license 
information. 