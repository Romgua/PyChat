import base64
import tkinter as tk
import threading
from tkinter import scrolledtext
from tkinter import messagebox
import pyaes

ENCODING = 'utf-8'
RSA_KEY = None


class GUI(threading.Thread):
    def __init__(self, client, args=None):
        super().__init__(daemon=False, target=self.run, args=args)
        self.args = args
        self.font = ('Helvetica', 13)
        self.client = client
        self.login_window = None
        self.main_window = None

        # RSA_KEY
        if self.args and len(self.args) > 1:
            global RSA_KEY
            RSA_KEY = self.args[1].encode(ENCODING)

    def run(self):
        self.login_window = LoginWindow(self, self.font, self.args)
        self.main_window = ChatWindow(self, self.font)
        if not self.args:
            self.notify_server(self.login_window.login, 'login')
        else:
            self.notify_server(self.args[0], 'login')
        self.main_window.run()

    @staticmethod
    def display_alert(message):
        """Display alert box"""
        messagebox.showinfo('Error', message)

    def update_login_list(self, active_users):
        """Update login list in main window with list of users"""
        self.main_window.update_login_list(active_users)

    def display_message(self, message):
        """Display message in ChatWindow"""
        self.main_window.display_message(message)

    def beautify_message(self, message):
        """Beautify message to display in ChatWindow"""
        return self.main_window.beautify_message(message)

    def send_message(self, message):
        """Enqueue message in client's queue"""
        self.client.queue.put(message)

    def set_target(self, target):
        """Set target for messages"""
        self.client.target = target

    def notify_server(self, message, action):
        """Notify server after action was performed"""
        data = action + ";" + message
        data = data.encode(ENCODING)
        self.client.notify_server(data, action)

    def login(self, login):
        self.client.notify_server(login, 'login')

    def logout(self, logout):
        self.client.notify_server(logout, 'logout')


class Window(object):
    def __init__(self, title, font):
        self.root = tk.Tk()
        self.title = title
        self.root.title(title)
        self.font = font


class LoginWindow(Window):
    def __init__(self, gui, font, args):
        if not args:
            super().__init__("Login", font)
        self.gui = gui
        self.label = None
        self.entry = None
        self.button = None
        self.login = None

        if not args:
            self.build_window()
            self.run()
        else:
            self.login = args[0]

    def build_window(self):
        """Build login window, , set widgets positioning and event bindings"""
        self.label = tk.Label(self.root, text='Enter your login', width=20, font=self.font)
        self.label.pack(side=tk.LEFT, expand=tk.YES)

        self.entry = tk.Entry(self.root, width=20, font=self.font)
        self.entry.focus_set()
        self.entry.pack(side=tk.LEFT)
        self.entry.bind('<Return>', self.get_login_event)

        self.button = tk.Button(self.root, text='Login', font=self.font)
        self.button.pack(side=tk.LEFT)
        self.button.bind('<Button-1>', self.get_login_event)

    def run(self):
        """Handle login window actions"""
        self.root.mainloop()
        self.root.destroy()

    def get_login_event(self, event):
        """Get login from login box and close login window"""
        self.login = self.entry.get()
        self.root.quit()


