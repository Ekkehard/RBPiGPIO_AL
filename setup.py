# !/usr/bin/env python
"""
Setup script for GPIO_AL package
"""

from setuptools import setup
import os
description = open( os.path.join( os.path.dirname( __file__ ),
                                  'GPIO_AL',
                                  'README.md'), 
                    'r').read()
setup(
    name = 'GPIO_AL',
    packages = ['GPIO_AL'],
    include_package_data = True,
    package_data = {
        'GPIO_AL':[]
        },
    version = '2.0.0',
    description = 'GPIO Abstraction Layer',
    author = 'W. Ekkehard Blanz',
    author_email = 'Ekkehard.Blanz@gmail.com',
    url = 'https://github.com/Ekkehard/RBPiGPIO_AL.git',
    keywords = ['Raspberry Pi Pico', 'GPIO', 'Analog Input', 'PWM', 'I2C'],
    install_requires=[
        'setuptools', 
        'gpiod >= 2.2',
        'gpiozero'],
    license='LICENSE.md',
    classifiers = [
        'Programming Language :: Python',
        'Development Status :: release 2.0.0',
        'Intended Audience :: Raspberry Pi Programmers',
        'License :: Apache License',
        'Operating System :: Raspbian :: Debian :: Linux',
        'Topic :: GPIO',
        ],
    long_description = description
    )
 
