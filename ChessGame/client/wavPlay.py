# -*- coding:utf-8 -*-
__author__ = 'gzs2218'

import winsound
class wavPlay(object):
    def __init__(self):
        pass

    def playStart(self):
        path = '..\\music\\start.wav'
        winsound.PlaySound(path, winsound.SND_ASYNC | winsound.SND_FILENAME)

    def playSetpiece(self):
        path = '..\\music\\set_piece.wav'
        winsound.PlaySound(path, winsound.SND_ASYNC | winsound.SND_FILENAME)

    def playWin(self):
        path = '..\\music\\win.wav'
        winsound.PlaySound(path, winsound.SND_ASYNC | winsound.SND_FILENAME)

    def playLose(self):
        path = '..\\music\\lose.wav'
        winsound.PlaySound(path, winsound.SND_ASYNC | winsound.SND_FILENAME)