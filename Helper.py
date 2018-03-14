from numpy.polynomial.polynomial import polyval2d
import numpy as np

F = 1
NUM_OF_SERVERS = (3 * F) + 1
BUFFER_SIZE = 1024
DELIM_1 = ','
DELIM_2 = '~'
DISCOVER_IP = '127.0.0.1'
DISCOVER_PORT = 5555
END_SESSION = 0
STORE = 1
RETRIEVE = 2
P = 14447
COMPLAINT = 0
OK = 1


def create_random_bivariate_polynomial(secret, deg):
    s = np.random.randint(low=1, high=P, size=[deg+1, deg+1], dtype=int)
    s[0][0] = secret
    return s


def poly2str(p):
    data = ''
    for i in p:
        data += str(i) + DELIM_1
    return data[:-1]


def deal_vss(cid, servers, broadcast, name, secret):
    s = create_random_bivariate_polynomial(secret, F)
    x, y = np.meshgrid(np.arange(1, NUM_OF_SERVERS+1), np.arange(1, NUM_OF_SERVERS+1))
    values = np.mod(polyval2d(x, y, s).astype(int), P)

    for sid, server_sock in servers.items():
        g = values[sid, :]
        h = values[:, sid]
        data = name + DELIM_2 + poly2str(g) + DELIM_2 + poly2str(h)
        server_sock.sendall(data.encode())

    # receive complaints
    report_mat = np.eye(NUM_OF_SERVERS, dtype=bool)
    complaint_mat = []
    while True:
        nodes, status = broadcast.recv(4).decode().split(DELIM_2)  # receive i,j~OK or i,j~COMPLAINT
        status = int(status)
        i, j = nodes.split(DELIM_1)
        report_mat[i, j] = True
        if status == COMPLAINT:  # add complaint
            complaint_mat.append((i, j))
        # todo deal with complaints



