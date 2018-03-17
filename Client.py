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
        self.__broadcast = None
        self.__broadcast_address = (addresses[1].split(DELIM_1))
        self.__broadcast_address = (self.__broadcast_address[0], int(self.__broadcast_address[1]))
        print('addresses: ', addresses)
        print('broadcast: ', self.__broadcast_address)
        print(type(self.__broadcast_address))

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
        self.__start_session(STORE)
        print('start store: name=', name, ', key=', key, ', value=', value)
        # self.__broadcast.sendall(name)  # todo name already taken
        # if deal_vss(self.__servers, self.__broadcast, key) == ERROR:
        #     print('error with storing key')
        #     self.__end_session()
        #     return ERROR
        # if deal_vss(self.__servers, self.__broadcast, value) == ERROR:
        #     print('error with storing value')
        #     self.__end_session()
        #     return ERROR
        print('store key,value successfully')
        self.__end_session()
        return OK

    def retrieve(self, name, key):
        self.__start_session(RETRIEVE)
        print('start retrieve: name=', name,', key=', key)
        self.__end_session()
        pass

    def __receive_broadcast(self, size=BUFFER_SIZE):
        data = self.__broadcast.recv(size).decode()
        sender, data = data.split(SENDER_DELIM)
        return int(sender), data

    def __start_session(self, request_type):
        self.__broadcast = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__broadcast.connect(self.__broadcast_address)
        data = self.__id + DELIM_1 + str(request_type)
        self.__broadcast.sendall(data.encode())

    def __end_session(self):
        print('ended session')
        self.__broadcast.close()

    def close(self):
        print('client closed connection')
        self.__start_session(END_SESSION)
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
        elif request == 'exit':
            print('see you next time.')
            break
        else:
            print('Invalid Usage')
    client.close()
