# -*- coding:utf-8 -*-
__author__ = 'gzs2218'

import math,sip
from PyQt4 import QtCore, QtGui
from PyQt4.Qt import *
from wavPlay import *

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

# 在本类中，0代表没有棋子，1代表白棋，2代表黑棋
NON_FLAG    =  0
WHITE_FLAG  =  1
BLACK_FLAG  =  2
class chessPlay(object):
    def __init__(self, name, chessBoard, inforShow):
        self.IsInto = False
        self.name = name
        self.score = None
        self.roomid = -1
        self.tableid = -1
        self.opponent = None
        self.IsReady = False
        self.IsBegin = False
        self.IsLeave = False
        self.IsNext = False
        self.chessType = NON_FLAG
        self.chessBoard = chessBoard
        self.inforShow = inforShow
        self.gridWidth = 32
        self.limit = 5
        self.list = [[(0, 0, NON_FLAG)] * 15 for i in range(15)]
        self.chessArr = [[(0, 0, NON_FLAG)] * 15 for i in range(15)]
        self.path = []
        self.wavplay = wavPlay()

    # 计算棋子该放置的坐标
    def locateTo(self, x, y):
        n = int(math.floor((x - self.limit) / self.gridWidth))
        m = int(math.floor((y - self.limit) / self.gridWidth))
        if n <= 0:
            n = 0
        elif n > 14:
            n = 14

        if m <= 0:
            m = 0
        elif m > 14:
            m = 14
        return n, m, self.gridWidth * n + 5, self.gridWidth * m + 5

    # 判断鼠标左键点击
    def pressEvent(self, curX, curY):
        if not self.IsBegin:
            return -1, -1
        if not self.IsNext:
            return -1, -1

        self.n, self.m, self.x, self.y = self.locateTo(curX, curY)
        if self.list[self.n][self.m][2] != 0:
            return -1, -1
        #更新之前一步所下棋的图案
        self.localUpdateLastChess()
        #绘制本次棋子
        self.list[self.n][self.m] = (float(self.x), float(self.y), self.chessType)
        self.path.append([self.n,self.m])
        self.chessArr[self.n][self.m] = QtGui.QGraphicsView(self.chessBoard)
        self.chessArr[self.n][self.m].setGeometry(QtCore.QRect(32, 32, 32, 32))
        if self.chessType == WHITE_FLAG:
            self.chessArr[self.n][self.m].setStyleSheet(_fromUtf8("background-image: url(:/images/white_before.png);"))
        else:
            self.chessArr[self.n][self.m].setStyleSheet(_fromUtf8("background-image: url(:/images/black_before.png);"))
        self.chessArr[self.n][self.m].setFrameShape(QtGui.QFrame.NoFrame)
        self.chessArr[self.n][self.m].show()
        self.wavplay.playSetpiece()
        self.chessArr[self.n][self.m].move(float(self.x), float(self.y))
        self.IsNext = False
        self.inforShow.setText("对手下".decode('utf-8'))
        self.chessBoard.update()
        return self.n, self.m

    #本地改变上一步的棋
    def localUpdateLastChess(self):
        if len(self.path) < 1:
            return
        else:
            n = self.path[-1][0]
            m = self.path[-1][1]
            x = float(n * self.gridWidth + self.limit)
            y = float(m * self.gridWidth + self.limit)
            if self.chessArr[n][m] != None:
                sip.delete(self.chessArr[n][m])
                self.chessArr[n][m] = None
            self.chessArr[n][m] = QtGui.QGraphicsView(self.chessBoard)
            self.chessArr[n][m].setGeometry(QtCore.QRect(32, 32, 32, 32))
            if self.chessType == WHITE_FLAG:
                self.chessArr[n][m].setStyleSheet(_fromUtf8("background-image: url(:/images/black_before.png);"))
            else:
                self.chessArr[n][m].setStyleSheet(_fromUtf8("background-image: url(:/images/white_before.png);"))
            self.chessArr[n][m].setFrameShape(QtGui.QFrame.NoFrame)
            self.chessArr[n][m].show()
            self.chessArr[n][m].move(x, y)
            self.chessBoard.update()

    #更改对手上一步的棋
    def opponentUpdateLastChess(self):
        if len(self.path) <= 1:
            return
        else:
            n = self.path[-2][0]
            m = self.path[-2][1]
            x = float(n * self.gridWidth + self.limit)
            y = float(m * self.gridWidth + self.limit)
            if self.chessArr[n][m] != None:
                sip.delete(self.chessArr[n][m])
                self.chessArr[n][m] = None
            self.chessArr[n][m] = QtGui.QGraphicsView(self.chessBoard)
            self.chessArr[n][m].setGeometry(QtCore.QRect(32, 32, 32, 32))
            if self.chessType == 2:
                self.chessArr[n][m].setStyleSheet(_fromUtf8("background-image: url(:/images/white_before.png);"))
            else:
                self.chessArr[n][m].setStyleSheet(_fromUtf8("background-image: url(:/images/black_before.png);"))
            self.chessArr[n][m].setFrameShape(QtGui.QFrame.NoFrame)
            self.chessArr[n][m].show()
            self.chessArr[n][m].move(x, y)
            self.chessBoard.update()

    #悔棋操作
    def backmove(self):
        if not self.path:
            return
        else:
            for i in range(2):
                n = self.path[-1][0]
                m = self.path[-1][1]
                self.path.pop()
                self.list[n][m] = (float(self.x), float(self.y), NON_FLAG)
                if self.chessArr[n][m] != None:
                    sip.delete(self.chessArr[n][m])
                    self.chessArr[n][m] = None
            # #改变之前棋子的图案
            # if self.path:
            #     for i in range(2):
            #         n = self.path[-i - 1][0]
            #         m = self.path[-i - 1][1]
            #         x = float(n * self.gridWidth + self.limit)
            #         y = float(m * self.gridWidth + self.limit)
            #         color = self.list[n][m][2]
            #         if self.chessArr[n][m] != None:
            #             sip.delete(self.chessArr[n][m])
            #             self.chessArr[n][m] = None
            #         self.chessArr[n][m] = QtGui.QGraphicsView(self.chessBoard)
            #         self.chessArr[n][m].setGeometry(QtCore.QRect(32, 32, 32, 32))
            #         if color == WHITE_FLAG:
            #             self.chessArr[n][m].setStyleSheet(_fromUtf8("background-image: url(:/images/white.png);"))
            #         else:
            #             self.chessArr[n][m].setStyleSheet(_fromUtf8("background-image: url(:/images/black.png);"))
            #         self.chessArr[n][m].setFrameShape(QtGui.QFrame.NoFrame)
            #         self.chessArr[n][m].show()
            #         self.chessArr[n][m].move(x, y)
            self.chessBoard.update()


    #清除棋盘数据
    def clearChessBoard(self):
        #清除原有棋子
        for i in range(len(self.path)):
            n = self.path[-1][0]
            m = self.path[-1][1]
            self.path.pop()
            self.list[n][m] = (float(self.x), float(self.y), 0)
            if self.chessArr[n][m] != None:
                sip.delete(self.chessArr[n][m])
                self.chessArr[n][m] = None
            self.chessBoard.update()
        #重新初始化数据
        self.list = [[(0, 0, NON_FLAG)] * 15 for i in range(15)]
        self.chessArr = [[(0, 0, NON_FLAG)] * 15 for i in range(15)]
        self.path = []

    #更新棋盘
    def updateChessBoard(self, n, m):
        other = WHITE_FLAG
        if self.chessType == WHITE_FLAG:
            other = BLACK_FLAG
        x = float(n * self.gridWidth + self.limit)
        y = float(m * self.gridWidth + self.limit)
        #更新之前棋子图案
        # self.opponentUpdateLastChess()
        #绘制当前棋子
        self.list[n][m] = (x, y, other)
        self.path.append([n,m])
        self.chessArr[n][m] = QtGui.QGraphicsView(self.chessBoard)
        self.chessArr[n][m].setGeometry(QtCore.QRect(32, 32, 32, 32))
        if other == WHITE_FLAG:
            self.chessArr[n][m].setStyleSheet(_fromUtf8("background-image: url(:/images/white.png);"))
        else:
            self.chessArr[n][m].setStyleSheet(_fromUtf8("background-image: url(:/images/black.png);"))
        self.chessArr[n][m].setFrameShape(QtGui.QFrame.NoFrame)
        self.chessArr[n][m].show()
        self.wavplay.playSetpiece()
        self.chessArr[n][m].move(x, y)
        self.IsNext = True
        self.inforShow.setText("我方下".decode('utf-8'))
        self.chessBoard.update()
        # print self.list

    #判断是否胜利
    def IsWin(self, x, y):
    #计算水平方向
        i = x
        j = y
        count = 0
        while i >= 0 and self.list[i][j][2] == self.chessType:
            i -= 1
            count += 1
        i = x + 1
        while i < 15 and self.list[i][j][2] == self.chessType:
            i += 1
            count += 1
        if count >= 5:
            return True

        #计算竖直方向
        i = x
        count = 0
        while j >= 0 and self.list[i][j][2] == self.chessType:
            j -= 1
            count += 1
        j = y + 1
        while j < 15 and self.list[i][j][2] == self.chessType:
            j += 1
            count += 1
        if count >= 5:
            return True

        #计算左上右下方向
        j = y
        count = 0
        while i >= 0 and j >= 0 and self.list[i][j][2] == self.chessType:
            i -= 1
            j -= 1
            count += 1
        i = x + 1
        j = y + 1
        while i < 15 and j < 15 and self.list[i][j][2] == self.chessType:
            i += 1
            j += 1
            count += 1
        if count >= 5:
            return True

        #计算右上左下方向
        i = x
        j = y
        count = 0
        while i < 15 and j >= 0 and self.list[i][j][2] == self.chessType:
            i += 1
            j -= 1
            count += 1
        i = x - 1
        j = y + 1
        while i >= 0 and j < 15 and self.list[i][j][2] == self.chessType:
            i -= 1
            j += 1
            count += 1
        if count >= 5:
            return True
        return False
