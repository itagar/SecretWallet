import socket
import random
from threading import Thread
from Helper import *

BUFFER_SIZE = 1024


class Server:
    """
    A Server in the Secret Wallet system
    """

    def __init__(self, port, is_byzantine=False, is_crash=False):
        """
        constructor for Server object
        :param port:
        :param is_byzantine:
        """
        if is_byzantine:
            print('a byzantine server')

        if is_crash:
            print('a crash server')

        # create welcome socket
        self.__welcome = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__welcome.bind((socket.gethostbyname(socket.gethostname()), port))
        self.__welcome.listen(NUM_OF_SERVERS)
        print('welcome socket established in ip:', socket.gethostbyname(socket.gethostname()), ' and port: ', str(port))

        # connect to discover server
        self.__discover = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__discover.connect((DISCOVER_IP, DISCOVER_PORT))
        discover_msg = socket.gethostbyname(socket.gethostname()) + DELIM_1 + str(port)
        send_msg(self.__discover, discover_msg)
        print('connected to discover server successfully.')

        # connect to broadcast server
        self.__id, broadcast_host, broadcast_port = receive_msg(self.__discover).split(DELIM_1)
        self.__id = int(self.__id)
        self.__p_i = int(receive_msg(self.__discover))
        print('server id is: ' + str(self.__id))
        self.__broadcast = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__broadcast.connect((broadcast_host, int(broadcast_port)))
        self.__send_broadcast(str(self.__id))
        print('server' + str(self.__id) + ' connected to broadcast server successfully.')

        # connect to other servers
        self.__servers_out = {}
        self.__servers_in = {}
        self.__secrets = {}
        self.__clients = {}
        self.__establish_servers_connection()
        self.__discover.close()

        # is the server faulty
        self.__is_byzantine = is_byzantine
        self.__is_crash = is_crash

    def __establish_servers_connection(self):
        """
        establish connection with the other servers
        :return: None
        """
        t1 = Thread(target=self.__accept_servers)
        t2 = Thread(target=self.__connect_servers)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        print('established connection to all servers.')

    def __accept_servers(self):
        """
        accepts servers connection
        :return:
        """
        connections = 0
        while connections < NUM_OF_SERVERS-1:
            conn, address = self.__welcome.accept()
            cur_id = int(receive_msg(conn))
            self.__servers_in[cur_id] = conn
            connections += 1
            print('accepted connection from server: ' + str(cur_id))

    def __connect_servers(self):
        """
        connect to other servers
        :return: None
        """
        addresses = receive_msg(self.__discover).split(DELIM_2)
        for address in addresses:
            cur_id, cur_host, cur_port = address.split(DELIM_1)
            cur_id = int(cur_id)
            if cur_id != self.__id:
                print(cur_id, cur_host, int(cur_port))
                self.__servers_out[cur_id] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.__servers_out[cur_id].connect((cur_host, int(cur_port)))
                self.__send_to_server(cur_id, str(self.__id))
                print('connected to server: ' + str(cur_id))

    def __session(self, client_socket, client_id, request):
        """
        starts a new session with client in the system
        :param client_socket: client socket - socket
        :param client_id: client id - int
        :param request: STORE or RETRIEVE
        :return: None
        """
        print('started session with client: ', client_id)

        if request == STORE:
            print('client: ', client_id, ' wish to store.')
            self.__store_session(client_socket)

        elif request == RETRIEVE:
            print('client: ', client_id, ' wish to retrieve.')
            self.__retrieve_session(client_socket)

        else:
            print('session with client: ', client_id, ' closed successfully.')
            client_socket.close()

    def handle_requests(self):
        """
        handles requests from user
        :return:
        """
        inputs = [self.__welcome, self.__broadcast]
        crash = False
        while True:
            print('ready to accept clients')
            print('current secrets: ', self.__secrets)
            self.__welcome.listen(NUM_OF_SERVERS)
            readable, writable, exceptional = select.select(inputs, [], inputs)
            for r in readable:

                # in case faulty
                if not crash:
                    crash = np.random.choice([False, True])
                    if crash:
                        print('crash into space')

                if r is self.__welcome:  # accept new clients
                    conn, address = self.__welcome.accept()
                    cid = int(receive_msg(conn))
                    self.__clients[cid] = conn
                    inputs.append(conn)
                    print('connected to client: ', cid)

                elif r is self.__broadcast:  # new session
                    # get cid and request type
                    data = self.__receive_broadcast()[1].split(DELIM_1)
                    if self.__is_crash and crash:
                        continue
                    cid, request = int(data[0]), int(data[1])
                    client_sock = self.__clients[cid]
                    self.__session(client_sock, cid, request)

                # remove clients in exit
                elif r in self.__clients.values():
                    if not receive_msg(r):
                        inputs.remove(r)
                        cid = self.__cid_from_socket(r)
                        print('removed client: ', cid)
                        del self.__clients[cid]
                        r.close()

    def __store_session(self, client_sock):
        """
        a new store session with client in the system
        :param client_sock: client socket - socket
        :return: None
        """
        sender, name = self.__receive_broadcast()
        status_mat = np.zeros(NUM_OF_SERVERS)
        if name not in self.__secrets:
            self.__send_broadcast(OK)
            status_mat[self.__id - 1] = True
        else:
            self.__send_broadcast(NAME_ALREADY_TAKEN)

        response_mat = np.zeros(NUM_OF_SERVERS)
        response_mat[self.__id - 1] = True
        while not response_mat.all():
            i, status = self.__receive_broadcast(True)
            if i == TIMEOUT:
                print('received timeout in name checking')
                break
            response_mat[i - 1] = True
            if status == OK:
                status_mat[i - 1] = True

        # less then N-F have name in secrets
        if np.count_nonzero(status_mat) < (NUM_OF_SERVERS - F):
            print('name: ', name, ' is already in use')
            return NAME_ALREADY_TAKEN

        # decide if harm in case byzantine
        harm = np.random.choice([True, False])

        q_k_i = self.__node_vss(client_sock)
        q_v_i = self.__node_vss(client_sock, harm)
        self.__secrets[name] = q_k_i, q_v_i

    def __retrieve_session(self, client_sock):
        """
        a new retrieve session with client in the system
        :param client_sock: client socket - socket
        :return: None
        """
        sender, name = self.__receive_broadcast()
        status_mat = np.zeros(NUM_OF_SERVERS)
        if name in self.__secrets:
            self.__send_broadcast(OK)
            status_mat[self.__id - 1] = True
            q_k_i, q_v_i = self.__secrets[name]
        else:
            self.__send_broadcast(INVALID_NAME_ERR)
            q_k_i, q_v_i = 0, 0

        response_mat = np.zeros(NUM_OF_SERVERS)
        response_mat[self.__id - 1] = True
        while not response_mat.all():
            i, status = self.__receive_broadcast(True)
            if i == TIMEOUT:
                print('received timeout in name validation')
                break
            response_mat[i - 1] = True
            if status == OK:
                status_mat[i - 1] = True

        # less then N-F have name in secrets
        if np.count_nonzero(status_mat) < (NUM_OF_SERVERS - F):
            print('name: ', name, ' not in secrets')
            return INVALID_NAME_ERR

        q_d_i = self.__node_vss(client_sock)
        R_i = (q_k_i - q_d_i) * self.__p_i

        # send value of R_i to all servers
        self.__send_broadcast(str(R_i))

        # receive values of R_j from all other servers
        report_mat = np.zeros(NUM_OF_SERVERS)
        report_mat[self.__id-1] = True
        X = [self.__id]
        Y = [R_i]
        while not report_mat.all():
            j, R_j = self.__receive_broadcast(True)
            if j == TIMEOUT:
                break
            report_mat[j-1] = True
            X.append(j)
            Y.append(int(R_j))

        # interpolate R and retrieve key if R(0)=0
        print('X:', X)
        print('Y:', Y)
        R = robust_interpolation(np.array(X), np.array(Y), 2 * F)
        print('R:', R)
        R_0 = np.polyval(R, 0)
        print('R(0)', R_0)

        if R_0 == 0:
            print('key authenticated - sending q_v_i to client')
            send_msg(client_sock, OK + DELIM_2 + str(q_v_i))
        else:
            print('invalid key - send error to client')
            send_msg(client_sock, ERROR + DELIM_2 + '#')

    def __sid_from_socket(self, sock):
        """
        return sid of a given server socket
        :param sock: a server socket
        :return: if server - sid associated with server socket, else - 0
        """
        for sid, server_sock in self.__servers_in.items():
            if sock is server_sock:
                return sid
        return 0

    def __cid_from_socket(self, sock):
        """
        return cid of a given client socket
        :param sock: a client socket
        :return: if client - cid associated with client socket, else - 0
        """
        for cid, client_sock in self.__clients.items():
            if sock is client_sock:
                return cid
        return 0

    def __send_broadcast(self, data):
        """
        sends broadcast message
        :param data: data server wish to broadcast
        :return: None
        """
        send_msg(self.__broadcast, data)

    def __receive_broadcast(self, timeout=False):
        """
        receives a broadcast message
        :param timeout: if True wait stop waiting after T seconds
        :return: data received from broadcast or TIMEOUT if T expired
        """
        data = receive_msg(self.__broadcast, timeout)
        if data == TIMEOUT:
            return TIMEOUT, None
        sender, data = data.split(SENDER_DELIM)
        return int(sender), data

    def __send_to_server(self, sid, data):
        """
        sends a message to server
        :param sid: server id
        :param data: data you wish to send
        :return: None
        """
        send_msg(self.__servers_out[sid], data)

    def __receive_from_server(self, sid, timeout=False):
        """
        receives message from server
        :param sid: server id
        :param timeout: if True wait stop waiting after T seconds
        :return: data received from server or TIMEOUT if T expired
        """
        data = receive_msg(self.__servers_in[sid], timeout)
        if data == TIMEOUT:
            return TIMEOUT
        return data

    def close(self):
        """
        close servers connection upon exit
        :return:
        """
        self.__welcome.close()
        self.__discover.close()
        self.__broadcast.close()
        for sid in self.__servers_in:
            self.__servers_in[sid].close()
        for sid in self.__servers_out:
            self.__servers_out[sid].close()

    def __node_vss(self, dealer, harm=False):
        """
        a node role in vss protocol
        :param dealer: dealer's socket = socket
        :param harm: flag for byzantine node to harm protocol - boolean
        :return: vss share
        """
        values = receive_msg(dealer).split(DELIM_2)
        g_i = str2pol(values[0])
        h_i = str2pol(values[1])
        print('recieved polynomials from dealer')
        print('g_i: ', g_i)
        print('h_i: ', h_i)

        if harm and self.__is_byzantine:
            print('server wants to harm - random polynomial')
            g_i = np.random.randint(0, P, NUM_OF_SERVERS + 1)
            h_i = np.random.randint(0, P, NUM_OF_SERVERS + 1)

        else:
            # check polynomial degrees are F - if not switch to zero polynomial
            if find_degree(g_i) != F:
                print('invalid values - degree of induced polynomials is not F')
                g_i = np.zeros(NUM_OF_SERVERS + 1)
            if find_degree(h_i) != F:
                print('invalid values - degree of induced polynomials is not F')
                h_i = np.zeros(NUM_OF_SERVERS + 1)

        # send values to all servers
        for j in self.__servers_out:
            data = str(g_i[j]) + DELIM_1 + str(h_i[j])
            self.__send_to_server(j, data)
            print('sent values to server: ', str(j))

        # receive and check values from all servers
        report = np.zeros(NUM_OF_SERVERS)
        report[self.__id - 1] = True
        complaints = []
        inputs = self.__servers_in.values()

        while not report.all():
            readers, writers, xers = select.select(inputs, [], [], T)
            # case timeout
            if not readers:
                print('received timeout while waiting for server values')
                criminals = (np.where(report == False)[0] + 1).tolist()
                complaints.extend(criminals)
                break
            for r in readers:
                j = self.__sid_from_socket(r)
                if j > 0:
                    data = self.__receive_from_server(j)
                    g_j_i, h_j_i = data.split(DELIM_1)
                    g_j_i, h_j_i = int(g_j_i), int(h_j_i)
                    print('received values from server: ', str(j))
                    report[j - 1] = True
                    if g_j_i != h_i[j] or h_j_i != g_i[j]:
                        complaints.append(j)

        print('received values from all nodes')
        print('complained: ', complaints)

        # report status for each node
        status_mat = np.eye(NUM_OF_SERVERS)
        report_mat = np.eye(NUM_OF_SERVERS)
        report_mat[self.__id - 1, :] = True

        for i in range(1, NUM_OF_SERVERS + 1):
            if i == self.__id:
                continue
            if i in complaints:
                status_mat[self.__id - 1, i - 1] = False
                data = str(i) + DELIM_2 + COMPLAINT
                self.__send_broadcast(data)
                print('sent complaint server: ', str(i))
            else:
                status_mat[self.__id - 1, i - 1] = True
                data = str(i) + DELIM_2 + SYNCED
                self.__send_broadcast(data)
                print('sent synced server: ', str(i))
        while not report_mat.all():
            i, data = self.__receive_broadcast()
            if i == 0 and data == TIMEOUT_COMPLAINTS:
                print('timeout whlie waiting for complaints')
                break
            j, stat = data.split(DELIM_2)
            j = int(j)
            report_mat[i - 1, j - 1] = True
            if stat == SYNCED:
                print('heard synced server: ', str(i), ' on server: ', str(j))
                status_mat[i - 1, j - 1] = True
            else:
                print('heard complaint server: ', str(i), ' on server: ', str(j))
                status_mat[i - 1, j - 1] = False

        # receive responses to complaints from dealer
        while True:
            data = self.__receive_broadcast()[1]
            if data == FIN_COMPLAINTS:
                print('dealer finished complaint solving phase')
                break
            nodes, vals = data.split(DELIM_2)
            i, j = nodes.split(DELIM_1)
            i, j = int(i), int(j)
            print('dealer broadcast: ', str(i), ' and: ', str(j), ' values: ', vals)
            status_mat[i - 1, j - 1] = True
            g_i_j, h_i_j = vals.split(DELIM_1)
            if j == self.__id:  # update my values if necessary
                print('updated g_i and h_i')
                g_i[i] = int(h_i_j)
                h_i[i] = int(g_i_j)
            elif i == self.__id:
                print('updated g_i and h_i')
                g_i[j] = int(g_i_j)
                h_i[j] = int(h_i_j)

        print('after complaints g_i: ', g_i)
        print('after complaints h_i: ', h_i)

        # decide if send ok or not
        ok_error_mat = np.zeros(NUM_OF_SERVERS)

        data = OK
        ok_flag = True

        # if all complaints were solved and polynomials are of degree F send OK1
        if np.all(status_mat) and find_degree(g_i) == F and find_degree(h_i) == F:
            ok_error_mat[self.__id - 1] = True
            print('sent OK1')
        else:
            data = ERROR
            print('sent ERROR1')
            ok_flag = False

        self.__send_broadcast(data)

        # receive all OK or ERROR from all servers
        report_mat = np.zeros(NUM_OF_SERVERS)
        report_mat[self.__id - 1] = True

        while not np.all(report_mat):
            i, data = self.__receive_broadcast()
            if i == 0 and data == TIMEOUT_OK1:
                print('timeout while waiting for OK1')
                break
            i = int(i)
            report_mat[i - 1] = True
            if data == OK:
                print('heard OK1 from node: ', int(i))
                ok_error_mat[i - 1] = True
            else:
                print('heard ERROR1 from node: ', int(i))

        # case less then n-f OK's return the zero-polynomial
        if np.count_nonzero(ok_error_mat) < (NUM_OF_SERVERS - F):
            print('heard less then n-f OK1 - commit to zero polynomial')
            # wait for vss fin signal
            self.__receive_broadcast()
            return 0

        print('heard at least n-f OK1')
        # receive new shares for servers which did not send ok
        honest_dealer_flag = True
        while True:
            data = self.__receive_broadcast()[1]
            if data == FIN_OK1:
                break
            j, g_j, h_j = data.split(DELIM_2)
            j = int(j)
            ok_error_mat[j - 1] = True
            g_j = str2pol(g_j)
            h_j = str2pol(h_j)
            if find_degree(g_j) != F or find_degree(h_j) != F:
                print('dishonest dealer')
                honest_dealer_flag = False
            if self.__id == j:
                g_i = g_j
                h_i = h_j
            else:
                g_i[j] = h_j[self.__id]
                h_i[j] = g_j[self.__id]

        print('dealer finished broadcasting polynomials')

        # decide if send OK2
        report_mat = np.zeros(NUM_OF_SERVERS)
        report_mat[self.__id - 1] = True
        ok2_error_mat = np.zeros(NUM_OF_SERVERS)

        # case solve all complaints and my polynomials are of degree F and dealer responded with degree F polynomials
        if ok_flag and honest_dealer_flag and np.all(ok_error_mat) and find_degree(g_i) == F and find_degree(h_i) == F:
            print('sent OK2')
            ok2_error_mat[self.__id - 1] = True
            self.__send_broadcast(OK2)

        # case dealer didn't solve all complaints
        else:
            self.__send_broadcast(ERROR)
            print('sent ERROR2')

        while not np.all(report_mat):
            i, data = self.__receive_broadcast()
            if i == 0 and data == TIMEOUT_OK2:
                print('timeout while waiting for OK2')
                break
            print("data: ERROR2 or OK2 from i", data,' ', i)
            i = int(i)
            report_mat[i - 1] = True
            if data == OK2:
                print('heard OK2 from: ', str(i))
                ok2_error_mat[i - 1] = True
            else:
                print('heard ERROR2 from: ', str(i))

        if self.__is_byzantine and harm:
            self.__receive_broadcast()
            return np.random.randint(0, P)

        # at least n-f sent ok2 - success
        if np.count_nonzero(ok2_error_mat) >= (NUM_OF_SERVERS - F):
            print('at least n-f OK2 - VSS success')
            q_i = g_i[0]

        # less then n-f sent ok2 - failure - return zero polynomial
        else:
            print('less then n-f OK2 - VSS failure')
            q_i = 0

        # wait for vss fin signal
        self.__receive_broadcast()
        return q_i


if __name__ == '__main__':
    faulty = False
    crash = False
    my_input = input('please insert b for byzantine server or anything else for non-faulty: ')
    if my_input == 'b':
        faulty = True
    if my_input == 'c':
        crash = True
    # pick random port
    welcome_port = random.randint(6000, 10000)
    server = Server(welcome_port, faulty, crash)

    # run system
    try:
        server.handle_requests()
    finally:
        print('server exiting system')
        server.close()

