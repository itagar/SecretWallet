import socket
from Helper import *
from numpy.polynomial.polynomial import polyval2d


class Client:
    """
    A Client in the SecretWallet system
    """

    def __init__(self):
        """
        constructor for Client object
        """
        # discover network
        discover = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        discover.connect((DISCOVER_IP, DISCOVER_PORT))
        data = receive_msg(discover)
        addresses = data.split(DELIM_2)
        self.__id = addresses[0]
        print('client: ', self.__id, ' discovered network')
        discover.close()

        # socket for broadcast
        self.__broadcast = None
        self.__broadcast_address = (addresses[1].split(DELIM_1))
        self.__broadcast_address = (self.__broadcast_address[0], int(self.__broadcast_address[1]))

        # connect to servers
        self.__servers = {}
        for address in addresses[2:]:
            cur_id, cur_ip, cur_port = address.split(DELIM_1)
            cur_id = int(cur_id)
            self.__servers[cur_id] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__servers[cur_id].connect((cur_ip, int(cur_port)))
            self.__send_to_server(cur_id, str(self.__id))

            print('client connected successfully to server: ', cur_id,
                  ' in ip: ', cur_ip, ' and port: ', cur_port)
        print('client connected successfully to all servers')

    def __get_sid(self, sock):
        """
        return the sid
        :param sock: a socket
        :return: the sid associated with the given socket or 0 if not in servers
        """
        for sid, server_sock in self.__servers.items():
            if sock is server_sock:
                return sid
        return 0

    def store(self, name, key, value):
        """
        Stores a secret in the system
        :param name: secret title
        :param key: secret key - decimal number
        :param value: secret value - decimal number
        :return: one of the following:
        DECIMAL_ERR - incase key or value are not decimal
        NAME_ALREADY_TAKEN - in case name already in use
        OK - otherwise
        """
        if not key.isdecimal():
            print('key has to be a number')
            return DECIMAL_ERR
        if not value.isdecimal():
            print('value has to be an number')
            return DECIMAL_ERR
        # modify to range
        key = int(key) % P
        value = int(value) % P
        self.__start_session(STORE)
        print('start store: name=', name, ', key=', str(key), ', value=', str(value))
        self.__send_broadcast(name)

        # check if name already taken
        response_mat = np.zeros(NUM_OF_SERVERS)
        status_mat = np.zeros(NUM_OF_SERVERS)
        while not response_mat.all():
            i, status = self.__receive_broadcast(True)  # todo
            if i == TIMEOUT:
                print('timeout in name validation')
                break
            response_mat[i - 1] = True
            if status == OK:
                status_mat[i - 1] = True

        # less then N-F have place for name in secrets
        if np.count_nonzero(status_mat) < (NUM_OF_SERVERS - F):
            print(NAME_ALREADY_TAKEN)
            return NAME_ALREADY_TAKEN

        self.__deal_vss(key)
        self.__deal_vss(value)
        print('store key,value successfully')
        self.__end_session()
        return OK

    def retrieve(self, name, key):
        """
        Retrieves a secret from system
        :param name: name of the stored secret
        :param key: key of the stored secret - decimal
        :return: one of the following:
        DECIMAL_ERR - in case key is not a decimal
        INVALID_NAME_ERR - in case name already in use
        INVALID_KEY_ERR - in case the key is invalid
        otherwise - returns the value of the stored secret - int
        """
        if not key.isdecimal():
            print('key has to be a number')
            return DECIMAL_ERR
        # modify to range
        key = int(key) % P
        self.__start_session(RETRIEVE)
        print('start retrieve: name=', name, ', key=', str(key))
        self.__send_broadcast(name)

        # check if name in secrets
        response_mat = np.zeros(NUM_OF_SERVERS)
        status_mat = np.zeros(NUM_OF_SERVERS)
        while not response_mat.all():
            i, status = self.__receive_broadcast(True)  # todo
            if i == TIMEOUT:
                print('timeout in name validation')
                break
            response_mat[i-1] = True
            if status == OK:
                status_mat[i-1] = True

        # less then N-F have name in secrets
        if np.count_nonzero(status_mat) < (NUM_OF_SERVERS - F):
            return INVALID_NAME_ERR

        self.__deal_vss(key)  # share q_d of secret key'
        response_mat = np.zeros(NUM_OF_SERVERS)
        X = []
        Y = []
        inputs = list(self.__servers.values())
        inputs.append(self.__broadcast)
        timeout_flag = False
        while not response_mat.all():
            if timeout_flag:
                readers, writers, xers = select.select(inputs, [], inputs, T)
            else:
                readers, writers, xers = select.select(inputs, [], inputs)
            if not readers:
                print('received timeout while waiting for response from system')
                break
            for r in readers:
                if r is self.__broadcast:
                    self.__receive_broadcast()
                else:
                    timeout_flag = True
                    i = self.__get_sid(r)
                    response_mat[i-1] = True
                    status, value = self.__receive_from_server(i).split(DELIM_2)
                    if status == OK:
                        print('got value from node: ', str(i))
                        X.append(i)
                        Y.append(int(value))
                    else:
                        print('got error from node: ', str(i))
        self.__end_session()
        if len(X) >= (NUM_OF_SERVERS - F):
            q = robust_interpolation(np.array(X), np.array(Y), F)
            return np.polyval(q, 0)
        else:
            return INVALID_KEY_ERR

    def __send_to_server(self, sid, data):
        """
        sends message to server
        :param sid: server id
        :param data: data you wish to send
        :return: None
        """
        send_msg(self.__servers[sid], data)

    def __receive_from_server(self, sid, timeout=False):
        """
        receive a message from server
        :param sid: server id
        :param timeout: if True send TIMEOUT after T seconds
        :return: received data or TIMEOUT
        """
        return receive_msg(self.__servers[sid], timeout)

    def __send_broadcast(self, data):
        """
        sends broadcast message
        :param data: data you wish to broadcast
        :return: None
        """
        send_msg(self.__broadcast, data)

    def __receive_broadcast(self, timeout=False):
        """
        receives message from broadcast
        :param timeout: if True send TIMEOUT after T seconds
        :return: data received from broadcast channel or TIMEOUT
        """
        data = receive_msg(self.__broadcast, timeout)
        if data == TIMEOUT:
            return TIMEOUT, None
        sender, data = data.split(SENDER_DELIM)
        return int(sender), data

    def __start_session(self, request_type):
        """
        Start session for storing or retrieving secrets
        :param request_type: STORE or RETRIEVE
        :return: None
        """
        self.__broadcast = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__broadcast.connect(self.__broadcast_address)
        data = self.__id + DELIM_1 + str(request_type)
        self.__send_broadcast(data)

    def __end_session(self):
        """
        close session
        :return: None
        """
        print('ended session')
        self.__broadcast.close()

    def exit(self):
        """
        exit from system
        :return: None
        """
        print('client closed connection')
        for sid in self.__servers:
            self.__servers[sid].close()

    def __deal_vss(self, secret):
        """
        Deals secret according to VSS protocol
        :param secret: Secret you wish to store - integer
        :return: OK in case everything went well or ERROR otherwise
        """
        s = create_random_bivariate_polynomial(secret, F)
        x, y = np.meshgrid(np.arange(0, NUM_OF_SERVERS + 1), np.arange(0, NUM_OF_SERVERS + 1))
        s_values = polyval2d(x, y, s).astype(int)

        for sid in self.__servers:
            g = s_values[sid, :]
            h = s_values[:, sid]
            data = poly2str(g) + DELIM_2 + poly2str(h)
            print('deal polynomials to server: ', str(sid))
            self.__send_to_server(sid, data)

        # receive complaints
        report_mat = np.eye(NUM_OF_SERVERS, dtype=bool)
        complaints = []
        timeout_flag = False  # todo
        while not np.all(report_mat):
            i, data = self.__receive_broadcast(timeout_flag)  # todo
            timeout_flag = True
            if i == TIMEOUT:
                print('received timeout while waiting for status report')
                where = np.where(report_mat == False)
                complaints.extend([(where[0][i] + 1, where[1][i] + 1) for i in range(len(where[0]))])
                break
            j, status = data.split(DELIM_2)  # receive i#j~OK or i#j~COMPLAINT
            j = int(j)
            report_mat[i - 1, j - 1] = True
            print('received complaint status from: ', str(i), ' on: ', str(j))
            if status == COMPLAINT:  # add complaint
                complaints.append((i, j))

        # solve complaints
        for i, j in complaints:
            # broadcast i,j~S(i,j),S(j,i)
            print('solved complaint of: ', i, ' on: ', j)
            data = str(i) + DELIM_1 + str(j) + DELIM_2 + str(s_values[i, j]) + DELIM_1 + str(s_values[j, i])
            self.__send_broadcast(data)

        # finished complaints resolving
        print('finished solving complaints')
        data = FIN_COMPLAINTS
        self.__send_broadcast(data)

        # wait for OK
        report_mat = np.zeros(NUM_OF_SERVERS, dtype=bool)
        errors_sid = []
        while not np.all(report_mat):
            i, status = self.__receive_broadcast(True)  # receive (i,OK) or (i,ERROR)
            if i == TIMEOUT:  # todo
                print('received timeout while waiting for ok')
                errors_sid.extend(np.where(report_mat == False)[0] + 1)
                break
            report_mat[i - 1] = True
            if status == ERROR:
                print('node: ', str(i), ' sent ERROR1')
                errors_sid.append(i)
            else:
                print('node: ', str(i), ' sent OK1')

        # less then n-f sent OK - failure
        if len(errors_sid) > F:
            print('less then n-f OK1')
            self.__send_broadcast(FIN_VSS)
            return ERROR

        # broadcast polynomials of all error nodes
        for i in errors_sid:
            # broadcast i~S(i,y)~S(x,i)
            print('broadcast polynomial of: ', str(i))
            g_i = poly2str(s_values[sid, :])
            h_i = poly2str(s_values[:, sid])
            data = str(i) + DELIM_2 + g_i + DELIM_2 + h_i
            self.__send_broadcast(data)

        # finished broadcasting not ok's polynomials
        self.__send_broadcast(FIN_OK1)
        print('finished broadcasting polynomials')

        # wait for OK2
        report_mat = np.zeros(NUM_OF_SERVERS, dtype=bool)
        status_mat = np.zeros(NUM_OF_SERVERS, dtype=bool)

        while not np.all(report_mat):
            i, status = self.__receive_broadcast(True)  # receive (i,OK2) or (i,ERROR2)
            if i == TIMEOUT:  # todo
                print('received timeout while waiting for OK2')
                break
            report_mat[i - 1] = True
            if status == OK2:
                print('received OK2 from: ', str(i))
                status_mat[i - 1] = True
            else:
                print('received ERROR2 from: ', str(i))

        # at least n-f nodes sent ok2 - success
        if np.count_nonzero(status_mat) >= (NUM_OF_SERVERS - F):
            print('at least n-f OK2 - VSS success')
            self.__send_broadcast(FIN_VSS)
            return OK

        # less then n-f sent ok2 - failure
        else:
            print('less then n-f OK2 - VSS failure')
            self.__send_broadcast(FIN_VSS)
            return ERROR


if __name__ == '__main__':
    client = Client()
    while True:
        request = input('what should i do next: ')
        if request == 'store':
            secret_name, secret_key, secret_value = input('please insert: name key value ').split()
            client.store(secret_name, secret_key, secret_value)
        elif request == 'ret':
            secret_name, secret_key = input('please insert: name key ').split()
            value = client.retrieve(secret_name, secret_key)
            if value == INVALID_NAME_ERR:
                print(secret_name, ' is not in database')
            elif value == INVALID_KEY_ERR:
                print(INVALID_KEY_ERR)
            else:
                print('correct key - value is: ', value)

        elif request == 'exit':
            print('see you next time.')
            break
        else:
            print('Invalid Usage ')
    client.exit()
