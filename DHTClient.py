#encoding: utf-8
#！/usr/bin
#!/usr/bin/env python

import logging
from utility import *
from DHTNode import *


stdger = logging.getLogger("std_log")
fileger = logging.getLogger("file_log")
peerger = logging.getLogger("peer_log")

#using example
class Master(object):

    def log(self, infohash, address=None):
        stdger.debug("%s from %s:%s" % (infohash.encode("hex"), address[0], address[1]))
        fileger.debug('%s from %s:%s' % (infohash.encode('hex').upper(),address[0],address[1]))

    def logPeer(self,mag,ip,port):

        peerger.debug("%s is located in %s:%d",mag,ip,port)

if __name__ == "__main__":
    #max_node_qsize bigger, bandwith bigger, spped higher

    initialLog()
    stdger.debug("start get peer %d" % 9501)
    dht=DHT(Master(), "0.0.0.0", 9512, max_node_qsize=1000)
    dht.start()
    dht.join_DHT()



    while True:
        stdger.debug("new loop")
        dht.initialBeforGet("9f9bfd28e052442b6836b5ff0c3aae826ea0eecf")
        dht.client()
