import tkinter as tk
import tkinter.messagebox


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
WINDOW_SIZE = '800x600'
STATUS_TIMEOUT = 4000


class Client:

    def __init__(self, master):
        self.__transactions = dict()

        self.__master = master
        self.__status = tk.Label(master, text=DEFAULT_STATUS)
        self.__create_window()
        self.__master.mainloop()

    def __create_title(self):
        self.__master.title(GUI_TITLE + " " + VERSION_TITLE)
        title_frame = tk.Frame(self.__master)
        title = tk.Label(title_frame)
        title.config(text=GUI_TITLE, font=('Verdana', 25))
        title.pack()
        title_frame.pack()

    def __create_status_bar(self):
        self.__status.config(bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.__status.pack(side=tk.BOTTOM, fill=tk.X)

    def __status_change(self, status_message, bad=False):
        color = 'red' if bad else 'green'
        self.__status.config(text=status_message, fg=color)
        self.__status.after(STATUS_TIMEOUT, self.reset_status)

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

    def reset_status(self):
        self.__status.config(text=DEFAULT_STATUS, fg='black')

    def __create_buttons(self):
        store_button = tk.Button(self.__master)
        store_button.config(text=STORE_TITLE, command=self.__store)
        retrieve_button = tk.Button(self.__master)
        retrieve_button.config(text=RETRIEVE_TITLE, command=self.__retrieve)
        store_button.pack(side=tk.LEFT)
        retrieve_button.pack(side=tk.RIGHT)

    def __create_window(self):
        self.__master.geometry(WINDOW_SIZE)
        self.__master.resizable(False, False)
        self.__create_title()
        self.__create_status_bar()
        self.__create_buttons()


if __name__ == '__main__':
    root = tk.Tk()
    client = Client(root)
