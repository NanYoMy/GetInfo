__author__ = 'dwb'

class KNode(object):
    def __init__(self, nid, ip=None, port=None):
        self.nid = nid
        self.ip = ip
        self.port = port

    def __eq__(self, node):
        return node.nid == self.nid

    def __hash__(self):
        return hash(self.nid)