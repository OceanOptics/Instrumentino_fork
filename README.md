Inlinino - Instrumentino v1 Fork
=============================
_A simple data logger_

## Purpose of the project
Inlinino is design to log data from sensors (with analog or serial interface)
continuisly during days. It is written in Python 2.7 and is a fork from
Instrumentino. The user interface is very simple and allow visualization of the
data in real-time. To date, the software can log data from the analog and
digital ports of an Arduino and from WETLabs ECO series sensors.

Instrumentino is an open-source modular graphical user interface framework for
controlling Arduino based experimental instruments and any other instrument
for which python API exist or can be developped.

## Differences between Instrumentino v1 and Inlinino
The main difference between Instrumentino and Inlinino resids in the fact that
Instrumentino is build to control instruments during short period of time
(less than a day) whereas inlinino can only read data from those instruments
but during an extensive period of time. In fact, inlinino use a ring buffer to
plot and log data whereas instrumentino use a classic list that keeps expending
as the program run. Inlinino is creating hourly log files and will create a new
log file at midnight when switching day. A big part of instrumentino's code was
removed in order to make the software lighter but it can easily be added back.

## Content of the application
Two separate programs:
- `instrumentino`: run on a PC/Mac and provides the graphical user interface
                 for logging and visualizing the data
- `controlino`: run on the Arduino controller itself and communicates with
                instrumentino

The other folder contains:
- `configurations`: python scripts to start inlinino with a given configuration

## Starting Inlinino
After following the installation steps described in INSTALL.md, Inlinino can be started for a specific configuration.
On OSX:
```
cd configurations/test/
nice -20 pythonw __main__.py
```
Note: use `nice` to set the application priority by (-20 is the highest), use `pythonw` instead of `python` to show the GUI of the application.
On Windows:
- Navigate to configurations\test\ or another configuration\Tara\
- Launch the applicaion by double clicking `__main__.py` or `__main__.pyw`
Note: by default *.py are started with `python.exe` and *.pyw are started by `pythonw.exe`. `python.exe` will start with a terminal window and will show any error or print statement ouput by the application whereas `pythonw.exe` will
show only the GUI of the application and no error is shown.

## Credits
This fork of Instrumentino was written by Nils (University of Maine).
Thank you to yoelk for sharing is work.

_"We are looking forward for contributors.
There is lots of potential for Instrumentino to grow!
Please contact me if you want to add features and make Instrumentino better.
yoelk [at] tx.technion.ac.il"_ `Yoelk`
