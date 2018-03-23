import socket
import select
import random
from threading import Thread, Lock
from Helper import *

BUFFER_SIZE = 1024


class Server:

    def __init__(self, port, is_byzantine=False):
        # create welcome socket
        self.__welcome = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__welcome.bind(('localhost', port))
        self.__welcome.listen(NUM_OF_SERVERS)
        print('welcome socket established in ip:', socket.gethostbyname('localhost'), ' and port: ', str(port))

        # connect to discover server
        self.__discover = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__discover.connect((DISCOVER_IP, DISCOVER_PORT))
        discover_msg = socket.gethostbyname('localhost') + DELIM_1 + str(port)
        send_msg(self.__discover, discover_msg)
        print('connected to discover server successfully.')
        data = receive_msg(self.__discover)

        # connect to broadcast server
        self.__id, broadcast_host, broadcast_port = data.split(DELIM_1)
        self.__id = int(self.__id)
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

        # is the server byzantine
        self.__is_byzantine = is_byzantine

    def get_id(self):
        return self.__id

    def __establish_servers_connection(self):
        t1 = Thread(target=self.__accept_servers)
        t2 = Thread(target=self.__connect_servers)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        print('established connection to all servers.')

    def __accept_servers(self):
        connections = 0
        while connections < NUM_OF_SERVERS-1:
            conn, address = self.__welcome.accept()
            cur_id = int(receive_msg(conn))
            self.__servers_in[cur_id] = conn
            connections += 1
            print('accepted connection from server: ' + str(cur_id))

    def __connect_servers(self):
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
        print('started session with client: ', client_id)

        if request == STORE:
            print('client: ', client_id, ' wish to store.')
            self.__store_session(client_socket)

        elif request == RETRIEVE:
            print('client: ', client_id, ' wish to retrieve.')
            self.__retrieve_session(client_socket, client_id)

        else:
            print('session with client: ', client_id, ' closed successfully.')
            client_socket.close()

    def handle_requests(self):
        inputs = [self.__welcome, self.__broadcast]
        while True:
            print('ready to accept clients')
            print('current secrets: ', self.__secrets)
            self.__welcome.listen(NUM_OF_SERVERS)
            readable, writable, exceptional = select.select(inputs, [], inputs)
            for r in readable:

                if r is self.__welcome:  # accept new clients
                    conn, address = self.__welcome.accept()
                    cid = int(receive_msg(conn))
                    self.__clients[cid] = conn
                    inputs.append(conn)
                    print('connected to client: ', cid)

                elif r is self.__broadcast:  # new session
                    # get cid and request type
                    data = self.__receive_broadcast()[1].split(DELIM_1)
                    cid, request = int(data[0]), int(data[1])
                    client_sock = self.__clients[cid]
                    self.__session(client_sock, cid, request)

                # remove clients in exit
                elif r in self.__clients.values():
                    inputs.remove(r)
                    cid = self.__get_cid(r)
                    print('removed client: ', cid)
                    del self.__clients[cid]
                    r.close()

    def __store_session(self, client_sock):
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
            i, status = self.__receive_broadcast()
            response_mat[i - 1] = True
            if status == OK:
                status_mat[i - 1] = True

        # less then N-F have name in secrets
        if np.count_nonzero(status_mat) < (NUM_OF_SERVERS - F):
            print('name: ', name, ' is already in use')
            return NAME_ALREADY_TAKEN

        q_k_i = self.__node_vss(client_sock)
        q_v_i = self.__node_vss(client_sock)
        self.__secrets[name] = q_k_i, q_v_i

    def __retrieve_session(self, client_sock, client_id):
        sender, name = self.__receive_broadcast()
        status_mat = np.zeros(NUM_OF_SERVERS)
        if name in self.__secrets:
            self.__send_broadcast(OK)
            status_mat[self.__id - 1] = True
        else:
            self.__send_broadcast(INVALID_NAME_ERR)

        response_mat = np.zeros(NUM_OF_SERVERS)
        response_mat[self.__id - 1] = True
        while not response_mat.all():
            i, status = self.__receive_broadcast()
            response_mat[i - 1] = True
            if status == OK:
                status_mat[i - 1] = True

        # less then N-F have name in secrets
        if np.count_nonzero(status_mat) < (NUM_OF_SERVERS - F):
            print('name: ', name, ' not in secrets')
            return INVALID_NAME_ERR

        q_k_i, q_v_i = self.__secrets[name]
        q_d_i = self.__node_vss(client_sock)
        # p_i = self.share_random_secret()
        R_i = q_k_i - q_d_i

        # send value of R_i to all servers
        self.__send_broadcast(str(R_i))

        # receive values of R_j from all other servers
        report_mat = np.zeros(NUM_OF_SERVERS)
        report_mat[self.__id-1] = True
        X = np.arange(1, NUM_OF_SERVERS+1)
        Y = np.zeros(NUM_OF_SERVERS)
        Y[self.__id-1] = R_i
        while not report_mat.all():
            j, R_j = self.__receive_broadcast()
            report_mat[j-1] = True
            Y[j-1] = int(R_j)

        # interpolate R and retrieve key if R(0)=0
        print('X:', X)
        print('Y:', Y)
        R = robust_interpolation(X, Y, F)
        print('R:', R)
        R_0 = np.polyval(R, 0)
        print('R(0)', R_0)

        if R_0 == 0:
            print('key authenticated - sending q_v_i to client')
            send_msg(client_sock, OK + DELIM_2 + str(q_v_i))
        else:
            print('invalid key - send error to client')
            send_msg(client_sock, ERROR + DELIM_2 + '#')

    def __get_sid(self, sock):
        for sid, server_sock in self.__servers_in.items():
            if sock is server_sock:
                return sid
        return 0

    def __get_cid(self, sock):
        for cid, client_sock in self.__clients.items():
            if sock is client_sock:
                return cid
        return 0

    def __send_broadcast(self, data):
        send_msg(self.__broadcast, data)

    def __receive_broadcast(self):
        data = receive_msg(self.__broadcast)
        sender, data = data.split(SENDER_DELIM)
        return int(sender), data

    def __send_to_server(self, sid, data):
        send_msg(self.__servers_out[sid], data)

    def __receive_from_server(self, sid):
        data = receive_msg(self.__servers_in[sid])
        return data

    def close(self):
        self.__welcome.close()
        self.__discover.close()
        self.__broadcast.close()
        for sid in self.__servers_in:
            self.__servers_in[sid].close()
        for sid in self.__servers_out:
            self.__servers_out[sid].close()

    def __node_vss(self, dealer, dealer_id=CLIENT_SENDER_ID):
        # in case byzantine - randomly decide if to do harm
        harm = np.random.choice([True, False])
        values = receive_msg(dealer).split(DELIM_2)
        g_i = str2pol(values[0])
        h_i = str2pol(values[1])
        print('recieved polynomials from dealer')
        print('g_i: ', g_i)
        print('h_i: ', h_i)

        if harm and self.__is_byzantine:
            print('server wants to harm - random ')
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
            if j != dealer_id:  # todo
                data = str(g_i[j]) + DELIM_1 + str(h_i[j])
                self.__send_to_server(j, data)
                print('sent values to server: ', str(j))

        # receive and check values from all servers
        report = np.zeros(NUM_OF_SERVERS)
        report[self.__id - 1] = True
        if dealer_id:  # todo
            report[dealer_id - 1] = True
        complaints = []
        inputs = self.__servers_in.values()

        while not report.all():
            readers, writers, xers = select.select(inputs, [], [])
            for r in readers:
                j = self.__get_sid(r)
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

        if dealer_id:  # todo
            report_mat[dealer_id - 1, :] = True
            report_mat[:, dealer_id - 1] = True
            status_mat[dealer_id - 1, :] = True
            status_mat[:, dealer_id - 1] = True

        for i in range(1, NUM_OF_SERVERS + 1):
            if i == self.get_id() or i == dealer_id:
                continue
            if i in complaints:
                status_mat[self.get_id() - 1, i - 1] = False
                data = str(i) + DELIM_2 + COMPLAINT
                self.__send_broadcast(data)
                print('sent complaint server: ', str(i))
            else:
                status_mat[self.get_id() - 1, i - 1] = True
                data = str(i) + DELIM_2 + SYNCED
                self.__send_broadcast(data)
                print('sent synced server: ', str(i))

        while not report_mat.all():
            i, data = self.__receive_broadcast()
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

        if dealer_id:  # todo
            ok_error_mat[dealer_id - 1] = True

        data = OK
        ok_flag = True

        # if all complaints were solved and polynomials are of degree F send OK1
        if np.all(status_mat) and find_degree(g_i) == F and find_degree(h_i) == F:
            ok_error_mat[self.get_id() - 1] = True
            print('sent OK1')
        else:
            data = ERROR
            print('sent ERROR1')
            ok_flag = False

        self.__send_broadcast(data)

        # receive all OK or ERROR from all servers
        report_mat = np.zeros(NUM_OF_SERVERS)
        report_mat[self.get_id() - 1] = True

        if dealer_id:  # todo
            report_mat[dealer_id - 1] = True

        while not np.all(report_mat):
            i, data = self.__receive_broadcast()
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
            if self.get_id == j:
                g_i = g_j
                h_i = h_j
            else:
                g_i[j] = h_j[self.get_id()]
                h_i[j] = g_j[self.get_id()]

        # decide if send OK2
        report_mat = np.zeros(NUM_OF_SERVERS)
        report_mat[self.get_id() - 1] = True
        ok2_error_mat = np.zeros(NUM_OF_SERVERS)

        if dealer_id:  # todo
            report_mat[dealer_id - 1] = True
            ok2_error_mat[dealer_id - 1] = True

        # case solve all complaints and my polynomials are of degree F and dealer responded with degree F polynomials
        if ok_flag and honest_dealer_flag and np.all(ok_error_mat) and find_degree(g_i) == F and find_degree(h_i) == F:
            print('sent OK2')
            ok2_error_mat[self.get_id() - 1] = True
            self.__send_broadcast(OK2)

        # case dealer didn't solve all complaints
        else:
            self.__send_broadcast(ERROR)
            print('sent ERROR2')

        while not np.all(report_mat):
            i, data = self.__receive_broadcast()
            print("data: ERROR2 or OK2 from i", data,' ', i)
            i = int(i)
            report_mat[i - 1] = True
            if data == OK2:
                print('heard OK2 from: ', str(i))
                ok2_error_mat[i - 1] = True
            else:
                print('heard ERROR2 from: ', str(i))

        if self.__is_byzantine and harm:
            return np.random.randint(0, P)

        # at least n-f sent ok2 - success
        if np.count_nonzero(ok2_error_mat) >= (NUM_OF_SERVERS - F):
            print('at least n-f OK2 - VSS success')
            return g_i[0]

        # less then n-f sent ok2 - failure - return zero polynomial
        else:
            print('less then n-f OK2 - VSS failure')
            return 0

    def deal_vss(self, secret):
        s = create_random_bivariate_polynomial(secret, F)
        x, y = np.meshgrid(np.arange(0, NUM_OF_SERVERS + 1), np.arange(0, NUM_OF_SERVERS + 1))
        s_values = polyval2d(x, y, s).astype(int)

        for sid in self.__servers_out:
            g = s_values[sid, :]
            h = s_values[:, sid]
            data = poly2str(g) + DELIM_2 + poly2str(h)
            self.__send_to_server(sid, data)
            print('deal polynomials to server: ', str(sid))

        # receive complaints
        report_mat = np.eye(NUM_OF_SERVERS, dtype=bool)
        complaints = []

        # todo
        report_mat[self.__id - 1, :] = True
        report_mat[:, self.__id - 1] = True

        while not np.all(report_mat):
            i, data = self.__receive_broadcast()
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
        report_mat[self.__id - 1] = True  # todo
        errors_sid = []
        while True:
            i, status = self.__receive_broadcast()  # receive (i,OK) or (i,ERROR)
            report_mat[i - 1] = True
            if status == ERROR:
                print('node: ', str(i), ' sent ERROR1')
                errors_sid.append(i)
            else:
                print('node: ', str(i), ' sent OK1')
            if np.all(report_mat):
                break

        # less then n-f sent OK - failure
        if len(errors_sid) > F:
            print('less then n-f OK1')
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
        # todo
        report_mat[self.__id - 1] = True
        status_mat[self.__id - 1] = True

        while True:
            i, status = self.__receive_broadcast()  # receive (i,OK2) or (i,ERROR2)
            report_mat[i - 1] = True
            if status == OK2:
                print('recieved OK2 from: ', str(i))
                status_mat[i - 1] = True
            else:
                print('recieved ERROR2 from: ', str(i))
            if np.all(report_mat):
                break

        # at least n-f nodes sent ok2 - success
        if np.count_nonzero(status_mat) >= (NUM_OF_SERVERS - F):
            print('at least n-f OK2 - VSS success')
            return s_values[0, self.__id]

        # less then n-f sent ok2 - failure
        else:
            print('less then n-f OK2 - VSS failure')
            return 0

    def share_random_secret(self):
        p_i = 0
        for j in range(1, 2):
            if server.get_id() == j:
                print('dealing random')
                # r_i = np.random.randint(1, P)
                r_i = j
                print('r_i:' + str(r_i))
                p_i += self.deal_vss(r_i)
            else:
                print('receiving random from: ', str(j))
                p_i += self.__node_vss(self.__servers_in[j], j)
        return p_i


if __name__ == '__main__':
    is_byz = input('1 for byzantine other wise not')
    if is_byz == '1':
        is_byz = True
    else:
        is_byz = False
    welcome_port = random.randint(6000, 10000)  # todo change port assignment to discover
    server = Server(welcome_port, is_byz)
    server.handle_requests()
    server.close()
