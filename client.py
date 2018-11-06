import socket, time, select, queue, os, sys
from gui import *

ENCODING = 'utf-8'
HOST = 'localhost'
PORT = 5000


class Client(threading.Thread):
    def __init__(self, host, port):
        super().__init__(daemon=True, target=self.run)

        self.host = host
        self.port = port
        self.sock = None
        self.connected = self.connect_to_server()
        self.buffer_size = 1024

        self.queue = queue.Queue()
        self.lock = threading.RLock()

        self.login = ''
        self.login_list = ['ALL']
        # # If login is past by shell argument
        # if sys.argv[2:]:
        #     self.login = sys.argv[2]
        #     self.login_list = ['ALL', sys.argv[2]]

        self.target = ''

        if self.connected:
            if sys.argv[2:]:
                self.gui = GUI(self, sys.argv[2:])
            else:
                self.gui = GUI(self)
            self.start()
            self.gui.start()
            # Only gui is non-daemon thread, therefore after closing gui app will quit

    def connect_to_server(self):
        """Connect to server via socket interface, return (is_connected)"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((str(self.host), int(self.port)))
        except ConnectionRefusedError:
            print("Server is inactive, unable to connect")
            return False
        return True

    def run(self):
        """Handle client-server communication using select module"""
        inputs = [self.sock]
        outputs = [self.sock]
        while inputs:
            try:
                read, write, exceptional = select.select(inputs, outputs, inputs)
            # if server unexpectedly quits, this will raise ValueError exception (file descriptor < 0)
            except ValueError:
                print('Server error')
                GUI.display_alert('Server error has occurred. Exit app')
                self.sock.close()
                break

            if self.sock in read:
                with self.lock:
                    try:
                        data = self.sock.recv(self.buffer_size)
                        print("client.py - 61: data =", data)
                    except socket.error:
                        print("Socket error")
                        GUI.display_alert('Socket error has occurred. Exit app')
                        self.sock.close()
                        break

                self.process_received_data(data)

            if self.sock in write:
                if not self.queue.empty():
                    data = self.queue.get()
                    print("client.py - 68: data = ", data)
                    self.send_message(data)
                    self.queue.task_done()
                else:
                    time.sleep(0.05)

            if self.sock in exceptional:
                print('Server error')
                GUI.display_alert('Server error has occurred. Exit app')
                self.sock.close()
                break

    def process_received_data(self, data):
        """Process received message from server"""
        if data:
            message = data.decode(ENCODING)
            print("client.py - 90: message = ", message)
            if '#pseudo' not in message and 'joined the chat' not in message:
                print("client.py - 92: message = ", message)
                if 'has now pseudo' in message:
                    message = message.split("pseudo")
                    message = message[1].strip()
                    if message not in self.login_list:
                        self.add_to_login_list(message)
                        text = message + ' has joined the chat.\n'
                        self.gui.display_message(text)

                elif 'left the chat' in message:
                    message = message.split("left")
                    message = message[0].strip()
                    text = message + ' has left the chat.\n'
                    self.gui.display_message(text)
                    print("client.py - 92: self.login_list = ", self.login_list)
                    print("client.py - 92: message = ", message)
                    if message in self.login_list:
                        self.remove_to_login_list(message)

                else:
                    message = message.split(">")
                    msg = message[1].strip().split(";")
                    print("client.py - 101: ", message)

                    if '::ffff' in msg:
                        msg = msg[23:]

                    print("client.py - 106: msg = ", msg)

                    if msg[1] not in self.login_list:
                        self.add_to_login_list(msg[1])

                    print("client.py - 111: self.login = ", self.login)
                    if msg[2] == self.login or msg[2] == 'ALL':
                        text = self.beautify_message(msg)
                        print("client.py - 114: text = ", text)
                        self.gui.display_message(text)

    def notify_server(self, action, action_type):
        """Notify server if action is performed by client"""
        self.queue.put(action)
        if action_type == "login":
            self.login = action.decode(ENCODING).split(';')[1]
        elif action_type == "logout":
            self.sock.close()

    def send_message(self, data):
        """"Send encoded message to server"""
        with self.lock:
            try:
                actions = data.decode(ENCODING).split(';')
                print("client.py - 132: data = ", data)
                print("client.py - 133: actions = ", actions)
                if actions[0] == "login":
                    data = "#pseudo=" + actions[1]
                    data = data.encode()
                print("client.py - 139: data = ", data)
                self.sock.send(data)
            except socket.error:
                self.sock.close()
                GUI.display_alert('Server error has occurred. Exit app')

    def add_to_login_list(self, user):
        self.login_list.append(user)
        self.gui.update_login_list(self.login_list)

    def remove_to_login_list(self, user):
        print("client.py - 156 : self.login_list = ", self.login_list)
        self.login_list.remove(user)
        print("client.py - 158 : self.login_list = ", self.login_list)
        self.gui.update_login_list(self.login_list)

    def beautify_message(self, msg):
        return self.gui.beautify_message(msg)


# Create new client with (IP, port)
if __name__ == '__main__':
    # If HOST is past by shell argument
    if sys.argv[1:]:
        HOST = sys.argv[1]
    Client(HOST, PORT)
