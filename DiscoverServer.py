import socket
from Server import NUM_OF_SERVERS, DELIM, DISCOVER_PORT, BUFFER_SIZE


class DiscoverServer:

    def __init__(self):
        self.__welcome = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__welcome.bind(('localhost', DISCOVER_PORT))
        print('discover server is live with ip: ' + socket.gethostbyname('localhost') +
              ' and port: ' + str(DISCOVER_PORT))
        print('waiting for broadcast server to connect')
        self.__welcome.listen(1)
        broadcast_socket, self.__broadcast_address = self.__welcome.accept()
        broadcast_host, broadcast_port = self.__broadcast_address[0][0], str(self.__broadcast_address[0][1])
        print('connected successfully to broadcast server')
        broadcast_socket.close()
        print('broadcast discovered successfully and connection was closed')

        self.__servers_addresses = []
        servers = []
        connections = 0

        while connections < NUM_OF_SERVERS:
            self.__welcome.listen(4)
            conn, address = self.__welcome.accept()
            cur_id = str(connections + 1)
            conn.sendall((cur_id + DELIM + broadcast_host + DELIM + broadcast_port).encode())
            connections += 1
            servers.append(conn)
            self.__servers_addresses.append(address)
            print('connected successfully to server:' + cur_id + ' in ip: ' + address[0] +
                  ' and port number: ' + str(address[1]))

        for i, sock in enumerate(servers):
            cur_host = self.__servers_addresses[i][0]
            cur_port = str(self.__servers_addresses[i][1])
            cur_id = str(i + 1)
            sock.sendall((cur_id + DELIM + cur_host + DELIM + cur_port).encode())
            sock.close()
            print('server: ' + cur_id + ' was discovered successfully and connection was closed')

    def connect_to_clients(self):
        pass

    def close(self):
        self.__welcome.close()


if __name__ == '__main__':
    discover_server = DiscoverServer()
