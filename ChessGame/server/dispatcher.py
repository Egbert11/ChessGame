__author__ = 'gzs2218'

class dispatcher(object):
    def __init__(self):
        self.__service_map = {}

    def dispatch (self, msg):
        sid = msg['sid']
        if not sid in self.__service_map:
            raise Exception('bad service %d'%sid)
        svc = self.__service_map[sid]
        return svc.handle(msg)

    def register (self, sid, svc):
        self.__service_map[sid] = svc