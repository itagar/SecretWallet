import socket
from Helper import *


class Client:

    def __init__(self):
        # discover network
        discover = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        discover.connect((DISCOVER_IP, DISCOVER_PORT))
        data = discover.recv(BUFFER_SIZE).decode()
        addresses = data.split(DELIM_2)
        self.__id = addresses[0]  # todo magic
        print('client: ', self.__id, ' discovered network')
        discover.close()

        # socket for broadcast
        self.__broadcast = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__broadcast_address = addresses[1].split(DELIM_1)
        self.__broadcast_address[1] = int(self.__broadcast_address[1])

        # connect to servers
        self.__servers = {}
        for address in addresses[2:]:
            cur_id, cur_ip, cur_port = address.split(DELIM_1)
            self.__servers[cur_id] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__servers[cur_id].connect((cur_ip, int(cur_port)))
            self.__servers[cur_id].sendall(self.__id.encode())

            print('client connected successfully to server: ', cur_id,
                  ' in ip: ', cur_ip, ' and port: ', cur_port)
        print('client connected successfully to all servers')

    def store(self, name, key, value):
        self.__start_session()
        print('start store: name=', name, ', key=', key, ', value=', value)
        self.__broadcast.sendall(name)  # todo name already taken
        if deal_vss(self.__servers, self.__broadcast, key) == ERROR:
            print('error with storing key')
            return ERROR
        if deal_vss(self.__servers, self.__broadcast, value) == ERROR:
            print('error with storing value')
            return ERROR
        print('store key,value sucessfully')
        return OK

    def retrieve(self, name, key):
        self.__start_session()
        print('start retrieve: name=', name,', key=', key)
        self.__end_session()
        pass

    def __start_session(self):
        self.__broadcast.connect(self.__broadcast_address)
        self.__broadcast.sendall(self.__id.encode())

    def __end_session(self):
        self.__broadcast.close()

    def close(self):
        self.__broadcast.sendall(str(END_SESSION).encode())
        self.__broadcast.close()
        for sid in self.__servers:
            self.__servers[sid].close()


if __name__ == '__main__':
    client = Client()
    while True:
        request = input('what should i do next: ')
        if request == 'store':
            secret_name, secret_key, secret_value = input('please insert: name key value').split()
            client.store(secret_name, secret_key, secret_value)
        elif request == 'ret':
            secret_name, secret_key = input('please insert: name key').split()
            client.retrieve(secret_name, secret_key)
        else:
            print('see you next time.')
            break
    client.close()
