import tkinter as tk
import tkinter.messagebox
import os
import subprocess


VERSION = 0.1
VERSION_TITLE = "(Version " + str(VERSION) + ")"
GUI_TITLE = "Secret Wallet"
DEFAULT_STATUS = "Select \'Store\' in order to store, or select \'Retrieve\' in order to retrieve."
STORE_TITLE = "Store"
RETRIEVE_TITLE = "Retrieve"
NAME_LABEL = "Name"
KEY_LABEL = "Key"
VALUE_LABEL = "Value"
ERROR_TITLE = "Error"
EMPTY_ENTRY_ERROR = "Cannot store empty entries"
NAME_ERROR = "Name is already stored"
INVALID_NAME_ERROR = "Invalid Name"
INVALID_KEY_ERROR = "Invalid Key"
STORE_SUCCESS_MSG = "Successfully Stored!"
STORE_FAILURE_MSG = "Store Failed."
RETRIEVE_SUCCESS_MSG = "Successfully Retrieved!"
RETRIEVE_FAILURE_MSG = "Retrieve Failed."
EMPTY_ENTRY = ""
WINDOW_SIZE = '800x400'
STATUS_TIMEOUT = 4000


class ClientGUI:

    def __init__(self, master):
        self.__transactions = dict()

        self.__master = master
        self.__status = tk.Label(master, text=DEFAULT_STATUS)
        self.__create_window()
        self.__master.mainloop()

    def __create_title(self):
        self.__master.title(GUI_TITLE + " " + VERSION_TITLE)
        title_frame = tk.Frame(self.__master)
        title_image = tk.PhotoImage(file="Title.png")
        title = tk.Label(title_frame, image=title_image)
        title.image = title_image  # Required for displaying the image.

        title.pack()
        title_frame.pack()

    def __create_sub_title(self):
        sub_title_frame = tk.Frame(self.__master)
        tk.Label(sub_title_frame, height=2).pack()
        tk.Label(sub_title_frame, text="Please select action...",
                 font=('Verdana', 15), height=2).pack()
        sub_title_frame.pack()

    def __create_status_bar(self):
        self.__status.config(bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.__status.pack(side=tk.BOTTOM, fill=tk.X)

    @staticmethod
    def __top_secret():
        file_path = os.getcwd() + os.path.sep + 'TopSecret.mp3'
        subprocess.Popen(r'vlc ' + file_path, shell=True)

    def __create_menu(self):
        main_menu = tk.Menu(self.__master, tearoff=False)
        self.__master.config(menu=main_menu)

        # Tools:
        tools_menu = tk.Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label="Tools", menu=tools_menu)

        # TODO: command.
        tools_menu.add_command(label="Top Secret", command=self.__top_secret)

        tools_menu.add_separator()

        # Tools --> Command:
        command_menu = tk.Menu(tools_menu, tearoff=False)
        tools_menu.add_cascade(label="Command", menu=command_menu)
        command_menu.add_command(label="Store", command=self.__store)
        command_menu.add_command(label="Retrieve", command=self.__retrieve)

        tools_menu.add_separator()

        tools_menu.add_command(label="Exit", command=self.__master.quit)

        # Help:
        help_menu = tk.Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label="Help", menu=help_menu)
        # TODO: Add commands.
        help_menu.add_command(label="Help")
        help_menu.add_command(label="About")

    def __status_change(self, status_message, bad=False):
        color = 'red' if bad else 'green'
        self.__status.config(text=status_message, fg=color)
        self.__status.after(STATUS_TIMEOUT, self.__reset_status)

    def __store(self):
        store_window = tk.Toplevel()
        store_window.title(STORE_TITLE)
        store_window.resizable(False, False)

        transaction_label = tk.Label(store_window, text=NAME_LABEL)
        key_label = tk.Label(store_window, text=KEY_LABEL)
        value_label = tk.Label(store_window, text=VALUE_LABEL)

        transaction_entry = tk.Entry(store_window)
        key_entry = tk.Entry(store_window)
        value_entry = tk.Entry(store_window)

        transaction_label.grid(row=0)
        key_label.grid(row=1)
        value_label.grid(row=2)
        transaction_entry.grid(row=0, column=1, columnspan=2)
        key_entry.grid(row=1, column=1, columnspan=2)
        value_entry.grid(row=2, column=1, columnspan=2)

        def store_command(transaction_id, key, value):
            if transaction_id == EMPTY_ENTRY or key == EMPTY_ENTRY or value == EMPTY_ENTRY:
                tkinter.messagebox.showerror(ERROR_TITLE, EMPTY_ENTRY_ERROR)
                transaction_entry.config(highlightbackground="red")
                self.__status_change(STORE_FAILURE_MSG, True)
                store_window.destroy()
                return

            if transaction_id in self.__transactions.keys():
                tkinter.messagebox.showerror(ERROR_TITLE, NAME_ERROR)
                self.__status_change(STORE_FAILURE_MSG, True)
                store_window.destroy()
                return

            self.__transactions[transaction_id] = (key, value)
            tkinter.messagebox.showinfo(message=STORE_SUCCESS_MSG)
            self.__status_change(STORE_SUCCESS_MSG)
            store_window.destroy()

        tk.Button(store_window, text='Store',
                  command=lambda: store_command(transaction_entry.get(),
                                                key_entry.get(),
                                                value_entry.get())).grid(row=3, column=1)
        tk.Button(store_window, text='Cancel',
                  command=store_window.destroy).grid(row=4, column=1)

        print(self.__transactions)

    def __retrieve(self):
        retrieve_window = tk.Toplevel()
        retrieve_window.title(RETRIEVE_TITLE)
        retrieve_window.resizable(False, False)

        transaction_label = tk.Label(retrieve_window, text=NAME_LABEL)
        key_label = tk.Label(retrieve_window, text=KEY_LABEL)

        transaction_entry = tk.Entry(retrieve_window)
        key_entry = tk.Entry(retrieve_window)

        transaction_label.grid(row=0)
        key_label.grid(row=1)
        transaction_entry.grid(row=0, column=1, columnspan=2)
        key_entry.grid(row=1, column=1, columnspan=2)

        value_string = tk.StringVar()
        tk.Label(retrieve_window, textvariable=value_string, fg='red').grid(row=2, column=1)

        def retrieve_command(transaction_id, key):
            if transaction_id not in self.__transactions.keys():
                tkinter.messagebox.showerror(ERROR_TITLE, INVALID_NAME_ERROR)
                self.__status_change(RETRIEVE_FAILURE_MSG, True)
                retrieve_window.destroy()
                return

            real_key, real_value = self.__transactions[transaction_id]
            if key != real_key:
                tkinter.messagebox.showerror(ERROR_TITLE,
                                             INVALID_KEY_ERROR)

                self.__status_change(RETRIEVE_FAILURE_MSG, True)
                retrieve_window.destroy()
            else:
                value_string.set(real_value)
                self.__status_change(RETRIEVE_SUCCESS_MSG)

        tk.Button(retrieve_window, text='Retrieve',
                  command=lambda: retrieve_command(transaction_entry.get(),
                                                   key_entry.get())).grid(row=3, column=1)
        tk.Button(retrieve_window, text='Cancel',
                  command=retrieve_window.destroy).grid(row=4, column=1)

        print(self.__transactions)

    def __reset_status(self):
        self.__status.config(text=DEFAULT_STATUS, fg='black')

    def __create_buttons(self):
        button_bar = tk.Frame(self.__master)
        button_bar.pack(side=tk.TOP, fill=tk.X)
        store_icon = tk.PhotoImage(file="Store.png").subsample(2, 2)
        retrieve_icon = tk.PhotoImage(file="Retrieve.png").subsample(2, 2)

        store_button = tk.Button(button_bar, command=self.__store)
        store_button.config(image=store_icon)
        store_button.image = store_icon

        retrieve_button = tk.Button(button_bar, command=self.__retrieve)
        retrieve_button.config(image=retrieve_icon)
        retrieve_button.image = retrieve_icon

        store_button.pack(side=tk.LEFT, padx=100, pady=15)
        retrieve_button.pack(side=tk.RIGHT, padx=100, pady=15)

    def __create_window(self):
        self.__master.geometry(WINDOW_SIZE)
        self.__master.resizable(False, False)
        self.__create_title()
        self.__create_sub_title()
        self.__create_status_bar()
        self.__create_buttons()
        self.__create_menu()


if __name__ == '__main__':
    root = tk.Tk()
    client = ClientGUI(root)
