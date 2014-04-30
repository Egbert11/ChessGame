# -*- coding: utf-8 -*-
__author__ = 'gzs2218'

import sys
sys.path.append("..")
from server import netstream
from client.ui_Login import Ui_Dialog
from client.gobangClient import *
from PyQt4 import QtCore, QtGui
from PyQt4.Qt import *

class GobangLogin(QtGui.QWidget, Ui_Dialog):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.connect(self.btnLogin, SIGNAL('clicked()'), self.login)
        self.connect(self.btnExit, SIGNAL('clicked()'), self.exit)
        self.connect(self.lineEditUsername, SIGNAL('returnPressed()'), self.login)

    # 登录
    def login(self):
        self.ip = str(self.lineEditServer.text()).strip()
        self.port = int(self.lineEditPort.text())
        self.username = str(self.lineEditUsername.text()).strip()
        if len(self.username) == 0:
            QtGui.QMessageBox.information(self, u'错误', u'输入的用户名不能为空')
            return
        self.ns = netstream.netstream(8)
        self.ns.connect(self.ip, self.port)
        self.timer = QTimer()
        self.timer.timeout.connect(self.serverConnect)
        self.timer.start(100)


    #连接服务器
    def serverConnect(self):
        self.ns.process()
        if self.ns.status() == netstream.NET_STATE_ESTABLISHED:
            # while True:
            data = self.ns.recv()
            if len(data) > 0 :
                data = json.loads(data)
                if data['sid'] == 101:
                    self.call_login_success()

    # 登录成功回调函数
    def call_login_success(self):
        self.close()
        self.timer.stop()
        self.client = GobangClient(self.ip, self.port, self.username, self.ns)
        self.client.startup()
        self.client.show()

    #登录失败回调函数
    def call_login_failed(self, addr):
        QtGui.QMessageBox.information(self, u"错误", "Unable to connect to [%s:%s]" % addr)

    def exit(self):
        self.close()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName(u"五子棋")
    loginForm = GobangLogin()
    loginForm.show()
    sys.exit(app.exec_())