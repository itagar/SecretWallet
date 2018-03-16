from numpy.polynomial.polynomial import polyval2d
import numpy as np
import select

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
COMPLAINT = 0
OK = 1
OK2 = 1
ERROR = 0

def create_random_bivariate_polynomial(secret, deg):
    s = np.random.randint(low=1, high=P, size=[deg+1, deg+1], dtype=int)
    s[0][0] = secret
    return s


def poly2str(p):
    data = ''
    for i in p:
        data += str(i) + DELIM_1
    return data[:-1]


def str2pol(s):
    p = []
    values = s.split(DELIM_1)
    for i in values:
        p.append(int(i))
    return p


def node_vss(sid, dealer, servers, brodcast):
    values = dealer.recv(BUFFER_SIZE).decode().split(DELIM_2)
    g = str2pol(values[0])
    h = str2pol(values[1])
    pass


def deal_vss(servers, broadcast, secret):
    s = create_random_bivariate_polynomial(secret, F)
    x, y = np.meshgrid(np.arange(1, NUM_OF_SERVERS+1), np.arange(1, NUM_OF_SERVERS+1))
    s_values = np.mod(polyval2d(x, y, s).astype(int), P)

    for sid, server_sock in servers.items():
        g = s_values[sid, :]
        h = s_values[:, sid]
        data = poly2str(g) + DELIM_2 + poly2str(h)
        server_sock.sendall(data.encode())

    # receive complaints
    report_mat = np.eye(NUM_OF_SERVERS, dtype=bool)
    complaints = []
    while True:
        nodes, status = broadcast.recv(4).decode().split(DELIM_2)  # receive i#j~OK or i,j~COMPLAINT
        i, j = nodes.split(SENDER_DELIM)
        i, j, status = int(i), int(j), int(status)
        report_mat[i, j] = True
        if status == COMPLAINT:  # add complaint
            complaints.append((i, j))
        if np.all(report_mat):  # all nodes reported status
            break

    # solve complaints
    for i, j in complaints:
        # broadcast i,j~S(i,j),S(j,i)
        data = str(i) + str(j) + DELIM_2 + str(s_values[i, j]) + DELIM_1 + str(s_values[j, i])
        broadcast.sendall(data.encode())

    # wait for OK
    report_mat = np.zeros(NUM_OF_SERVERS, dtype=bool)
    errors_sid = []
    while True:
        i, status = broadcast.recv(3).decode().split(SENDER_DELIM)  # receive i#OK or i#ERROR  todo magic
        i, status = int(i), int(status)
        report_mat[i] = True
        if status == ERROR:
            errors_sid.append(i)
        if np.all(report_mat):
            break

    # broadcast polynomials of all error nodes
    for i in errors_sid:
        # broadcast i~S(i,y)~S(x,i)
        g_i = poly2str(s[sid, :])
        h_i = poly2str(s[:, sid])
        data = str(i) + DELIM_2 + g_i + DELIM_2 + h_i
        broadcast.sendall(data.encode())

    # wait for OK2
    report_mat = np.zeros(NUM_OF_SERVERS, dtype=bool)
    status_mat = np.zeros(NUM_OF_SERVERS, dtype=bool)
    while True:
        i, status = broadcast.recv(3).decode().split(SENDER_DELIM)  # receive i#OK2 or i#ERROR  todo magic
        i, status = int(i), int(status)
        report_mat[i] = True
        if status == OK2:
            status_mat[i] = True
        if np.all(report_mat):
            break

    # if at least n-f process succeeded else failed
    if np.count_nonzero(status_mat) >= (NUM_OF_SERVERS - F):
        broadcast.sendall(str().encode())
        return OK
    else:
        broadcast.sendall(str(ERROR).encode())
        return ERROR
