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
        self.__id = addresses[0]
        print('client: ', self.__id, ' discovered network')

        # connect to broadcast
        self.__broadcast = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        broadcast_ip, broadcast_port = addresses[1].split(DELIM_1)
        self.__broadcast.connect((broadcast_ip, int(broadcast_port)))

        # connect to servers
        self.__servers = {}
        for address in addresses[2:]:
            cur_id, cur_ip, cur_port = address.split(DELIM_1)
            self.__servers[cur_id] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__servers[cur_id].connect((cur_ip, int(cur_port)))
            print('client connected successfully to server: ', cur_id,
                  ' in ip: ', cur_ip, ' and port: ', cur_port)
        print('client connected successfully to all servers')
        for sid in self.__servers:  # todo remove all next lines
            self.__servers[sid].sendall(str(END_SESSION).encode())
            self.__servers[sid].close()
        self.__broadcast.sendall(str(END_SESSION).encode())
        self.__broadcast.close()

    def store(self, name, key, value):
        pass

    def retrieve(self, name, key, value):
        pass

    def close(self):
        self.__broadcast.close()
        for sid in self.__servers:
            self.__servers[sid].close()

if __name__ == '__main__':
    client = Client()
    client.close()