class ChatWindow(Window):
    def __init__(self, gui, font):
        super().__init__("Python Chat", font)
        self.gui = gui
        self.messages_list = None
        self.logins_list = None
        self.entry = None
        self.send_button = None
        self.exit_button = None
        self.lock = threading.RLock()
        self.target = ''
        self.login = self.gui.login_window.login

        self.build_window()

    def build_window(self):
        """Build chat window, set widgets positioning and event bindings"""
        # Size config
        self.root.geometry('750x500')
        self.root.minsize(600, 400)

        # Frames config
        main_frame = tk.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky=tk.N + tk.S + tk.W + tk.E)

        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        # List of messages
        frame00 = tk.Frame(main_frame)
        frame00.grid(column=0, row=0, rowspan=2, sticky=tk.N + tk.S + tk.W + tk.E)

        # List of logins
        frame01 = tk.Frame(main_frame)
        frame01.grid(column=1, row=0, rowspan=3, sticky=tk.N + tk.S + tk.W + tk.E)

        # Message entry
        frame02 = tk.Frame(main_frame)
        frame02.grid(column=0, row=2, columnspan=1, sticky=tk.N + tk.S + tk.W + tk.E)

        # Buttons
        frame03 = tk.Frame(main_frame)
        frame03.grid(column=0, row=3, columnspan=2, sticky=tk.N + tk.S + tk.W + tk.E)

        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=8)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # ScrolledText widget for displaying messages
        self.messages_list = scrolledtext.ScrolledText(frame00, wrap='word', font=self.font)
        self.messages_list.insert(tk.END, 'Welcome to Python Chat\n')
        self.messages_list.configure(state='disabled')

        # Listbox widget for displaying active users and selecting them
        self.logins_list = tk.Listbox(frame01, selectmode=tk.SINGLE, font=self.font,
                                      exportselection=False)
        self.logins_list.bind('<<ListboxSelect>>', self.selected_login_event)

        # Entry widget for typing messages in
        self.entry = tk.Text(frame02, font=self.font)
        self.entry.focus_set()
        self.entry.bind('<Return>', self.send_entry_event)

        # Button widget for sending messages
        self.send_button = tk.Button(frame03, text='Send', font=self.font)
        self.send_button.bind('<Button-1>', self.send_entry_event)

        # Button for exiting
        self.exit_button = tk.Button(frame03, text='Exit', font=self.font)
        self.exit_button.bind('<Button-1>', self.exit_event)

        # Positioning widgets in frame
        self.messages_list.pack(fill=tk.BOTH, expand=tk.YES)
        self.logins_list.pack(fill=tk.BOTH, expand=tk.YES)
        self.entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)
        self.send_button.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)
        self.exit_button.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)

        # Protocol for closing window using 'x' button
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing_event)

    def run(self):
        """Handle chat window actions"""
        self.root.mainloop()
        self.root.destroy()

    def selected_login_event(self, event):
        """Set as target currently selected login on login list"""
        target = self.logins_list.get(self.logins_list.curselection())
        self.target = target
        self.gui.set_target(target)

    def send_entry_event(self, event):
        """Send message from entry field to target"""
        global message
        text = self.entry.get(1.0, tk.END)
        if text != '\n':
            if RSA_KEY:
                # Encrypt!
                aes = pyaes.AESModeOfOperationOFB(RSA_KEY)
                # Message encrypt in bytes
                msg = aes.encrypt(text[:-1])
                # Base64 encode message to send to server
                my_msg = base64.b64encode(msg)
                message = bytes('msg;' + self.login + ';' + self.target + ';', ENCODING) + my_msg
            else:
                message = 'msg;' + self.login + ';' + self.target + ';' + text
                message = message.encode(ENCODING)

            self.gui.send_message(message)
            self.entry.mark_set(tk.INSERT, 1.0)
            self.entry.delete(1.0, tk.END)
            self.entry.focus_set()
        else:
            messagebox.showinfo('Warning', 'You must enter non-empty message')

        with self.lock:
            self.messages_list.configure(state='normal')
            if text != '\n':
                if self.isBytes(message):
                    text = self.beautify_message(message)
                else:
                    text = self.beautify_message(message.split(';'))
                self.messages_list.insert(tk.END, text)
            self.messages_list.configure(state='disabled')
            self.messages_list.see(tk.END)
        return 'break'

    def exit_event(self, event):
        """Send logout message and quit app when "Exit" pressed"""
        self.gui.notify_server(self.login, 'logout')
        self.root.quit()

    def on_closing_event(self):
        """Exit window when 'x' button is pressed"""
        self.exit_event(None)

    def display_message(self, message):
        """Display message in ScrolledText widget"""
        with self.lock:
            self.messages_list.configure(state='normal')
            self.messages_list.insert(tk.END, message)
            self.messages_list.configure(state='disabled')
            self.messages_list.see(tk.END)

    def update_login_list(self, active_users):
        """Update listbox with list of active users"""
        self.logins_list.delete(0, tk.END)
        for user in active_users:
            self.logins_list.insert(tk.END, user)
        self.logins_list.select_set(0)
        self.target = self.logins_list.get(self.logins_list.curselection())

    def beautify_message(self, msg):
        text = msg
        if len(msg) > 3:
            if self.isBytes(msg):
                msg = msg.decode(ENCODING).split(';')
            text = msg[1] + ' >> [' + msg[2] + '] '

            # If message encrypted
            if RSA_KEY:
                aes = pyaes.AESModeOfOperationOFB(RSA_KEY)
                #base64 decode
                decoded_msg = base64.b64decode(msg[3])
                # Decrypt!
                decryptedMsg = aes.decrypt(decoded_msg).decode(ENCODING)

                text += decryptedMsg
            else:
                text += msg[3]

            # If message received
            # if (msg[1] != self.login):
            text += '\r\n'

        return text

    def isBytes(self, msg):
        return type(msg) == type(b'')
