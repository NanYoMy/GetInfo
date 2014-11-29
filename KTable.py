__author__ = 'dwb'

from Queue import Queue

from utility import *

class KTable():
    def __init__(self):
        self.nid = random_id()
        self.nodes = Queue()

    def put(self, node):
        self.nodes.put(node)
