# -*- coding: utf-8 -*-

__author__ = 'gzs2218'

import json
from server.netstream import *
from server.dispatcher import *
from server.tableList_service import *
from server.chatMessage import *
from server.chessBoard import *
from server.ticks import *


class GobangServer(object):
    def __init__(self):
        self.host = nethost(8)
        self.host.startup(2000)
        print 'service startup at port', self.host.port
        self.host.settimer(2000)
        self.userList = {}

if __name__ == "__main__":
    #任务处理分发器
    dis = dispatcher()
    #注册各类服务
    dis.register(tableList_service.SERVICE_ID, tableList_service())
    dis.register(chatMessage.SERVICE_ID, chatMessage())
    dis.register(chessBoard.SERVICE_ID, chessBoard())
    dis.register(ticks.SERVICE_ID, ticks())
    server = GobangServer()
    while 1:
        # time.sleep(0.1)
        server.host.process()
        event, wparam, lparam, data = server.host.read()
        if event < 0: continue
        # print 'event=%d wparam=%xh lparam=%xh data="%s"'%(event, wparam, lparam, data)
        # 接收到玩家数据
        if event == NET_DATA:
            data = json.loads(data)
            if data['sid'] == 103:
                server.userList[data['user']] = wparam
            else:
                result =  dis.dispatch(data)
                #返回数据到发送者
                if result['sendType'] == 1:
                    server.host.send(wparam, json.dumps(result))
                #广播
                elif result['sendType'] == 2:
                    print result
                    for user in server.userList.keys():
                        # print server.userList
                        server.host.send(server.userList[user], json.dumps(result))
                #发给部分人
                elif result['sendType'] == 3:
                    if result['userlist']:
                        for user in result['userlist']:
                            server.host.send(server.userList[user], json.dumps(result))
                server.host.process()
            if data == 'exit':
                print 'client request to exit'
                server.host.close(wparam)
        # 处理玩家进入
        elif event == NET_NEW:
            print wparam, 'is in'
            # server.userList.append(wparam)
            data = {'sid':101,'type':'HELLO CLIENT %X'%(wparam)}
            server.host.send(wparam, json.dumps(data))
            server.host.settag(wparam, wparam)
            server.host.nodelay(wparam, 1)
        #处理时钟
        elif event == NET_TIMER:
            #发送桌子列表
            data = {'sid':100,'cid':1001}
            result = dis.dispatch(data)
            for user in server.userList.keys():
                server.host.send(server.userList[user], json.dumps(result))
            #发送分数
            data = {'sid':100,'cid':1008}
            result = dis.dispatch(data)
            for user in server.userList.keys():
                server.host.send(server.userList[user], json.dumps(result))
        #处理玩家离开
        elif event == NET_LEAVE:
            print wparam, 'is out'
            server.host.close(wparam)