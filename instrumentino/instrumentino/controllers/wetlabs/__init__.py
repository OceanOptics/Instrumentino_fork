# -*- coding: utf-8 -*-
# @Author: nils
# @Date:   2016-04-08 16:22:19
# @Last Modified by:   nils
# @Last Modified time: 2016-04-11 18:50:21

# To check sensor is working correctly:
# On OSX:
#   screen /dev/tty.usbserial-FTZ267A6A 19200
#   close session with ctrl-A ctrl-\
#
# Column header in order:
#   %m/%d/%y
#   %H:%M:%S
#   wv(nm)
#   count
#   wv(nm)
#   count
#   wv(nm)
#   count
#   checksum (528) ???

# TODO user buffer of serialpy directly as cache

from __future__ import division

from serial import Serial
from threading import Thread
from time import sleep

from instrumentino.controllers import InstrumentinoController
from instrumentino import cfg
from instrumentino.comp import SysComp, SysVarAnalog


class WETLabs(InstrumentinoController):
    ''' This class implements an interface to serial WET Labs sensors '''
    # Inspired by class arduino from yoelk

    # Instrument name
    m_name = "WET Labs"

    # Cache
    m_countValuesCache = {}

    # Timer Event to update cache
    timer = None

    def __init__(self):
        InstrumentinoController.__init__(self, self.m_name)
        self.m_serial = Serial()
        # WET Labs serial communication constants
        self.m_serial.baudrate = 19200
        self.m_serial.bytesize = 8
        self.m_serial.parity = 'N'  # None
        self.m_serial.stopbits = 1
        self.m_serial.timeout = 1   # 1 Hz

    def Connect(self, _port):
        try:
            self.m_serial.port = _port
            self.m_serial.open()
        except:
            cfg.LogFromOtherThread('BB3 did not respond', True)
            return None

        if self.m_serial.isOpen():
            # Create thread to update cache
            thread = Thread(target=self.runCacheUpdate, args=())
            thread.daemon = True
            thread.start()
            return True
        else:
            return None

    def Close(self):
        if self.m_serial.isOpen():
            self.m_serial.close()

    def runCacheUpdate(self):
        while(True):
            sleep(self.m_serial.timeout)
            try:
                self.CacheUpdate()
            except:
                print "Unexpected error updating cache of WETLabs sensor"

    def CacheUpdate(self):
        # it is buffering so require to get data out now
        # self.m_serial.reset_input_buffer()
        data = self.m_serial.readline()
        if data:
            # There is data, update the cache
            data = data.split('\t')
            for i in range(2, 8, 2):
                self.m_countValuesCache[data[i]] = int(data[i + 1])
        else:
            # No data, cache is set to None
            for key in self.m_countValuesCache.keys():
                self.m_countValuesCache[key] = None

    def CacheRead(self):
        return self.m_countValuesCache

    def CountRead(self, _key):
        return self.m_countValuesCache[_key]


class SysCompWETLabs(SysComp):
    ''' A WET Labs count variable based on analog var '''

    def __init__(self, _name, _vars, _helpline=''):
        SysComp.__init__(self, _name, _vars, WETLabs, _helpline)

    def FirstTimeOnline(self):
        for var in self.vars.values():
            var.FirstTimeOnline()


class SysVarCountWETLabs(SysVarAnalog):
    ''' A WET Labs count variable based on analog var '''

    def __init__(self, _name, _rangeCount, _key,
                 _compName='', _helpline='', _units='',
                 _PreSetFunc=None, _PostGetFunc=None):
        showEditBox = (_PreSetFunc is not None)
        SysVarAnalog.__init__(self, _name, _rangeCount, WETLabs,
                              _compName, _helpline, showEditBox,
                              _units, _PreSetFunc, _PostGetFunc)
        self.m_key = _key

    def FirstTimeOnline(self):
        self.GetController().m_countValuesCache[self.m_key] = None

    def GetFunc(self):
        return self.GetController().CountRead(self.m_key)

# Simple example logging the data
if __name__ == '__main__':
    BB3_349 = WETLabs()

    # Connect with port
    BB3_349.Connect('/dev/tty.usbserial-FTZ267A6A')

    # UpdateCache 10 times
    for i in range(1, 10):
        BB3_349.CacheUpdate()
        print BB3_349.CacheRead()

    # Close connection
    BB3_349.Close()
