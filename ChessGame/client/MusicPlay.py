__author__ = 'gzs2218'
# -*-coding: utf-8 -*-
import ctypes, time

from PyQt4.QtCore import *
from lib import winamp
from ctypes.wintypes import *

#音乐播放线程
class MusicPlay(QThread):
    def __init__(self, parent = None):
        super(MusicPlay, self).__init__(parent)
        self.name = ''
        self.IsPaused = True

    #播放
    def play(self, name):
        self.name = name
        # print 'hello',name
        self.start()

    #暂停
    def pause(self):
        # if winamp.ispaused():
        #     self.play(self.name)
        # else:
        if self.IsPaused:
            winamp.pause(False)
            self.IsPaused = False
        else:
            winamp.pause(True)
            self.IsPaused = True

    #停止
    def stop(self):
        winamp.stop()

    #新线程
    def run(self):
        info = winamp.fileinfo(self.name)
        print info
        def ms2time(ms):
            if ms <= 0: return '00:00:000'
            time_sec, ms = ms / 1000, ms % 1000
            time_min, time_sec = time_sec / 60, time_sec % 60
            time_hor, time_min = time_min / 60, time_min % 60
            if time_hor == 0: return '%02d:%02d:%03d'%(time_min, time_sec, ms)
            return '%02d:%02d:%02d:%03d'%(time_hor, time_min, time_sec, ms)

        #print 'Playing "%s" (%s), press \'q\' to exit ....'%(info[0], name)
        winamp.play(self.name)
        user32 = ctypes.windll.user32
        while 1:
            user32.GetAsyncKeyState.restype = WORD
            user32.GetAsyncKeyState.argtypes = [ ctypes.c_char ]
            if user32.GetAsyncKeyState('Q'): break
            time.sleep(0.1)
            print '[%s / %s]\r'%(ms2time(winamp.gettime()), ms2time(winamp.getlength())),
            if (winamp.gettime() > 0) and (winamp.gettime() > winamp.getlength() - 3000):
                winamp.settime(0)
        print '\nstopped'
        quit()