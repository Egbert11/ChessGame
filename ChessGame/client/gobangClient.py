# -*- coding: utf-8 -*-
__author__ = 'gzs2218'

import json,time,sys
sys.path.append("..")
from server import netstream
from ui_Game import Ui_MainWindow
from chessPlay import *
from PyQt4 import QtGui
from PyQt4.Qt import *
from wavPlay import *
from lib import winamp
from MusicPlay import *


class GobangClient(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self, ip, port, username, ns):
        QtGui.QMainWindow.__init__(self, None)
        self.ip = ip
        self.port = port
        self.username = username
        self.ns = ns

    #初始化配置
    def __init_config(self):
        self.tableList = [ 0 for x in range(0,25)]
        self.scoreList = {}
        self.timer = QTimer()
        self.loopCount = 40
        self.tickCount = 100
        self.FirstTime = True
        # self.musicPlay = wavPlay()
        self.bgPlay = MusicPlay()
        indll = 'lib/in_mp3.dll'
        outdll = 'lib/out_wave.dll'
        if winamp.init(indll, outdll):
            print 'cannot load plugins'
            sys.exit(0)
        self.bgPlay.play('music/bg.mp3')
        self.bgIsPlay = True
        self.bgPlay.IsPaused = False
        self.wavplay = wavPlay()

    #初始化Ui
    def __init_ui(self):
        self.setupUi(self)
        self.setWindowTitle(self.username)
        self.userInfo = chessPlay(self.username, self.chessBoard, self.inforShow)
        self.setButtonStatus(False, False, False, False, False, False)
        #将两个聊天对话框设为只读
        self.groupTalk.setReadOnly(True)
        # self.groupTalk.moveCursor(QtGui.QTextCursor.End)
        self.singleTalk.setReadOnly(True)
        # self.singleTalk.moveCursor(QtGui.QTextCursor.End)

        self.connect(self.start, SIGNAL('clicked()'), self.startChess)
        self.connect(self.undo, SIGNAL('clicked()'), self.undoChess)
        self.connect(self.left, SIGNAL('clicked()'), self.leaveChess)
        self.connect(self.again, SIGNAL('clicked()'), self.againChess)
        self.connect(self.giveUp, SIGNAL('clicked()'), self.loseChess)

    def __connect(self):
        #进入房间
        self.room.itemDoubleClicked.connect(self.intoTable)
        #定时器触发
        self.connect(self.timer, SIGNAL("timeout()"), self.check)
        #发送群聊消息
        self.connect(self.groupSend, SIGNAL("clicked()"),self.sendGroupMessage)
        self.connect(self.groupEdit, SIGNAL("returnPressed()"), self.sendGroupMessage)
        #房间聊天
        self.connect(self.singleSend, SIGNAL("clicked()"),self.sendSingleMessage)
        self.connect(self.singleEdit, SIGNAL("returnPressed()"), self.sendSingleMessage)
        #背景音乐控制
        self.connect(self.bgMusic, SIGNAL("clicked()"), self.controlBgMusic)


    # 设置按钮状态
    def setButtonStatus(self, startStatus, giveUpStatus, undoStatus, againStatus, leftStatus, singleSendStatus):
        self.start.setEnabled(startStatus)
        self.giveUp.setEnabled(giveUpStatus)
        self.undo.setEnabled(undoStatus)
        self.again.setEnabled(againStatus)
        self.left.setEnabled(leftStatus)
        self.singleSend.setEnabled(singleSendStatus)

    #启动和服务端的连接
    def startup(self):
        # self.ns = netstream.netstream(8)
        # self.ns.connect(self.ip, self.port)
        self.__init_config()
        self.__init_ui()
        self.__connect()
        # self.login_success_caller('Connected to remote host. Start sending messages')
        self.timer.start(50)

    # 客户端轮询函数
    def check(self):
        # while not shutdown:
        self.clientConfig()
        # time.sleep(0.05)
        self.ns.process()
        if self.ns.status() == netstream.NET_STATE_ESTABLISHED:
            # while True:
            data = self.ns.recv()
            # print 'data:%s'%data
            if len(data) > 0:
                data = json.loads(data)
                #查询能否进入房间
                # print data
                if data['sid'] == 100:
                    if data['cid'] == 1001:
                        self.tableList = data['tableList']
                    elif data['cid'] == 1003:
                        if data['roomid'] == self.userInfo.roomid - 1 and data['tableid'] == self.userInfo.tableid - 1:
                            self.inforShow.setText("你的对手离开\n了房间".decode('utf-8'))
                            self.player2.setText("玩家2：".decode('utf-8'))
                            self.score_player2.setText("分数：".decode('utf-8'))
                            self.setButtonStatus(False,False,False,False,True,False)
                            self.userInfo.opponent = None
                    elif data['cid'] == 1004:
                        if data['opponent'] != '':
                            self.userInfo.opponent = data['opponent']
                            self.player2.setText(self.userInfo.opponent)
                            if self.userInfo.opponent in self.scoreList:
                                self.score_player2.setText("分数：".decode('utf-8')+str(self.scoreList[self.userInfo.opponent]))
                            self.setButtonStatus(True,False,False,False,True,True)
                    elif data['cid'] == 1005:
                        if data['message'] == u'begin':
                            # QtGui.QMessageBox.information(self, "提示".decode('utf-8'),"可以开始比赛了".decode('utf-8') )
                            #开始比赛
                            self.beginChess(data)
                        else:
                            self.inforShow.setText("你们还有一\n方未准备".decode('utf-8'))
                             # QtGui.QMessageBox.information(self, "提示".decode('utf-8'),"你们有一方还未准备".decode('utf-8') )
                    elif data['cid'] == 1006:
                        n = data['n']
                        m = data['m']
                        self.userInfo.updateChessBoard(n, m)
                    elif data['cid'] == 1007:
                        self.inforShow.setText("很遗憾，\n你输了".decode('utf-8'))
                        self.setButtonStatus(False, False, False, True, True, True)
                        self.wavplay.playLose()
                        # if self.userInfo.chessType == 2:
                        #     QtGui.QMessageBox.information(self, "结束".decode('utf-8'), "白棋获胜，你输了".decode('utf-8'))
                        # else:
                        #     QtGui.QMessageBox.information(self, "结束".decode('utf-8'), "黑棋获胜，你输了".decode('utf-8'))
                        self.userInfo.IsNext = False
                    elif data['cid'] == 1008:
                        self.scoreList = data['scoreList']
                    elif data['cid'] == 1009:
                        self.inforShow.setText("对方认输，\n你赢了".decode('utf-8'))
                        self.setButtonStatus(False, False, False, True, True, True)
                        self.userInfo.IsNext = False
                        self.wavplay.playWin()
                        # if self.userInfo.chessType == 2:
                        #     QtGui.QMessageBox.information(self, "结束".decode('utf-8'), "白棋认输，你赢了".decode('utf-8'))
                        # else:
                        #     QtGui.QMessageBox.information(self, "结束".decode('utf-8'), "黑棋认输，你赢了".decode('utf-8'))
                    else:
                        pass
                        # print self.tableList
                elif data['sid'] == 101:
                    self.inforShow.setText("欢迎你进入\n大厅".decode('utf-8'))
                    # QtGui.QMessageBox.information(self, "提示".decode('utf-8'),"欢迎你进入大厅".decode('utf-8') )
                    pass
                elif data['sid'] == 102:
                    if data['cid'] == 1001:
                        # print 'heh'
                        groupMsg = data['user']+': '+str(time.strftime('%H:%M:%S',time.localtime(time.time())))+'\n'+data['message']+'\n'
                        self.groupTalk.insertPlainText(groupMsg)
                        self.groupTalk.setTextCursor(self.groupTalk.textCursor())
                    elif data['cid'] == 1002:
                        singleMsg = data['user']+': '+str(time.strftime('%H:%M:%S',time.localtime(time.time())))+'\n'+data['message']+'\n'
                        self.singleTalk.insertPlainText(singleMsg)
                        self.singleTalk.setTextCursor(self.singleTalk.textCursor())
                elif data['sid'] == 104:
                    if data['cid'] == 1001:
                        reply = QtGui.QMessageBox.question(self, "悔棋".decode('utf-8'), "你的对手请求悔棋，是否同意？".decode('utf-8'),QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
                        if reply == QtGui.QMessageBox.Yes:
                            data = {'sid':104,'cid':1002,'reply':'yes','userlist':[self.userInfo.opponent]}
                            self.ns.send(json.dumps(data))
                            self.ns.process()
                            self.userInfo.backmove()
                        else:
                            data = {'sid':104,'cid':1002,'reply':'no','userlist':[self.userInfo.opponent]}
                            self.ns.send(json.dumps(data))
                            self.ns.process()
                    elif data['cid'] == 1002:
                        if data['reply'] == 'yes':
                            QtGui.QMessageBox.information(self, "提示".decode('utf-8'),"对手同意了你的悔棋请求".decode('utf-8'))
                            self.userInfo.backmove()
                        else:
                            QtGui.QMessageBox.information(self, "提示".decode('utf-8'),"对手拒绝了你的悔棋请求".decode('utf-8'))
                        self.userInfo.IsNext = True
                        self.inforShow.setText("我方下".decode('utf-8'))
                    elif data['cid'] == 1003:
                        reply = QtGui.QMessageBox.question(self, "再来一局".decode('utf-8'), "你的对手请求再来一局，是否同意？".decode('utf-8'),QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
                        if reply == QtGui.QMessageBox.Yes:
                            data = {'sid':104,'cid':1004,'reply':'yes','userlist':[self.userInfo.opponent],'white':self.userInfo.opponent}
                            self.ns.send(json.dumps(data))
                            self.ns.process()
                            #清除棋盘
                            self.userInfo.clearChessBoard()
                            #正式开始比赛
                            self.beginChess(data)
                        else:
                            data = {'sid':104,'cid':1004,'reply':'no','userlist':[self.userInfo.opponent]}
                            self.ns.send(json.dumps(data))
                            self.ns.process()
                    elif data['cid'] == 1004:
                        if data['reply'] == 'yes':
                            QtGui.QMessageBox.information(self, "提示".decode('utf-8'),"对手同意再来一局".decode('utf-8'))
                            #清除棋盘
                            self.userInfo.clearChessBoard()
                            #正式开始比赛
                            self.beginChess(data)
                        else:
                            QtGui.QMessageBox.information(self, "提示".decode('utf-8'),"对手拒绝再来一局".decode('utf-8'))

                elif data['sid'] == 105:
                    pass
                elif data == 'quit':
                    self.ns.close()
                    shutdown = True
                    # break
                else:
                    pass
            else:
                pass
        elif self.ns.status() == netstream.NET_STATE_STOP:
            pass

    #鼠标左键按下监听
    def releaseAction(self,event):
        if event.button() == Qt.LeftButton:
            self.paint(event.pos().x(), event.pos().y())

    #描绘棋子
    def paint(self, x, y):
        n, m = self.userInfo.pressEvent(x,y)
        if n != -1:
            data = {'sid':100,'cid':1006,'m':m,'n':n,'userlist':[self.userInfo.opponent]}
            self.ns.send(json.dumps(data))

        if self.userInfo.IsWin(n, m):
            self.userInfo.IsNext = False
            self.setButtonStatus(False, False, False, True, True, True)
            self.inforShow.setText("恭喜你赢了".decode('utf-8'))
            self.wavplay.playWin()
            data = {'sid':100,'cid':1007,'winner':self.userInfo.name,'loser':self.userInfo.opponent,'chessType':self.userInfo.chessType}
            self.ns.send(json.dumps(data))
            self.ns.process()
            # if self.userInfo.chessType == 1:
            #     QtGui.QMessageBox.information(self, "结束".decode('utf-8'), "白棋获胜，你赢了".decode('utf-8'))
            # else:
            #     QtGui.QMessageBox.information(self, "结束".decode('utf-8'), "黑棋获胜，你赢了".decode('utf-8'))

    #排行榜
    def rank(self):
        self.scoreRank.clear()
        data = sorted(self.scoreList.iteritems(), key=lambda d:d[1], reverse = True)
        self.scoreRank.addItem('玩家'.decode('utf-8').ljust(18, ' ') + '分数'.decode('utf-8'))
        for i in range(len(data)):
            if i >= 3:
                break
            self.scoreRank.addItem(str(data[i][0]).ljust(20,' ')+str(data[i][1]))

    # 客户端配置
    def clientConfig(self):
        #更新房间列表人数
        self.updateRoom()
        self.rank()
        #配对用户名和hid
        if self.FirstTime:
            data = {'sid':103,'cid':1001,'user':self.userInfo.name}
            self.ns.send(json.dumps(data))
            self.ns.process()
            self.FirstTime = False
        #如果用户还没对手,一直检索对手


        if self.userInfo.opponent == None  and self.loopCount == 0:
            self.loopCount = 40
            # print self.userInfo.opponent,self.userInfo.tableid
            if self.userInfo.tableid != -1:
                data = {'sid':100, 'cid':1004,'roomid':self.userInfo.roomid - 1,'tableid':self.userInfo.tableid - 1,'user':self.userInfo.name}
                self.ns.send(json.dumps(data))
                self.ns.process()
        else:
            if self.loopCount == 0:
                self.loopCount = 40
            self.loopCount -= 1
        #更新分数
        if self.userInfo.IsInto:
            if self.userInfo.name in self.scoreList:
                self.score_player1.setText("分数：".decode('utf-8')+str(self.scoreList[self.userInfo.name]))
            if self.userInfo.opponent != None and self.userInfo.opponent in self.scoreList:
                self.score_player2.setText("分数：".decode('utf-8')+str(self.scoreList[self.userInfo.opponent]))
        #每隔5秒发送心跳包
        if self.tickCount == 0:
            self.tickCount = 100
            data = {'sid':105,'cid':1001}
            self.ns.send(json.dumps(data))
            self.ns.process()
        else:
            self.tickCount -= 1

    #进入房间事件
    def intoTable(self, item):
        #如果已经进入房间,就不让点击房间桌子item了
        if self.userInfo.IsInto:
            return
        parent1 = item.parent()
        if parent1:
            num1 = parent1.indexOfChild(item)
        parent2 = parent1.parent()
        num2 = -1
        if parent2:
            num2 = parent2.indexOfChild(parent1)
        if num2 != -1:
            index = num2 * 5 + num1
            num =self.tableList[index]
            if num == 2:
                # QtGui.QMessageBox.information(self, "错误".decode('utf-8'),"桌子认输已满,请选择别的桌子".decode('utf-8'))
                pass
            elif num == 1:
                # QtGui.QMessageBox.information(self, "提示".decode('utf-8'),"你已进入房间，你的对手已经坐下".decode('utf-8'))
                #用户进入房间
                data = {'sid':100, 'cid':1002,'roomid':num2,'tableid':num1,'user':self.username}
                # self.tableList[index] += 1
                self.ns.send(json.dumps(data))
                # self.ns.process()

                self.userInfo.IsInto = True
                self.setButtonStatus(True,False,False,False,True,True)
                self.userInfo.roomid = num2 + 1
                self.userInfo.tableid = num1 + 1
                self.roomName.setText('房间'.decode('utf-8')+str(self.userInfo.roomid)+'\n桌子'.decode('utf-8')+str(self.userInfo.tableid))
                self.inforShow.setText("欢迎你坐下\n".decode('utf-8'))
                self.player1.setText(self.userInfo.name)
                if self.userInfo.name in self.scoreList:
                    self.score_player1.setText("分数：".decode('utf-8')+str(self.scoreList[self.userInfo.name]))
                #用户获取的对手资料
                data = {'sid':100, 'cid':1004,'roomid':num2,'tableid':num1,'user':self.username}
                self.ns.send(json.dumps(data))
                self.ns.process()
            else:
                # QtGui.QMessageBox.information(self, "提示".decode('utf-8'),"你已进入房间，等待你的对手中".decode('utf-8') )
                data = {'sid':100, 'cid':1002,'roomid':num2,'tableid':num1,'user':self.username}
                # self.tableList[index] += 1
                self.ns.send(json.dumps(data))
                self.ns.process()

                self.userInfo.IsInto = True
                self.userInfo.opponent = None
                self.setButtonStatus(False,False,False,False,True,False)
                self.userInfo.roomid = num2 + 1
                self.userInfo.tableid = num1 + 1
                self.roomName.setText('房间'.decode('utf-8')+str(self.userInfo.roomid)+'\n桌子'.decode('utf-8')+str(self.userInfo.tableid))
                self.inforShow.setText("欢迎你坐下\n".decode('utf-8'))
                self.player1.setText(self.userInfo.name)
                if self.userInfo.name in self.scoreList:
                    self.score_player1.setText("分数：".decode('utf-8')+str(self.scoreList[self.userInfo.name]))

    #控制背景音乐播放
    def controlBgMusic(self):
        self.bgPlay.pause()
        if self.bgIsPlay:
            self.bgMusic.setText('播放背景音乐'.decode('utf-8'))
            self.bgIsPlay = False
        else:
            self.bgMusic.setText('关闭背景音乐'.decode('utf-8'))
            self.bgIsPlay = True

    #更新房间桌子列表
    def updateRoom(self):
        item0 = self.room.invisibleRootItem()
        item1 = item0.child(0)
        childCount =  item1.childCount()
        for i in range(childCount):
            itemChild1 = item1.child(i)
            num = 0
            for j in range(0, 5):
                num += self.tableList[i * 5 + j]
                if itemChild1:
                    itemChild2 = itemChild1.child(j)
                    itemChild2.setText(0,'桌子'.decode('utf-8')+str(j+1)+'('+str(self.tableList[i*5 +j])+'/2)')
            if itemChild1:
                itemChild1.setText(0,'房间'.decode('utf-8')+ str(i+1) +'('+ str(num) +'/10)')

    #发送群聊消息
    def sendGroupMessage(self):
        text = self.groupEdit.text()
        text = unicode(text).strip()
        self.groupEdit.clear()
        if len(text) > 0:
            data = {'sid':102,'cid':1001,'message':text,'user':self.userInfo.name}
            self.ns.send(json.dumps(data))
            self.ns.process()

    #房间聊天
    def sendSingleMessage(self):
        if self.userInfo.opponent != None:
            text = self.singleEdit.text()
            text = unicode(text).strip()
            self.singleEdit.clear()
            if len(text) > 0:
                data = {'sid':102,'cid':1002,'message':text,'userlist':[self.userInfo.name,self.userInfo.opponent],'user':self.userInfo.name}
                self.ns.send(json.dumps(data))
                self.ns.process()

    # 开始准备
    def startChess(self):
        self.setButtonStatus(False, True, True, False, False, True)
        self.userInfo.IsReady = True
        message = {'sid':100,'cid':1005,'message':'start','user':self.userInfo.name,'opponent':self.userInfo.opponent}
        self.ns.send(json.dumps(message))

    # 再来一局
    def againChess(self):
        message = {'sid':104,'cid':1003,'message':'again','userlist':[self.userInfo.opponent],'user':self.userInfo.name}
        self.ns.send(json.dumps(message))

    # 认输
    def loseChess(self):
        self.setButtonStatus(False, False, False, True, True, True)
        self.userInfo.IsNext = False
        data = {'sid':100,'cid':1009,'winner':self.userInfo.opponent,'loser':self.userInfo.name,'chessType':self.userInfo.chessType}
        self.ns.send(json.dumps(data))
        self.ns.process()
        self.inforShow.setText("你认输了".decode('utf-8'))
        self.wavplay.playLose()

    # 悔棋
    def undoChess(self):
        if not self.userInfo.IsNext:
            return
        if len(self.userInfo.path) < 2:
            self.inforShow.setText("你还没下，\n不得悔棋".decode('utf-8'))
            return
        else:
            self.userInfo.IsNext = False
            self.inforShow.setText("悔棋等待中".decode('utf-8'))
            data = {'sid':104, 'cid':1001,'message':'undo','userlist':[self.userInfo.opponent],'user':self.userInfo.name}
            self.ns.send(json.dumps(data))
            self.ns.process()

    # 正式开始比赛
    def beginChess(self, data):
        self.inforShow.setText("可以开始\n比赛了".decode('utf-8'))
        self.wavplay.playStart()
        self.setButtonStatus(False,True,True,False,False,True)
        self.userInfo.IsBegin = True
        self.chessBoard.mouseReleaseEvent = self.releaseAction
        #如果白棋是自己的名字，那么自己的五子棋类型为白棋
        if data['white'] == self.userInfo.name:
            # QtGui.QMessageBox.information(self, "提示".decode('utf-8'),"你是白棋，你先下".decode('utf-8') )
            self.inforShow.setText("你是白棋，\n你先下".decode('utf-8'))
            self.userInfo.chessType = WHITE_FLAG  #白棋
            self.userInfo.IsNext = True
        else:
            # QtGui.QMessageBox.information(self, "提示".decode('utf-8'),"你是黑棋，你后手".decode('utf-8') )
            self.inforShow.setText("你是黑棋，\n你后手".decode('utf-8'))
            self.userInfo.chessType = BLACK_FLAG  #黑棋
            self.userInfo.IsNext = False

    # 离开房间
    def leaveChess(self):
        self.userInfo.clearChessBoard()
        self.player1.setText("玩家1：".decode('utf-8'))
        self.score_player1.setText("分数：".decode('utf-8'))
        self.player2.setText("玩家2：".decode('utf-8'))
        self.score_player2.setText("分数：".decode('utf-8'))
        self.userInfo.IsInto = False
        data = {'sid':100,'cid':1003,'roomid':self.userInfo.roomid - 1,'tableid':self.userInfo.tableid - 1,'user':self.userInfo.name,'opponent':self.userInfo.opponent}
        self.userInfo.opponent = None
        self.userInfo.tableid = -1
        self.userInfo.roomid = -1
        # self.tableList[index] += 1
        self.ns.send(json.dumps(data))
        self.ns.process()
        self.setButtonStatus(False,False,False,False,False,False)
        self.roomName.setText("暂未进\n入房间".decode('utf-8'))
        self.inforShow.setText("你已经离开\n了房间".decode('utf-8'))