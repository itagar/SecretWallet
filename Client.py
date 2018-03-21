import socket
from Helper import *


class Client:

    def __init__(self):
        # discover network
        discover = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        discover.connect((DISCOVER_IP, DISCOVER_PORT))
        data = receive_msg(discover)
        addresses = data.split(DELIM_2)
        self.__id = addresses[0]  # todo magic
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
            self.send_to_server(cur_id, str(self.__id))

            print('client connected successfully to server: ', cur_id,
                  ' in ip: ', cur_ip, ' and port: ', cur_port)
        print('client connected successfully to all servers')

    def store(self, name, key, value):
        self.__start_session(STORE)
        print('start store: name=', name, ', key=', key, ', value=', value)
        self.send_broadcast(name)  # todo name already taken
        if self.deal_vss(key) == ERROR:
            print('error with storing key')
            self.__end_session()
            return ERROR
        if self.deal_vss(value) == ERROR:
            print('error with storing value')
            self.__end_session()
            return ERROR
        print('store key,value successfully')
        self.__end_session()
        return OK

    def retrieve(self, name, key):
        self.__start_session(RETRIEVE)
        print('start retrieve: name=', name, ', key=', key)
        self.send_broadcast(name)  # todo if name not in secrets
        self.deal_vss(key)  # share q_d of secret key'
        response_mat = np.zeros(NUM_OF_SERVERS)
        while not response_mat.all():
            pass
        self.__end_session()

    def send_to_server(self, sid, data):
        send_msg(self.__servers[sid], data)

    def receive_from_server(self, sid):
        receive_msg(self.__servers[sid])

    def send_broadcast(self, data):
        send_msg(self.__broadcast, data)

    def receive_broadcast(self):
        data = receive_msg(self.__broadcast)
        sender, data = data.split(SENDER_DELIM)
        return int(sender), data

    def __start_session(self, request_type):
        self.__broadcast = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__broadcast.connect(self.__broadcast_address)
        data = self.__id + DELIM_1 + str(request_type)
        self.send_broadcast(data)

    def __end_session(self):
        print('ended session')
        self.__broadcast.close()

    def close(self):
        print('client closed connection')
        self.__start_session(END_SESSION)
        for sid in self.__servers:
            self.__servers[sid].close()

    def deal_vss(self, secret):
        s = create_random_bivariate_polynomial(secret, F)
        x, y = np.meshgrid(np.arange(0, NUM_OF_SERVERS + 1), np.arange(0, NUM_OF_SERVERS + 1))
        s_values = np.mod(polyval2d(x, y, s).astype(int), P)

        for sid in self.__servers:
            g = s_values[sid, :]
            h = s_values[:, sid]
            data = poly2str(g) + DELIM_2 + poly2str(h)
            self.send_to_server(sid, data)
            print('deal polynomials to server: ', str(sid))

        # receive complaints
        report_mat = np.eye(NUM_OF_SERVERS, dtype=bool)
        complaints = []
        while not np.all(report_mat):
            i, data = self.receive_broadcast()
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
            data = str(i) + DELIM_1 + str(j) + DELIM_2 + str(s_values[i, j]).zfill(VALUE_DIGITS) \
                   + DELIM_1 + str(s_values[j, i]).zfill(VALUE_DIGITS)
            self.send_broadcast(data)

        # finished complaints resolving
        print('finished solving complaints')
        data = FIN_COMPLAINTS
        self.send_broadcast(data)

        # wait for OK
        report_mat = np.zeros(NUM_OF_SERVERS, dtype=bool)
        errors_sid = []
        while True:
            i, status = self.receive_broadcast()  # receive (i,OK) or (i,ERROR)
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
            self.send_broadcast(data)

        # finished broadcasting not ok's polynomials
        self.send_broadcast(FIN_OK1)
        print('finished broadcasting polynomials')

        # wait for OK2
        report_mat = np.zeros(NUM_OF_SERVERS, dtype=bool)
        status_mat = np.zeros(NUM_OF_SERVERS, dtype=bool)

        while True:
            i, status = self.receive_broadcast()  # receive (i,OK2) or (i,ERROR2)
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
            return OK

        # less then n-f sent ok2 - failure
        else:
            print('less then n-f OK2 - VSS failure')
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
            client.retrieve(secret_name, secret_key)
        elif request == 'exit':
            print('see you next time.')
            break
        else:
            print('Invalid Usage ')
    client.close()
