from numpy.polynomial.polynomial import polyval2d
import numpy as np
import select
from threading import Thread
import time
from scipy.interpolate import lagrange
from itertools import combinations

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
VALUE_DIGITS = 5
COMPLAINT = 'COMPLAINT'
SYNCED = 'SYNCED'
OK = 'OK1'
OK2 = 'OK2'
ERROR = 'ERR'
FIN_COMPLAINTS = 'FIN_COMPLAINTS'
FIN_OK1 = 'FIN_OK1'
FIN_SUCCESS = 'FIN_SUCC'
FIN_FAILURE = 'FIN_FAIL'
ENOUGH_OK1 = 'ENOUGH_OK1'
BROADCAST_HOST = 'localhost'
INVALID_NAME_ERR = 'Name not in DB'
INVALID_KEY_ERR = 'Invalid Key'
NAME_ALREADY_TAKEN = 'Name already in use'
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
        data += str(i) + DELIM_1
    return data[:-1]


def str2pol(s):
    p = []
    values = s.split(DELIM_1)
    for i in values:
        p.append(int(i))
    return p


def robust_interpolation(x, y, deg):
    p = {}
    max_votes = 0
    best = None
    for indices in combinations(range(len(x)), deg+1):
        x_cur, y_cur = x[list(indices)], y[list(indices)]
        p[indices] = np.around(lagrange(x_cur, y_cur).coef).astype(int)
    for indices in p:
        values = np.polyval(p[indices], x)
        inliers = np.count_nonzero((values - y) == 0)
        if inliers > max_votes:
            best = p[indices]
            max_votes = inliers
    return best


def find_degree(y_array):
    if np.all(np.array(y_array) == y_array[0]):
        return 0
    deg = 1
    prev_array = y_array
    while True:
        diff_array = []
        for i in range(len(prev_array) - 1):
            diff_array.append(prev_array[i+1] - prev_array[i])
        prev_array = diff_array
        diff_array = np.array(diff_array)
        if np.all(diff_array == diff_array[0]):  # if all diffs equals
            break
        deg += 1

    return deg




