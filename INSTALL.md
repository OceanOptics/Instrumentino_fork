Install Inlinino
================

Inlinino  package is composed of two softwares:
- `instrumentino`: run on a PC/Mac and provides the graphical user interface
                 for logging and visualizing the data
- `controlino`: run on the Arduino controller itself and communicates with
                instrumentino

If you're not planning on using an arduino to log analog data you can ignore
the step install Controllino.

## Installing Inlinino
Inlinino is written in python 2.7, so it runs on Windows, OSX and Linux.

Install python 2.7 on your OS.
Install the python package necessary to run the Inlinino:
<script>
  cd inlinino/instrumentino/setup.py
  python setup.py install
</script>

Everything should be setup you can now run Inlinino from one of the existing
system configurations or create your own configuration.

## Installing Controlino
Controlino is written in C++ and design to run on any Arduino device.

The simplest way to install Controlino is to use Arduino Software.
Steps-by-steps instructions for setting up the Arduino Software (IDE) on your
computer and connecting it to an Arduino board are available for your OS
following those links:
- [Windows](https://www.arduino.cc/en/Guide/Windows)
- [Mac OS X](https://www.arduino.cc/en/Guide/MacOSX)
- [Linux](https://www.arduino.cc/en/Guide/Linux)


Load controlino.cpp in the Arduino Software:
- in ~/Documents/Arduino create a folder Controlino/
- copy and rename controlino.cpp
  to ~/Documents/Arduino/Controlino/Controlino.ino
- load Controlino.ino from Arduino Software (File > Open...)

Comment/uncomment appropriate lines following instructions
between line 24 and 58 in Controlino.ino

Compile and upload Controlino to the Arduino board (using button on top left).