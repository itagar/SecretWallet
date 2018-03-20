from numpy.polynomial.polynomial import polyval2d
import numpy as np
import select
import Server
from threading import Thread, Lock
import time

F = 1
NUM_OF_SERVERS = (3 * F) + 1
BUFFER_SIZE = 1024
DELIM_1 = ','
DELIM_2 = '~'
SENDER_DELIM = '#'
DISCOVER_IP = '127.0.0.1'
DISCOVER_PORT = 4400
END_SESSION = 0
STORE = 1
RETRIEVE = 2
P = 14447
COMPLAINT = 'COMPPLAINT'
SYNCED = 'SUNCED'
OK = 'OK1'
OK2 = 'OK2'
ERROR = 'ERR'
FIN_COMPLAINTS = 'FIN_COMPLAINTS'
FIN_OK1 = 'FIN_OK1'
FIN_SUCCESS = 'FIN_SUCC'
FIN_FAILURE = 'FIN_FAIL'
ENOUGH_OK1 = 'ENOUGH_OK1'
VALUE_DIGITS = 5
BROADCAST_HOST = 'localhost'
BROADCAST_PORT = 4401
CLIENT_SENDER_ID = 0


def send_msg(sock, data):
    length = str(len(data)).zfill(3)  # todo magic
    sock.sendall((length + data).encode())


def receive_msg(sock):
    length = sock.recv(3).decode()  # todo magic
    if not length:
        return
    data = sock.recv(int(length)).decode()
    return data


def create_random_bivariate_polynomial(secret, deg):
    s = np.random.randint(low=1, high=P, size=[deg+1, deg+1], dtype=int)
    s[0][0] = secret
    return s


def poly2str(p):
    data = ''
    for i in p:
        data += str(i).zfill(VALUE_DIGITS) + DELIM_1
    return data[:-1]


def str2pol(s):
    p = []
    values = s.split(DELIM_1)
    for i in values:
        p.append(int(i))
    return p


