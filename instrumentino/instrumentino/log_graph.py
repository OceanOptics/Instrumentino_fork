from __future__ import division
__author__ = 'yoelk'
from datetime import datetime, timedelta
import wx
from wx import xrc
from instrumentino.comp import SysVarAnalog, SysVarDigital
from instrumentino import cfg
from itertools import cycle
import numpy as np
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
#from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
from matplotlib import pyplot as plt
from matplotlib.dates import DateFormatter, MinuteLocator, SecondLocator,\
    AutoDateFormatter, AutoDateLocator
from collections import deque

# class Data():
#     '''
#     A class to describe collected data
#     '''
#     def __init__(self, length):
#         self.data = []

class RingBufferNP():
    # Ring buffer based on numpy.roll for np.array
    # Same concept as FIFO except that the size of the numpy array does not vary
    def __init__(self, length):
        # initialize buffer with NaN values
        # length correspond to the size of the buffer
        self.data=np.empty(length, dtype='f')
        self.data[:]=np.NAN

    def extend(self, x):
        # Add np.array at the end of the buffer
        step = x.size
        self.data = np.roll(self.data, -step)
        self.data[-step:] = x

    def get(self, n=1):
        # return the most recent n element(s) in buffer
        return self.data[-1*n:]

    def getleft(self, n=1):
        # return the oldest n element(s) in buffer
        return self.data[0:n]


class RingBuffer():
    # Ring buffer based on deque for every kind of data
    def __init__(self, length):
        # initialize buffer with None values
        self.data=deque([None]*length, length);

    def extend(self, x):
        # Add x at the end of the buffer
        self.data.extend(x)

    def get(self, n=1):
        # return the most recent n element(s) in buffer
        return list(self.data)[-1*n:]

    def getleft(self, n=1):
        # return the oldest n element(s) in buffer
        return list(self.data)[0:n]


class AnalogData(RingBufferNP):
    '''
    A class to describe collected analog data
    '''
    def __init__(self, length, yRange):
        RingBufferNP.__init__(self, length)
        self.yRange = yRange


