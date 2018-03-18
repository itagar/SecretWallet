from numpy.polynomial.polynomial import polyval2d
import numpy as np
import select
import Server

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
COMPLAINT = '0'
OK = '3'
OK2 = '4'
ERROR = '0'
FIN_COMPLAINTS = '5'
FIN_OK1 = '6'
FIN_SUCCESS = '7'
FIN_FAILURE = '8'
ENOUGH_OK1 = '9'
VALUE_DIGITS = 5
BROADCAST_HOST = 'localhost'
BROADCAST_PORT = 4401
CLIENT_SENDER_ID = 0


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


def node_vss(server, dealer):
    values = dealer.recv(BUFFER_SIZE).decode().split(DELIM_2)
    g_i = str2pol(values[0])
    h_i = str2pol(values[1])
    print('recieved polynomials from dealer')

    # todo check polynomial degrees if not F then polynomial is zeros

    # send values to all servers
    for j in server.servers_out:
        data = str(server.get_id()) + DELIM_1 + str(g_i[j]).zfill(VALUE_DIGITS) + DELIM_1 +\
               str(h_i[j]).zfill(VALUE_DIGITS)
        server.servers_out[j].sendall(data.encode())
        print('sent values to server: ', str(j))

    # receive and check values from all servers
    report = np.zeros(NUM_OF_SERVERS)
    report[server.get_id()-1] = True
    complaints = []
    inputs = server.servers_out.values()

    while not report.all():
        print('in while')
        readers, writers, xers = select.select(inputs, [], [])
        for j in readers:
            j, g_j_i, h_j_i = j.recv(BUFFER_SIZE).decode().split(DELIM_1)
            j, g_j_i, h_j_i = int(j), int(g_j_i), int(h_j_i)
            print('received values from server: ', str(j))
            report[j-1] = True
            if g_j_i != g_i[j] or h_j_i != h_i[j]:
                print('complaint on server: ', str(j))
                complaints.append(j)
            else:
                print('synced with server: ', str(j))

    # report status for each node
    status_mat = np.eye(NUM_OF_SERVERS)
    report_mat = np.eye(NUM_OF_SERVERS)
    report_mat[:, server.get_id()] = True

    for i in range(1, NUM_OF_SERVERS):
        if i == server.get_id():
            continue
        if i in complaints:
            status_mat[server.get_id()-1, i-1] = False
            data = str(i) + DELIM_2 + COMPLAINT
            server.broadcast.sendall(data.encode())
            print('sent complaint server: ', str(i))
        else:
            status_mat[server.get_id()-1, i - 1] = True
            data = str(i) + DELIM_2 + OK
            server.broadcast.sendall(data.encode())
            print('sent synced server: ', str(i))

    while not report_mat.all():
        i, data = server.receive_broadcast(3)  # todo magic
        j, stat = data.split(DELIM_2)
        j, stat = int(j), int(stat)
        report_mat[i-1, j-1] = True
        if stat == OK:
            print('heard synced server: ', str(i), 'print on server: ', str(j))
            status_mat[i-1, j-1] = True
        else:
            print('heard complaint server: ', str(i), 'print on server: ', str(j))
            status_mat[i - 1, j - 1] = False

    # receive responses to complaints from dealer
    while True:
        data = server.receive_broadcast(15)[1]  # todo boom magic
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
        ok_error_mat[server.get_id - 1] = True

    server.broadcast.sendall(data.encode())

    # receive all OK or ERROR from all servers
    report_mat = np.zeros(NUM_OF_SERVERS)
    report_mat[server.get_id() - 1] = True

    while not np.all(report_mat):
        i, data = server.receive_broadcast(1)
        i = int(i)
        report_mat[i - 1] = True
        if data == OK:
            print('heard OK1 from node: ', int(i))
            ok_error_mat[i-1] = True
        else:
            print('heard ERROR1 from node: ', int(i))

    # case less then n-f OK's return the zero-polynomial
    if np.nonzero(ok_error_mat) < (NUM_OF_SERVERS - F):
        print('heard less then n-f OK1 - commit to zero polynomial')
        return np.zeros(NUM_OF_SERVERS), np.zeros(NUM_OF_SERVERS)

    print('heard at least n-f OK1')
    # receive new shares for servers which did not send ok
    while True:
        data = server.receive_broadcast(61)[1]  # todo magic
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
        server.broadcast.sendall(OK2.encode())

    # case dealer didn't solve all complaints
    else:
        server.broadcast.sendall(ERROR.encode())
        print('sent OK2')

    while not np.all(report_mat):
        i, data = server.receive_broadcast(1)
        i = int(i)
        report_mat[i - 1] = True
        if data == OK2:
            print('heard OK2 from: ', str(i))
            ok2_error_mat[i - 1] = True
        else:
            print('heard ERROR2 from: ', str(i))

    # at least n-f sent ok2 - success
    if np.nonzero(ok2_error_mat) >= (NUM_OF_SERVERS - F):
        print('at least n-f OK2 - VSS success')
        return g_i, h_i

    # less then n-f sent ok2 - failure - return zero polynomial
    else:
        print('less then n-f OK2 - VSS failure')
        return np.zeros(NUM_OF_SERVERS), np.zeros(NUM_OF_SERVERS)


def deal_vss(servers, broadcast, secret):
    s = create_random_bivariate_polynomial(secret, F)
    x, y = np.meshgrid(np.arange(0, NUM_OF_SERVERS+1), np.arange(0, NUM_OF_SERVERS+1))
    s_values = np.mod(polyval2d(x, y, s).astype(int), P)

    for sid, server_sock in servers.items():
        g = s_values[sid, :]
        h = s_values[:, sid]
        data = poly2str(g) + DELIM_2 + poly2str(h)
        server_sock.sendall(data.encode())
        print('deal polynomials to server: ', str(sid))

    # receive complaints
    report_mat = np.eye(NUM_OF_SERVERS, dtype=bool)
    complaints = []
    while not np.all(report_mat):
        nodes, status = broadcast.recv(5).decode().split(DELIM_2)  # receive i#j~OK or i#j~COMPLAINT
        i, j = nodes.split(SENDER_DELIM)
        i, j, status = int(i), int(j), int(status)
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
        broadcast.sendall(data.encode())

    # finished complaints resolving
    print('finished solving complaints')
    data = FIN_COMPLAINTS
    broadcast.sendall(data.encode())

    # wait for OK
    report_mat = np.zeros(NUM_OF_SERVERS, dtype=bool)
    errors_sid = []
    while True:
        i, status = broadcast.recv(3).decode().split(SENDER_DELIM)  # receive i#OK or i#ERROR  todo magic
        i, status = int(i), int(status)
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
        broadcast.sendall(data.encode())

    # finished broadcasting not ok's polynomials
    broadcast.sendall(FIN_OK1.encode())
    print('finished broadcasting polynomials')

    # wait for OK2
    report_mat = np.zeros(NUM_OF_SERVERS, dtype=bool)
    status_mat = np.zeros(NUM_OF_SERVERS, dtype=bool)

    while True:
        i, status = broadcast.recv(3).decode().split(SENDER_DELIM)  # receive i#OK2 or i#ERROR  todo magic
        i, status = int(i), int(status)
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
