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
DISCOVER_PORT = 5555
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

    # todo check polynomial degrees if not F then polynomial is zeros

    # send values to all servers
    for j in server.servers_out:
        data = str(server.get_id()) + DELIM_1 + str(g_i[j]).zfill(VALUE_DIGITS) + DELIM_1 +\
               str(h_i[j]).zfill(VALUE_DIGITS)
        server.servers_out[j].sendall(data.encode())

    # receive and check values from all servers
    report = np.zeros(NUM_OF_SERVERS)
    report[server.get_id()-1] = True
    complaints = []
    inputs = server.servers_out.values()

    while not report.all():
        readers, writers, xers = select.select(inputs, [], [])
        for j in readers:
            j, g_j_i, h_j_i = j.recv(BUFFER_SIZE).decode().split(DELIM_1)
            report[j-1] = True
            if g_j_i != g_i[j] or h_j_i != h_i[j]:
                complaints.append(j)

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
        else:
            status_mat[server.get_id()-1, i - 1] = True
            data = str(i) + DELIM_2 + OK
            server.broadcast.sendall(data.encode())

    while not report_mat.all():
        i, data = server.receive_broadcast(3)  # todo magic
        j, stat = data.split(DELIM_2)
        j, stat = int(j), int(stat)
        report_mat[i-1, j-1] = True
        if stat == OK:
            status_mat[i-1, j-1] = True
        else:
            status_mat[i - 1, j - 1] = False

    # receive responses to complaints from dealer
    while True:
        data = server.receive_broadcast(15)[1]  # todo boom magic
        if data == FIN_COMPLAINTS:
            break
        nodes, vals = data.split(DELIM_2)
        i, j = nodes.split(DELIM_1)
        i, j = int(i), int(j)
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
        ok_flag = False
    else:
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
            ok_error_mat[i-1] = True

    # case less then n-f OK's return the zero-polynomial
    if np.nonzero(ok_error_mat) < (NUM_OF_SERVERS - F):
        return np.zeros(NUM_OF_SERVERS), np.zeros(NUM_OF_SERVERS)

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
        ok2_error_mat[server.get_id() - 1] = True
        server.broadcast.sendall(OK2.encode())

    # case dealer didn't solve all complaints
    else:
        server.broadcast.sendall(ERROR.encode())

    while not np.all(report_mat):
        i, data = server.receive_broadcast(1)
        i = int(i)
        report_mat[i - 1] = True
        if data == OK2:
            ok2_error_mat[i - 1] = True

    # at least n-f sent ok2 - success
    if np.nonzero(ok2_error_mat) >= (NUM_OF_SERVERS - F):
        return g_i, h_i

    # less then n-f sent ok2 - failure - return zero polynomial
    else:
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

    # receive complaints
    report_mat = np.eye(NUM_OF_SERVERS, dtype=bool)
    complaints = []
    while not np.all(report_mat):
        nodes, status = broadcast.recv(5).decode().split(DELIM_2)  # receive i#j~OK or i#j~COMPLAINT
        i, j = nodes.split(SENDER_DELIM)
        i, j, status = int(i), int(j), int(status)
        report_mat[i-1, j-1] = True
        if status == COMPLAINT:  # add complaint
            complaints.append((i, j))

    # solve complaints
    for i, j in complaints:
        # broadcast i,j~S(i,j),S(j,i)
        data = str(i) + DELIM_1 + str(j) + DELIM_2 + str(s_values[i, j]).zfill(VALUE_DIGITS)\
               + DELIM_1 + str(s_values[j, i]).zfill(VALUE_DIGITS)
        broadcast.sendall(data.encode())

    # finished complaints resolving
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
            errors_sid.append(i)
        if np.all(report_mat):
            break

    # less then n-f sent OK - failure
    if len(errors_sid) > F:
        return ERROR

    # broadcast polynomials of all error nodes
    for i in errors_sid:
        # broadcast i~S(i,y)~S(x,i)
        g_i = poly2str(s_values[sid, :])
        h_i = poly2str(s_values[:, sid])
        data = str(i) + DELIM_2 + g_i + DELIM_2 + h_i
        broadcast.sendall(data.encode())

    # finished broadcasting not ok's polynomials
    broadcast.sendall(FIN_OK1.encode())

    # wait for OK2
    report_mat = np.zeros(NUM_OF_SERVERS, dtype=bool)
    status_mat = np.zeros(NUM_OF_SERVERS, dtype=bool)

    while True:
        i, status = broadcast.recv(3).decode().split(SENDER_DELIM)  # receive i#OK2 or i#ERROR  todo magic
        i, status = int(i), int(status)
        report_mat[i-1] = True
        if status == OK2:
            status_mat[i-1] = True
        if np.all(report_mat):
            break

    # at least n-f nodes sent ok2 - success
    if np.count_nonzero(status_mat) >= (NUM_OF_SERVERS - F):
        return OK

    # less then n-f sent ok2 - failure
    else:
        return ERROR
