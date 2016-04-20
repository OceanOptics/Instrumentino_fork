from __future__ import division
import wx
import wx.xrc
from wx.lib import wordwrap #  Used in help/about
# import time
# import threading
import sys
from datetime import datetime
import subprocess
from instrumentino import cfg
from instrumentino.log_graph import LogGraphPanel
from instrumentino.controllers.arduino import \
    SysVarAnalogArduinoUnipolar,\
    SysVarAnalogArduinoBipolarWithExternalPolarity, SysVarDigitalArduino
from instrumentino.controllers.arduino.pins import AnalogPins, DigitalPins

__author__ = ['yoelk', 'doizuc']


class InstrumentinoApp(wx.App):
    '''
    This class implements the application
    '''
    monitorUpdateDelayMilisec = 250
    # Arduino.cacheReadDelayMilisec
    updateFrequency = 1000 / monitorUpdateDelayMilisec
    maxDataGapSeconds = 5

    def __init__(self, system):
        self.system = system
        self.sysComps = self.system.comps
        self.sysActions = self.system.actions
        wx.App.__init__(self, False)

        self.lastUpdateTime = datetime.now()

    def OnInit(self):
        '''
        Load the main window from the main.xrc
        '''
        self.mainXrc = wx.xrc.XmlResource(
            cfg.ResourcePath('mainSignalsOnly.xrc'))
        self.InitFrame()
        return True

    def InitFrame(self):
        '''
        Init the main window
        '''
        self.listButtons = []
        self.runButtons = []
        self.mainFrame = self.mainXrc.LoadFrame(None, 'mainFrame')
        self.splitter = wx.xrc.XRCCTRL(self.mainFrame, 'splitter')
        self.mainFrame.SetTitle(self.system.name)
        self.mainFrame.Bind(wx.EVT_CLOSE, self.OnClose)

        # Set icon
        _icon = wx.EmptyIcon()
        _icon.CopyFromBitmap(wx.Bitmap(
            cfg.ResourcePath('Inlinino.ico'),
            wx.BITMAP_TYPE_ICO))
        self.mainFrame.SetIcon(_icon)

        # log
        self.logGraph = LogGraphPanel(
            wx.xrc.XRCCTRL(self.mainFrame, 'logGraphPage'), self.sysComps)
        self.Connect(-1, -1, cfg.EVT_LOG_UPDATE, self.OnLogUpdate)

        # update framework
        cfg.InitVariables(self)

        # Menu
        self.mainFrame.Bind(
            wx.EVT_MENU, self.OnClose, id=wx.xrc.XRCID('quitMenuItem'))
        self.mainFrame.Bind(
            wx.EVT_MENU, self.OnAbout, id=wx.xrc.XRCID('aboutMenuItem'))
        self.mainFrame.Bind(
            wx.EVT_MENU, self.OnSupport, id=wx.xrc.XRCID('supportMenuItem'))

        menusDict = dict(self.mainFrame.GetMenuBar().GetMenus())
        commMenu = [
            key for key, value in menusDict.iteritems() if value == 'Comm'][0]
        for comp in self.sysComps:
            cfg.AddControllerIfNeeded(comp.controllerClass)

        for controller in cfg.controllers:
            menu = commMenu.Append(-1, controller.name,
                                   'Connect the ' + controller.name)
            self.mainFrame.Bind(wx.EVT_MENU, controller.OnMenuConnect, menu)

        # sysCompsPanel (display analog and digital values)
        self.sysCompsPanel = wx.xrc.XRCCTRL(self.mainFrame, 'sysCompsPanel')
        sysCompsPanelBoxSizer = self.sysCompsPanel.GetSizer()
        for sysComp in self.sysComps:
            panel = sysComp.CreatePanel(self.sysCompsPanel)
            if panel is not None:
                sysCompsPanelBoxSizer.Add(panel)
        # make all sysComps fill their given area
        for sysCompPanel in sysCompsPanelBoxSizer.GetChildren():
            sysCompPanel.SetFlag(wx.GROW)
        sysCompsPanelBoxSizer.Fit(self.mainFrame)

        # main frame
        self.splitter.SetSashPosition(400, True)
        self.mainFrame.GetSizer().Fit(self.mainFrame)
        # self.UpdateControls()
        self.mainFrame.Show()

        # Monitor periodically (base on wxTimer event)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.MonitorUpdate, self.timer)
        self.timer.Start(self.monitorUpdateDelayMilisec)
        # Monitor periodically (based on threading and time)
        #   no difference with wxTimer and error are not handle very well
        # thread = threading.Thread(target=self.runMonitorUpdate, args=())
        # thread.daemon = True                            # Daemonize thread
        # thread.start()                                  # Start the execution

        # Avoid system to go to sleep
        if 'darwin' in sys.platform:
            print('Running \'caffeinate\' on MacOSX '
                  'to prevent the system from sleeping')
            subprocess.Popen('caffeinate')

    def OnLogUpdate(self, event):
        ''' Update log '''
        (text, critical) = event.data
        # cfg.Log(text)
        if critical:
            dlg = wx.MessageDialog(self.mainFrame,
                                   text,
                                   'Error', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

    def OnClose(self, event):
        '''
        Close the application
        '''
        dlg = wx.MessageDialog(self.mainFrame,
                               "Do you really want to close?\n" +
                               "Data is saved automatically.",
                               "Confirm Exit", wx.OK | wx.CANCEL)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            cfg.userStopped = True
            self.timer.Stop()

            cfg.logGraph.StopUpdates()
            if cfg.signalsLogFile is not None:
                cfg.signalsLogFile.close()

            cfg.Close()

            self.mainFrame.Destroy()

    def OnSupport(self, evt):
        ''' Show support dialog'''
        dlg = wx.MessageDialog(self.mainFrame,
                               'Send questions, bug reports, fixes, '
                               'enhancements, t-shirts, money, lobsters & '
                               'beers to Nils\n'
                               '<nils.haentjens+inlinino@maine.edu>',
                               'A question ? Bug ? Error ?',
                               wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def OnAbout(self, evt):
        '''
        Show about dialog
        '''
        # First we create and fill the info object
        info = wx.AboutDialogInfo()
        info.Name = self.system.name
        info.Version = self.system.version
        #info.Copyright = "2014 University of Basel - 2016 Univeristy of Maine"
        info.Description = wx.lib.wordwrap.wordwrap(
            self.system.description +
            '\r\nThis software is based on the instrumentino framework.',
            350, wx.ClientDC(self.mainFrame))
        # info.WebSite = ('http://www.chemie.unibas.ch/~hauser/'
        #                 'open-source-lab/instrumentino/index.html')
        info.Developers = [
            'Joel Koenka (University of Basel)',
            'Nils Haentjens (Univeristy of Maine) '
            '<nils.haentjens+inlinino@maine.edu>']

        info.License = wx.lib.wordwrap.wordwrap(
            'This software is released under GPLv3. The code is hosted on '
            'GitHub: https://github.com/OceanOptics/Inlinino and is a fork '
            'from this repo: https://github.com/yoelk/instrumentino\n'
            'When using the sofware for scientific publications, the based '
            'software Instrumentino is happy to be cited by'
            ' the release article: http://www.sciencedirect.com/science/'
            'article/pii/S0010465514002112',
            500, wx.ClientDC(self.mainFrame))

        # Then we call wx.AboutBox giving it that info object
        wx.AboutBox(info)

    # def runMonitorUpdate(self):
    # Alternative to wxtimer (not working on OSX while app in background)
    #     while(True):
    #         self.MonitorUpdate()
    #         time.sleep(1/self.updateFrequency)

    def MonitorUpdate(self, event=None):
        '''
        Read system variables' values from controllers
        '''
        # Check time of last update to look for gaps in data
        # to test this section of code use:
        #       kill -STOP [PID] to pause the process
        #       kill -CONT [PID] to resume the process
        timeNow = datetime.now()
        if (cfg.AllOnline() and
                (timeNow - self.lastUpdateTime).seconds >
                self.maxDataGapSeconds):
            print 'Paused between ', self.lastUpdateTime, timeNow
            cfg.LogFromOtherThread('Program was paused between' +
                                   self.lastUpdateTime.strftime('%H:%M:%S') +
                                   ' and ' + timeNow.strftime('%H:%M:%S'),
                                   True)
        self.lastUpdateTime = timeNow

        # Update cached variables from controllers
        for comp in self.sysComps:
            if cfg.IsCompOnline(comp):
                comp.Update()

        # Update signalLogFile and plot
        if cfg.AllOnline():
            self.logGraph.FinishUpdate()


class SavedFile(object):
    '''
    Describe a system dependent saved file
    '''

    def __init__(self, systemUid, list):
        self.systemUid = systemUid
        self.list = list


class Instrument():
    '''
    an instrument parent class
    '''

    def __init__(self, comps, actions, version='1.0', name='Instrument',
                 description='Instrument\'s description'):
        self.comps = comps
        self.actions = actions
        self.version = version
        self.name = name
        self.description = description

        self.StartApp()

    def GetSystemUid(self):
        '''
        Return a unique id for the instrument
        '''
        # return self.name + self.version + self.description
        return self.name + '_' + self.version

    def StartApp(self):
        '''
        Run application
        '''
        app = InstrumentinoApp(self)
        app.MainLoop()

#################################
# make a simple example to demonstrate some of the GUI capabilities
# Use an Arduino to track the values of two analog pins.
# The first has a unipolar positive range (0 to 5 V).
# The second has a unipolar negative range (-5 to 0 V).
# The third has a bipolar range (-5 to 5 V) while a digital pin sets the
# polarity.
if __name__ == '__main__':
    '''
    *** System constants
    '''
    # pin assignments
    pinAnal_unipolarPositive = 0
    pinAnal_unipolarNegative = 1
    pinAnal_bipolar = 2
    pinDigi_polarity = 2

    '''
    *** System components
    '''
    polarityVariable = SysVarDigitalArduino('polarity', pinDigi_polarity)

    def SetPolarityPositiveFunc():
        pass

    def GetPolarityPositiveFunc():
        return polarityVariable.Get() == 'on'

    analPins = AnalogPins('analog pins',
                          (SysVarAnalogArduinoUnipolar(
                               'unipolar +', [0, 5], pinAnal_unipolarPositive,
                               None, units='V'),
                           SysVarAnalogArduinoUnipolar(
                               'unipolar -', [-5, 0], pinAnal_unipolarNegative,
                               None, units='V'),
                           SysVarAnalogArduinoBipolarWithExternalPolarity(
                               'bipolar', [-5, 5], pinAnal_bipolar, None,
                               SetPolarityPositiveFunc,
                               GetPolarityPositiveFunc,
                               units='V'),))

    digiPins = DigitalPins('digital pins',
                           (polarityVariable,))

    '''
    *** System
    '''
    class System(Instrument):
        def __init__(self):
            comps = (analPins, digiPins)
            actions = ()
            name = 'Basic Arduino example'
            description = '''Basic Arduino example.\n
                Use an Arduino to track the values of two analog pins.\n
                The first has a unipolar positive range (0 to 5 V).\n
                The second has a unipolar negative range (-5 to 0 V).\n
                The third has a bipolar range (-5 to 5 V) while a digital
                pin sets the polarity.'''
            version = '1.0'

            Instrument.__init__(
                self, comps, actions, version, name, description)

    '''
    *** Run program
    '''
    System()
