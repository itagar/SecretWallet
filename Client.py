import socket
from Server import *


class Client:

    def __init__(self):
        # discover network
        discover = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        discover.connect((DISCOVER_IP, DISCOVER_PORT))
        data = discover.recv(BUFFER_SIZE).decode()
        discover.close()
        addresses = data.split(DELIM_2)

        # connect to broadcast
        self.__broadcast = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        broadcast_ip, broadcast_port = addresses[0].split
        self.__broadcast.connect((broadcast_ip, int(broadcast_port)))

        # connect to servers
        self.__servers = {}
        for i in range(1, NUM_OF_SERVERS+1):
            cur_id, cur_ip, cur_port = addresses[i].split
            self.__servers[cur_id] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__servers[cur_id].connect((cur_ip, int(cur_port)))
            print('client connected successfully to server: ', cur_id,
                  ' in ip: ', cur_ip, ' and port: ', cur_port)
        print('client connected successfully to all servers')

    def store(self, name, key, value):
        pass

    def retrieve(self, name, key, value):
        pass

    def close(self):
        self.__broadcast.close()
        for server in self.__servers:
            server.close()

if __name__ == '__main__':
    client = Client()
    client.close()