def node_vss(server, dealer=None):
    if dealer:  # case dealer is not server
        dealer.lock.aquire()
        values = receive_msg(dealer).split(DELIM_2)
        dealer.lock.release()
    else:  # dealer is server
        values = server.values  # todo maybe add values for client
    g_i = str2pol(values[0])
    h_i = str2pol(values[1])
    print('recieved polynomials from dealer')
    print('g_i: ', g_i)
    print('h_i: ', h_i)

    # todo check polynomial degrees if not F then polynomial is zeros

    # send values to all servers
    for j in server.servers_out:
        data = str(g_i[j]).zfill(VALUE_DIGITS) + DELIM_1 + str(h_i[j]).zfill(VALUE_DIGITS)
        server.send_to_server(j, data)
        print('sent values to server: ', str(j))

    # receive and check values from all servers
    report = np.zeros(NUM_OF_SERVERS)
    report[server.get_id()-1] = True
    complaints = []
    inputs = server.servers_in.values()

    while not report.all():
        readers, writers, xers = select.select(inputs, [], [])
        for r in readers:
            j = server.get_sid(r)
            if j > 0:
                data = server.receive_from_server(j)
                g_j_i, h_j_i = data.split(DELIM_1)
                g_j_i, h_j_i = int(g_j_i), int(h_j_i)
                print('received values from server: ', str(j))
                report[j-1] = True
                if g_j_i != h_i[j] or h_j_i != g_i[j]:
                    complaints.append(j)

    print('received values from all nodes')
    print('complained: ', complaints)

    # report status for each node
    status_mat = np.eye(NUM_OF_SERVERS)
    report_mat = np.eye(NUM_OF_SERVERS)
    report_mat[server.get_id()-1, :] = True

    for i in range(1, NUM_OF_SERVERS+1):
        if i == server.get_id():
            continue
        if i in complaints:
            status_mat[server.get_id()-1, i-1] = False
            data = str(i) + DELIM_2 + COMPLAINT
            server.send_broadcast(data)
            print('sent complaint server: ', str(i))
        else:
            status_mat[server.get_id()-1, i - 1] = True
            data = str(i) + DELIM_2 + SYNCED
            server.send_broadcast(data)
            print('sent synced server: ', str(i))

    while not report_mat.all():
        i, data = server.receive_broadcast()
        j, stat = data.split(DELIM_2)
        j = int(j)
        report_mat[i-1, j-1] = True
        if stat == SYNCED:
            print('heard synced server: ', str(i), ' on server: ', str(j))
            status_mat[i-1, j-1] = True
        else:
            print('heard complaint server: ', str(i), ' on server: ', str(j))
            status_mat[i - 1, j - 1] = False

    # receive responses to complaints from dealer
    while True:
        data = server.receive_broadcast()[1]  # todo boom magic
        if data == FIN_COMPLAINTS:
            print('dealer finished complaint solving phase')
            break
        nodes, vals = data.split(DELIM_2)
        i, j = nodes.split(DELIM_1)
        i, j = int(i), int(j)
        print('dealer broadcast: ', str(i), ' and: ', str(j), ' values')
        status_mat[i-1, j-1] = True
        if i == server.get_id() or j == server.get_id():  # update my values if necessary
            g_i_j, h_i_j = vals.split(DELIM_1)
            g_i[j] = int(h_i_j)
            h_i[j] = int(g_i_j)

    # decide if send ok or not
    ok_error_mat = np.zeros(NUM_OF_SERVERS)
    # TODO - are_polynomes_ok = check_polynom_deg(g_i, h_i)
    data = OK
    ok_flag = True

    if not np.all(status_mat):  # if all complaints were solved
        data = ERROR
        print('sent ERROR1')
        ok_flag = False
    else:
        print('sent OK1')
        ok_error_mat[server.get_id() - 1] = True

    server.send_broadcast(data)

    # receive all OK or ERROR from all servers
    report_mat = np.zeros(NUM_OF_SERVERS)
    report_mat[server.get_id() - 1] = True

    while not np.all(report_mat):
        i, data = server.receive_broadcast()
        i = int(i)
        report_mat[i - 1] = True
        if data == OK:
            print('heard OK1 from node: ', int(i))
            ok_error_mat[i-1] = True
        else:
            print('heard ERROR1 from node: ', int(i))

    # case less then n-f OK's return the zero-polynomial
    if np.count_nonzero(ok_error_mat) < (NUM_OF_SERVERS - F):
        print('heard less then n-f OK1 - commit to zero polynomial')
        return np.zeros(NUM_OF_SERVERS), np.zeros(NUM_OF_SERVERS)

    print('heard at least n-f OK1')
    # receive new shares for servers which did not send ok
    while True:
        data = server.receive_broadcast()[1]  # todo magic
        if data == FIN_OK1:
            break
        j, g_j, h_j = data.split(DELIM_2)
        j = int(j)
        ok_error_mat[j-1] = True
        g_j = str2pol(g_j)
        h_j = str2pol(h_j)
        if server.get_id == j:
            g_i = g_j
            h_i = h_j
        else:
            g_i[j] = g_j[server.get_id()]
            h_i[j] = h_j[server.get_id()]

    # decide if send OK2
    report_mat = np.zeros(NUM_OF_SERVERS)
    report_mat[server.get_id() - 1] = True
    ok2_error_mat = np.zeros(NUM_OF_SERVERS)

    # case solve all complaints
    if ok_flag and np.all(ok_error_mat):  # TODO check polynomial degree
        print('sent OK2')
        ok2_error_mat[server.get_id() - 1] = True
        server.send_broadcast(OK2)

    # case dealer didn't solve all complaints
    else:
        server.send_broadcast(ERROR)
        print('sent OK2')

    while not np.all(report_mat):
        i, data = server.receive_broadcast()
        i = int(i)
        report_mat[i - 1] = True
        if data == OK2:
            print('heard OK2 from: ', str(i))
            ok2_error_mat[i - 1] = True
        else:
            print('heard ERROR2 from: ', str(i))

    # at least n-f sent ok2 - success
    if np.count_nonzero(ok2_error_mat) >= (NUM_OF_SERVERS - F):
        print('at least n-f OK2 - VSS success')
        return g_i, h_i

    # less then n-f sent ok2 - failure - return zero polynomial
    else:
        print('less then n-f OK2 - VSS failure')
        return np.zeros(NUM_OF_SERVERS), np.zeros(NUM_OF_SERVERS)