class LogGraphPanel(wx.Panel):
    '''
    A panel with a log graph
    adapted from examples by Eli Bendersky (eliben@gmail.com)
    '''
    def __init__(self, parent, sysComps):
        '''
        Creates the main panel with all the controls on it
        '''
        wx.Panel.__init__(self, parent)
        self.parent = parent
        self.sysComps = sysComps

        self.sizeBuffer = 5*60*4  # Number of point staying in memory (buffer)
        self.nData2log = 0        # Number of elements buffered since last write
        self.nData2plot = 0   # Number of data points available when start
        self.maxData2plot = 2*60*4  # Number of points to plot
                                  #     should be < sizeBuffer
        self.dataWriteBulk = 240  # Frequency at which update log file (~1min)
                                  #     should be < sizeBuffer
        self.logFileLength = 60   # Minutes before creating a new log file
                                  #     if > 1440 then feature is disable

        # add controls
        self.cb_freeze = wx.CheckBox(self, -1, "Freeze")
        self.Bind(wx.EVT_CHECKBOX, self.on_cb_freeze, self.cb_freeze)
        # self.slider_label = wx.StaticText(self, -1, "x-Zoom")
        # self.slider_zoom = wx.Slider(self, -1, value=1, minValue=1,
        #                              maxValue=60, name="x-Zoom", size=(200,29),
        #                              style=wx.SL_AUTOTICKS | wx.SL_LABELS | wx.SL_HORIZONTAL)
        # self.slider_zoom.SetTickFreq(10, 1)
        # self.Bind(wx.EVT_COMMAND_SCROLL_THUMBTRACK, self.on_slider_width, self.slider_zoom)

        # Get DPI of screen (Retina Screen not supported)
        screenSizeMMw, screenSizeMMh = wx.ScreenDC().GetSizeMM()
        screenSizePixw, screenSizePixh = wx.ScreenDC().GetSize()
        self.dpi = int(((screenSizePixw / screenSizeMMw) +
                        (screenSizePixh / screenSizeMMh)) / 2 * 25.4)
        if not (60 < self.dpi < 300):
            self.dpi = 100  # Setting DPI
        # set figure
        self.figure, self.axes = plt.subplots()
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.toolbar = NavigationToolbar(self.canvas)

        self.axes.set_xlabel('Time (min)', fontsize=12)
        self.axes.set_ylabel('Signal (%)', fontsize=12)
        self.axes.set_ybound(0,100)
        self.axes.xaxis_date()
        self.axes.get_xaxis().set_ticks([])
        self.axes.set_axis_bgcolor('white')

        self.figure.canvas.mpl_connect('pick_event', self.OnPick)

        # Show on screen
        self.controllersHBox = wx.BoxSizer(wx.HORIZONTAL)
        # self.controllersHBox.Add(self.slider_label, 0, wx.ALIGN_CENTER_VERTICAL)
        # self.controllersHBox.Add(self.slider_zoom, 0, wx.SHAPED | wx.FIXED_MINSIZE | wx.ALIGN_CENTER_VERTICAL)
        # self.controllersHBox.AddSpacer(29)
        self.controllersHBox.Add(self.cb_freeze, 0, wx.ALIGN_CENTER_VERTICAL)
        self.controllersHBox.AddSpacer(29)
        self.controllersHBox.Add(self.toolbar, 0, wx.ALIGN_TOP)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.canvas, 1, wx.EXPAND | wx.GROW | wx.ALL)
        self.vbox.Add(self.controllersHBox, 0, wx.ALIGN_RIGHT | wx.ALIGN_TOP)

        # fit all to screen
        self.parent.GetSizer().Add(self, 1, wx.EXPAND | wx.GROW | wx.ALL)
        self.SetSizer(self.vbox)
        self.vbox.Fit(self)

        # Set data sources
        # self.lastTime = None
        self.time = RingBuffer(self.sizeBuffer)
        # init time because matplot do not manage None values
        # base = datetime.today()
        # self.time.extend([base - timedelta(seconds=x/4) for x in range(self.maxData2plot, 0, -1)])
        self.analog = {}
        self.digital = {}
        self.all = {}
        self.all2plot = {}
        # self.realAnalogData = {}
        # self.plottedAnalogData = {}
        # self.digitalData = {}
        # self.allRealData = {}
        # Set plot var
        self.plottedLines = {}
        variableNamesOnLegend = []
        # Build set of colors and widths
        colors = ['b', 'g', 'r', 'c', 'm', 'b', 'y']
        colorCycler = cycle(colors)
        lineWidths = [1]*len(colors)+[2]*len(colors)+[4]*len(colors)
        lineWidthCycler = cycle(lineWidths)
        # List all components
        for comp in self.sysComps:
            # List all variables from each components
            for var in comp.vars.values():
                if not var.showInSignalLog:
                    continue

                # Get name of variable
                name = var.FullName()

                # Load Analogue
                if isinstance(var, SysVarAnalog):
                    # Initialize variable to store
                    self.analog[name] = AnalogData(self.sizeBuffer, var.range)

                    # Initialize line on figure
                    variableNamesOnLegend += [name]
                    color = next(colorCycler)
                    lineWidth = next(lineWidthCycler)
                    if var.showInSignalLog:
                        nameOnLegend = name + ' [' + str(var.range[0]) + ',' + str(var.range[1]) + ']'
                        graphVisible = True
                    else:
                        nameOnLegend = None
                        graphVisible = False
                    if not self.hasBipolarRange(name):
                        # self.plottedAnalogData[name] = AnalogData(var.range)
                        self.plottedLines[name] = self.axes.plot(
                            [datetime.now()],
                            [np.NAN],
                            '.-', lw=lineWidth, color=color,
                            label=nameOnLegend, visible=graphVisible)[0]

                    # else:
                    #     # split this variable to two unipolar variables for the sake of plotting
                    #     self.plottedAnalogData[name+'_POS'] = AnalogData([0,var.range[1]])
                    #     self.plottedAnalogData[name+'_NEG'] = AnalogData([var.range[0],0])

                    #     self.plottedLines[name+'_POS'] = self.axes.plot(self.time, self.plottedAnalogData[name+'_POS'].data,
                    #                                                     '-', lw=lineWidth, color=color, label=nameOnLegend, visible=graphVisible)[0]
                    #     self.plottedLines[name+'_NEG'] = self.axes.plot(self.time, self.plottedAnalogData[name+'_NEG'].data,
                    #                                                     '--', lw=lineWidth, color=color, visible=graphVisible)[0]

                # Load Digital
                if isinstance(var, SysVarDigital):
                    self.digital[name] = RingBufferNP(self.sizeBuffer)

                # Add copy to data to plot
                self.all2plot[name] = RingBufferNP(self.maxData2plot)

        # Set dictionnary all that points to analog and digital dictionnary
        self.all.update(self.analog)
        self.all.update(self.digital)

        # finalize legend
        self.axes.set_ybound(0,100)
        leg = self.axes.legend(loc='upper left', fancybox=False, shadow=False)
        leg.get_frame().set_alpha(0.4)
        self.lineLegendDict = {}
        for legline, lineName in zip(leg.get_lines(), variableNamesOnLegend):
            legline.set_picker(5)  # 5 pts tolerance
            self.lineLegendDict[legline] = lineName

        self.lineLegendDictReverseDict = {v: k for k, v in self.lineLegendDict.items()}

        # Set y-axis
        self.axes.get_xaxis().set_major_formatter(DateFormatter('%H:%M'))
        self.axes.get_xaxis().set_major_locator(MinuteLocator())
        #self.axes.set_ybound(0,100)


    def HideVariableFromLog(self, name):
        if not self.hasBipolarRange(name):
            plottedLines = [self.plottedLines[name]]
        else:
            plottedLines = [self.plottedLines[name+'_POS'],
                            self.plottedLines[name+'_NEG']]

        vis = not plottedLines[0].get_visible()
        for line in plottedLines:
            line.set_visible(vis)
        # Change the alpha on the line in the legend so we can see what lines
        # have been toggled
        legendLine = self.lineLegendDictReverseDict[name]
        if vis:
            legendLine.set_alpha(1.0)
        else:
            legendLine.set_alpha(0.2)
        self.figure.canvas.draw()


    def OnPick(self, event):
        # on the pick event, find the orig line corresponding to the
        # legend proxy line, and toggle the visibility
        legendLine = event.artist
        name = self.lineLegendDict[legendLine]
        self.HideVariableFromLog(name)


    def hasBipolarRange(self, name):
        return self.analog[name].yRange[0] * self.analog[name].yRange[1] < 0


    @staticmethod
    def NormalizePositiveValue(value, yRange):
        if value != None:
            # unipolar range [X, Y] or [-X, -Y]
            relevantEdge = yRange[0] if yRange[0] >= 0 else yRange[1]
            return abs(value - relevantEdge) / abs(yRange[1] - yRange[0]) * 100


    def AddData(self, name, value):
        # keep all data arrays the same length. the time array should be updated last
        #if len(self.all[name].data) <= len(self.time):
            # Set value to previous value if NaN
            # if value == None:
            #     value = self.allRealData[name].data[-1] if len(self.allRealData[name].data) > 0 else 0

            # Add data to main dictionnary
            self.analog[name].extend(np.array(value,'f'))

            # Normalize data and update plotting dictionnary
            # if name in self.analog.keys():
            #if not self.hasBipolarRange(name):
            normVal = LogGraphPanel.NormalizePositiveValue(value, self.all[name].yRange)
            self.all2plot[name].extend(np.array(normVal, 'f'))
            # else:
            #     normPosVal = self.NormalizePositiveValue(value, self.plottedAnalogData[name+'_POS'].yRange)
            #     normNegVal = self.NormalizePositiveValue(value, self.plottedAnalogData[name+'_NEG'].yRange)
            #     self.plottedAnalogData[name+'_POS'].data += [normPosVal if value>=0 else None]
            #     self.plottedAnalogData[name+'_NEG'].data += [normNegVal if value<0 else None]


    def FinishUpdate(self):
        # Update time and adjust number of data to log and plot
        self.time.extend([datetime.now()])
        self.nData2log += 1
        if self.nData2plot < self.maxData2plot:
            self.nData2plot += 1

        # create new file if first call, switch day, or maximum time for file
        if (cfg.signalsLogFile == None or
            cfg.timeCurrentSignalsLogFile.day != self.time.data[-1].day or
            self.time.data[-1] - cfg.timeCurrentSignalsLogFile >= timedelta(minutes=self.logFileLength)):
            # close previous file (if there is one)
            if cfg.signalsLogFile != None:
                if self.nData2log > 0:
                    self.WriteDataInLog(self.nData2log)
                cfg.signalsLogFile.close()
            # open new file
            filename = self.time.data[-1].strftime('%Y%m%d-%H%M%S') + '.csv'
            cfg.signalsLogFile = open(cfg.LogPath(filename), 'w')
            print "Writing data in {}".format(filename)
            cfg.timeCurrentSignalsLogFile = self.time.data[-1]
            # write a header with variable names
            cfg.signalsLogFile.write('time,' + str(self.all.keys())[1:-1] + '\r')
        else:
            # update the signals' file once in a while
            if self.nData2log == self.dataWriteBulk:
                self.WriteDataInLog(self.nData2log)

        # only show the graph when not frozen
        if not self.cb_freeze.IsChecked():
            self.Redraw()  #len(self.time) == 2)


    def StopUpdates(self):
        self.WriteDataInLog(self.nData2log)
        plt.close()


    def WriteDataInLog(self, _n):
        # No buffer, write directly
        for i in range(0,_n):
            cfg.signalsLogFile.write(str(self.time.get(_n)[i].strftime('%H:%M:%S.%f')) +
                                     ',' + str([v.get(_n)[i] for v in self.all.values()])[1:-1] + '\r')

        # With buffer (not working yet, bug with \n)
        # print str([str(self.time.get(_n)[i].strftime('%H:%M:%S.%f')) +\
        #         ',' + str([v.get(_n)[i] for v in self.all.values()])[1:-1] +\
        #         '\r\n' for i in range(0,_n)])[1:-1]
        # cfg.signalsLogFile.write(
        #         str([str(self.time.get(_n)[i].strftime('%H:%M:%S.%f')) +\
        #         ',' + str([v.get(_n)[i] for v in self.all.values()])[1:-1] +\
        #         '\r\n' for i in range(0,_n)])[1:-1]
        #         )

        # Reset data remaining to write in log
        self.nData2log = 0;


    def Redraw(self):  #, firstTime=False):
        """ Redraws the figure """
        if self.nData2plot > 2:
            # Update x-axis (if not frozen)
            if not self.cb_freeze.IsChecked():
                # self.axes.set_xbound(lower=self.time[max(0,len(self.time)-int(self.slider_zoom.GetValue() * 60 * cfg.app.updateFrequency))],
                                                     # upper=self.time[-1])
                self.axes.set_xbound(lower=self.time.data[-self.nData2plot], upper=self.time.data[-1])

            # Update data to plot
            for name in self.analog.keys():
                # print self.plottedAnalogData[name].data
                # print np.array(self.plottedAnalogData[name].data, dtype=np.float)
                self.plottedLines[name].set_xdata(self.time.get(self.nData2plot))
                self.plottedLines[name].set_ydata(self.all2plot[name].get(self.nData2plot))
                # self.plottedLines[name].set_ydata(np.append(self.plottedLines[name].get_ydata(), np.array(self.plottedAnalogData[name].data[-1], dtype=np.float)))
                # self.plottedLines[name].set_xdata(np.append(self.plottedLines[name].get_xdata(), self.time[-1]))

            # Update axes on first loop
            # if firstTime:
            #     self.axes.get_xaxis().set_major_formatter(DateFormatter('%H:%M'))
            #     self.axes.get_xaxis().set_major_locator(MinuteLocator())
            #     self.axes.set_ybound(0,100)

        self.canvas.draw()


    def on_cb_freeze(self, event):
        self.Redraw()


    def on_slider_width(self, event):
        self.Redraw()

##############################
class SimpleFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None)
        self.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
        self.panel = LogGraphPanel(self, [])

if __name__ == '__main__':
    app = wx.PySimpleApp()
    app.frame = SimpleFrame()
    app.frame.Show()
    app.MainLoop()
