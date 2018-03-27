import numpy as np
import select
from scipy.interpolate import lagrange
from itertools import combinations

F = 1
NUM_OF_SERVERS = (3 * F) + 1
BUFFER_SIZE = 1024
DELIM_1 = ','
DELIM_2 = '~'
SENDER_DELIM = '#'
DISCOVER_IP = '127.0.0.1'
DISCOVER_PORT = 3331
BROADCAST_PORT = 3341
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

TIMEOUT_COMPLAINTS = 'TIMEOUT_COMPLAINTS'
TIMEOUT_OK1 = 'TIMEOUT_OK1'
TIMEOUT_OK2 = 'TIMEOUT_OK2'
FIN_COMPLAINTS = 'FIN_COMPLAINTS'
FIN_OK1 = 'FIN_OK1'
FIN_VSS = 'FIN_VSS'
FIN_SUCCESS = 'FIN_SUCC'
FIN_FAILURE = 'FIN_FAIL'

ENOUGH_OK1 = 'ENOUGH_OK1'
BROADCAST_HOST = 'localhost'
INVALID_NAME_ERR = 'Name not in DB'
INVALID_KEY_ERR = 'Invalid Key'
NAME_ALREADY_TAKEN = 'Name already in use'
DECIMAL_ERR = 'Key and value has to be decimal'
CLIENT_SENDER_ID = 0
MESSAGE_LENGTH_DIGITS = 3
TIMEOUT = 'timeout expired'
T = 0.2


def send_msg(sock, data):
    """
    sends a message to given TCP socket
    :param sock: socket
    :param data: data you wish to send - str
    :return: None
    """
    length = str(len(data)).zfill(MESSAGE_LENGTH_DIGITS)
    sock.sendall((length + data).encode())


def receive_msg(sock, timeout=False):
    """
    receive's a message from a given TCP socket
    :param sock: socket
    :param timeout: if True wait T seconds for message then fail
    :return: message from socket or TIMEOUT in case timeout expired
    """
    if timeout:
        readers, writers, xers = select.select([sock], [], [], T)
        if readers:
            length = sock.recv(MESSAGE_LENGTH_DIGITS).decode()
        else:
            return TIMEOUT
        ready = select.select([sock], [], [], T)
        if ready[0]:
            data = sock.recv(int(length)).decode()
            return data
        else:
            return TIMEOUT
    else:
        length = sock.recv(MESSAGE_LENGTH_DIGITS).decode()
        if not length:
            return
        data = sock.recv(int(length)).decode()
        return data


def create_random_bivariate_polynomial(secret, deg):
    """
    create a random bivariate polynomial S in Fp with S[0,0]=secret
    :param secret: an integer
    :param deg: degree of polynomial in x and y
    :return: a random bivariate polynomial S in Fp with S[0,0]=secret
    """
    s = np.random.randint(low=1, high=P, size=[deg+1, deg+1], dtype=int)
    s[0][0] = secret
    return s


def poly2str(p):
    """
    code a polynomial to string
    :param p: a polynomial - list
    :return: p coded to string
    """
    data = ''
    for i in p:
        data += str(i) + DELIM_1
    return data[:-1]


def str2pol(s):
    """
    decode a string to polynomial
    :param s: a polynomial coded to string
    :return: the decoded polynomial - list
    """
    p = []
    values = s.split(DELIM_1)
    for i in values:
        p.append(int(i))
    return p


def robust_interpolation(x, y, deg):
    """
    preform a robust interpolation
    :param x: array of x values - np.array
    :param y: array of y values - np.array
    :param deg:
    :return: a polynomial in degree-'deg' that agree with the most given points
    """
    p = {}
    max_votes = 0
    best = None
    for indices in combinations(range(len(x)), deg+1):
        x_cur, y_cur = x[list(indices)], y[list(indices)]
        p[indices] = np.around(lagrange(x_cur, y_cur).coef).astype(int)
    for indices in p:
        values = np.polyval(p[indices], x)
        inliers = np.count_nonzero((values - y) == 0)
        print(np.array(indices) + 1, ': ', p[indices], ' inliers: ', inliers)
        if inliers > max_votes:
            best = p[indices]
            max_votes = inliers
    return best


def find_degree(y_array):
    """
    returns the degree of polynomial fit to the given values
    :param y_array: y values of: X=[0,1,2,...,len(y_array)]
    :return: the degree of the polynomial fit to y_array
    """
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
