# -*- coding:utf-8 -*-
__author__ = 'gzs2218'

class tableList_service(object):
    SERVICE_ID = 100

    def __init__(self):
        #显示每张桌子现有人数的列表
        self.tableList = [ 0 for x in range(0,25)]
        #显示每个用户的当前状态
        self.state={}
        #显示每个用户的分数
        self.score = {}
        #显示每张桌子的用户列表
        self.userList = []
        for i in range(25):
            self.userList.append([])
        commands = {
            1001:self.getTableList,
            1002:self.userIn,
            1003:self.userOut,
            1004:self.getOpponent,
            1005:self.setState,
            1006:self.updateChess,
            1007:self.getWinner,
            1008:self.getScoreList,
            1009:self.giveUp
        }
        self.registers(commands)
        print self.__command_map

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

    # 获取每张卓子的人数
    def getTableList(self,msg):
        data = {'sid':100,'cid':1001,'tableList':self.tableList,'sendType':1}
        return data

    # 玩家进入房间
    def userIn(self,msg):
        tableNum = msg['roomid'] * 5 + msg['tableid']
        if self.tableList[tableNum] < 2:
            self.tableList[tableNum] += 1
        self.userList[tableNum].append(msg['user'])
        self.state[msg['user']] = 'notReady'
        if msg['user'] in self.score.keys() and self.score[msg['user']] != 0:
            pass
        else:
            self.score[msg['user']] = 0
        print 'userlist',self.userList
        data = {'sid':100,'cid':1001,'tableList':self.tableList,'sendType':1}
        return data

    #玩家离开房间
    def userOut(self,msg):
        tableNum = msg['roomid'] * 5 + msg['tableid']
        if self.tableList[tableNum] > 0:
            self.tableList[tableNum] -= 1
        self.userList[tableNum].remove(msg['user'])
        if msg['opponent'] != None:
            msg['userlist'] = [msg['opponent']]
        else:
            msg['userlist'] = []
        msg['sendType'] = 3
        print 'userlist',self.userList
        self.state[msg['user']] = 'leave'
        return msg

    #获取对手信息
    def getOpponent(self,msg):
        tableNum = msg['roomid'] * 5 + msg['tableid']
        opponent = ''
        for i in self.userList[tableNum]:
            if i != msg['user']:
                opponent = i
        data = {'sid':100,'cid':1004,'opponent':opponent,'sendType':1}
        return data

    #设置状态
    def setState(self, msg):
        state = msg['message']
        name = msg['user']
        self.state[name] = state
        if self.state[msg['opponent']] == 'start':
            return {'sid':100,'cid':1005,'message':'begin','userlist':[msg['user'],msg['opponent']],'sendType':3,'white':msg['user']}
        else:
            return {'sid':100,'cid':1005,'message':'nobegin','userlist':[msg['user'],msg['opponent']],'sendType':3}

    #提示对手可以开始了
    def updateChess(self, msg):
        msg['sendType'] = 3
        return msg

    #获知胜利结果
    def getWinner(self, msg):
        winner = msg['winner']
        self.score[winner] += 10
        loser = msg['loser']
        self.score[loser] += 2
        msg['userlist'] = [msg['loser']]
        msg['sendType'] = 3
        return msg

    #获取分数列表
    def getScoreList(self,msg):
        data = {'sid':100,'cid':1008,'scoreList':self.score}
        return data

    #某方认输
    def giveUp(self, msg):
        winner = msg['winner']
        self.score[winner] += 10
        loser = msg['loser']
        self.score[loser] += 2
        msg['userlist'] = [msg['winner']]
        msg['sendType'] = 3
        return msg