def deal_vss(dealer, servers, secret, is_server=False):
    s = create_random_bivariate_polynomial(secret, F)
    x, y = np.meshgrid(np.arange(0, NUM_OF_SERVERS+1), np.arange(0, NUM_OF_SERVERS+1))
    s_values = np.mod(polyval2d(x, y, s).astype(int), P)

    # dealer is one of servers - pass the values to the node thread through values field
    if is_server:
        dealer.values = s_values[dealer.get_id(), :]
        dealer.lock.release()

    for sid in servers:
        g = s_values[sid, :]
        h = s_values[:, sid]
        data = poly2str(g) + DELIM_2 + poly2str(h)
        dealer.send_to_server(sid, data)
        print('deal polynomials to server: ', str(sid))

    # receive complaints
    report_mat = np.eye(NUM_OF_SERVERS, dtype=bool)
    complaints = []
    while not np.all(report_mat):
        i, data = dealer.receive_broadcast()
        j, status = data.split(DELIM_2)  # receive i#j~OK or i#j~COMPLAINT
        j = int(j)
        report_mat[i-1, j-1] = True
        print('received complaint status from: ', str(i), ' on: ', str(j))
        if status == COMPLAINT:  # add complaint
            complaints.append((i, j))

    # solve complaints
    for i, j in complaints:
        # broadcast i,j~S(i,j),S(j,i)
        print('solved complaint of: ', i, ' on: ', j)
        data = str(i) + DELIM_1 + str(j) + DELIM_2 + str(s_values[i, j]).zfill(VALUE_DIGITS)\
               + DELIM_1 + str(s_values[j, i]).zfill(VALUE_DIGITS)
        dealer.send_broadcast(data)

    # finished complaints resolving
    print('finished solving complaints')
    data = FIN_COMPLAINTS
    dealer.send_broadcast(data)

    # wait for OK
    report_mat = np.zeros(NUM_OF_SERVERS, dtype=bool)
    errors_sid = []
    while True:
        i, status = dealer.receive_broadcast()  # receive (i,OK) or (i,ERROR)
        report_mat[i-1] = True
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
        dealer.send_broadcast(data)

    # finished broadcasting not ok's polynomials
    dealer.send_broadcast(FIN_OK1)
    print('finished broadcasting polynomials')

    # wait for OK2
    report_mat = np.zeros(NUM_OF_SERVERS, dtype=bool)
    status_mat = np.zeros(NUM_OF_SERVERS, dtype=bool)

    while True:
        i, status = dealer.receive_broadcast()  # receive (i,OK2) or (i,ERROR2)
        report_mat[i-1] = True
        if status == OK2:
            print('recieved OK2 from: ', str(i))
            status_mat[i-1] = True
        else:
            print('recieved ERROR2 from: ', str(i))
        if np.all(report_mat):
            break

    # at least n-f nodes sent ok2 - success
    if np.count_nonzero(status_mat) >= (NUM_OF_SERVERS - F):
        print('at least n-f OK2 - VSS success')
        return OK

    # less then n-f sent ok2 - failure
    else:
        print('less then n-f OK2 - VSS failure')
        return ERROR


def share_random_secret(server):
    for i in range(1, NUM_OF_SERVERS+1):
        if server.get_id() == i:
            r_i = np.random.randint(1, P)
            server.lock.aquire()
