# -*- coding:utf-8 -*-
__author__ = 'gzs2218'

class chatMessage(object):
    SERVICE_ID = 102

    def __init__(self):
        commands = {
            1001:self.receiveGroupMessage,
            1002:self.receiveSingleMessage
        }
        self.registers(commands)

    def handle(self, msg):
        cid = msg['cid']
        if not cid in self.__command_map:
            raise Exception('bad command %s'%cid)
        f = self.__command_map[cid]
        return f(msg)

    def register(self, cid, function):
        self.__command_map[cid] =  function

    def registers(self, CommandDict):
        self.__command_map = {}
        for cid in CommandDict:
            self.register(cid, CommandDict[cid])
        return 0

    # 群聊消息
    def receiveGroupMessage(self, msg):
        text = msg['message']
        user = msg['user']
        data = {'sid':102,'cid':1001,'message':text,'sendType':2,'user':user}
        return data

    # 房间聊天消息
    def receiveSingleMessage(self, msg):
        msg['sendType'] = 3
        return msg
