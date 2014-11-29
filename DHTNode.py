__author__ = 'dwb'

import socket
import logging
from threading import Thread
from bencode import bencode, bdecode
from Config import *
from utility import *
from KTable import *
from KNode import *

stdger = logging.getLogger("std_log")
fileger = logging.getLogger("file_log")



class DHT(Thread):
    def __init__(self, master, bind_ip, bind_port, max_node_qsize):
        Thread.__init__(self)

        self.setDaemon(True)
        self.isServerWorking = True
        self.isClientWorking = True
        self.master = master
        self.bind_ip = bind_ip
        self.bind_port = bind_port
        self.max_node_qsize = max_node_qsize
        self.table = KTable()
        self.ufd = socket.socket(socket.AF_INET,socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.ufd.bind((self.bind_ip, self.bind_port))
        self.server_thread=Thread(target=self.server)
        self.server_thread.daemon=True

        self.iteration=10000
        self.needFindIt=True
        self.maglink="mnopqrstuvwxyz123456"

        timer(RE_JOIN_DHT_INTERVAL, self.join_DHT)

    def start(self):
        self.server_thread.start()
        Thread.start(self)
        return self

    def server(self):

        while self.isServerWorking:
            try:
                (data, address) = self.ufd.recvfrom(65536)
                stdger.debug('receive packega')
                msg = bdecode(data)
                self.on_message(msg, address)
            except Exception:
                pass

    def client(self):

        #read at most 10000 package
        while True and self.needFindIt and self.iteration:

            self.iteration -= 1
            try:
                node = self.table.nodes.get(block=True)
                self.send_get_peer((node.ip, node.port), self.maglink)
            except Exception:
                pass

    def initialBeforGet(self,maglink):


        stdger.debug("the queue size: %d"%self.table.nodes.qsize())
        #restore the last 100 node
        while self.table.nodes.qsize() > 100:
            try:
                data=self.table.nodes.get()
            except Exception:
                pass

        stdger.debug("the queue size: %d"%self.table.nodes.qsize())
        self.iteration=100000
        self.needFindIt=True
        self.maglink=maglink.decode("hex")


    def on_message(self, msg, address):
        try:
            if msg["y"] == "r":
                stdger.debug("get useful package")
                if msg["r"].has_key("nodes"):
                    self.process_get_peer_node_response(msg, address)
                elif msg["r"].has_key("values"):
                    self.process_get_peer_value_response(msg,address)

            elif msg["y"] == "q":
                if msg["q"] == "find_node":
                    self.process_find_node_request(msg, address)

                elif msg["q"] == "get_peers":
                    self.process_get_peers_request(msg, address)
        except KeyError, e:
            pass

    #send msg to a specified address
    def send_krpc(self, msg, address):
        try:
            self.ufd.sendto(bencode(msg), address)
        except:
            pass

    #send udp message
    def send_find_node(self, address, nid=None):
        nid = get_neighbor(nid) if nid else self.table.nid
        #token id
        tid = entropy(TID_LENGTH)
        #random_id() quite good idea
        msg = dict(
            t = tid,
            y = "q",
            q = "find_node",
            a = dict(id = nid, target = random_id())
        )
        stdger.debug("send udp packet")
        self.send_krpc(msg, address)

    #send get_peer udp
    def send_get_peer(self, address, magLink):

        nid = random_id()
        #token id
        tid = entropy(TID_LENGTH)
        #random_id() quite good idea
        msg = dict(
            t = tid,
            y = "q",
            q = "get_peers",
            a = dict(id = nid, info_hash = magLink)
        )
        stdger.debug("send get peer package")
        self.send_krpc(msg, address)

    #only need to send a random_id to the bootstrap node.
    def join_DHT(self):

        while self.table.nodes.qsize()<8:

            for address in BOOTSTRAP_NODES:
                self.send_find_node(address)

    def play_dead(self, tid, address):
        msg = dict(
            t = tid,
            y = "e",
            e = [202, "Server Error"]
        )
        self.send_krpc(msg, address)

    #get the node
    def process_get_peer_node_response(self, msg, address):
        stdger.debug("recieve get peer node")
        stdger.debug("the msg %s"%msg)
        nodes = decode_nodes(msg["r"]["nodes"])
        for node in nodes:
            (nid, ip, port) = node
            if len(nid) != 20: continue
            if ip == self.bind_ip: continue

            stdger.debug("add new peer node %s" % nid.encode("hex"))
            self.table.put(KNode(nid, ip, port))

    #get the peer info
    def process_get_peer_value_response(self, msg, address):

        stdger.debug("recieve get peer value")
        maglinkerServer = msg["r"]["values"]

        stdger.debug("the msg %s"%msg)

        n = decode_values(maglinkerServer)

        for i in n:
            self.master.logPeer(self.maglink.encode('hex'),i[0],i[1])






    def process_get_peers_request(self, msg, address):
        try:
            tid = msg["t"]
            infohash = msg["a"]["info_hash"]
            self.master.log(infohash, address)
            self.play_dead(tid, address)
        except KeyError, e:
            pass

    def process_find_node_request(self, msg, address):
        try:
            tid = msg["t"]
            target = msg["a"]["target"]
            self.master.log(target, address)
            self.play_dead(tid, address)
        except KeyError, e:
            pass

    def stop(self):
        self.isClientWorking = False
        self.isServerWorking = False