import tkinter as tk


VERSION = 0.1


class Client:

    def __init__(self, master):
        self.__transactions = dict()

        self.__master = master
        self.__create_window()
        self.__master.mainloop()

    def __create_title(self):
        self.__master.title("Secret Wallet (Version " + str(VERSION) + ")")
        title_frame = tk.Frame(self.__master)
        title = tk.Label(title_frame)
        title.config(text="Secret Wallet", font=('Verdana', 25))
        title.pack()
        title_frame.pack()

    def __create_status_bar(self):
        status_bar = tk.Label(self.__master)
        status_bar.config(bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def __store(self):
        store_window = tk.Toplevel()
        store_window.title("Store")
        store_window.resizable(False, False)

        transaction_label = tk.Label(store_window, text="Transaction ID")
        key_label = tk.Label(store_window, text="Key")
        value_label = tk.Label(store_window, text="Value")

        transaction_entry = tk.Entry(store_window)
        key_entry = tk.Entry(store_window)
        value_entry = tk.Entry(store_window)

        transaction_label.grid(row=0)
        key_label.grid(row=1)
        value_label.grid(row=2)
        transaction_entry.grid(row=0, column=1, columnspan=2)
        key_entry.grid(row=1, column=1, columnspan=2)
        value_entry.grid(row=2, column=1, columnspan=2)

        tk.Button(store_window, text='Store').grid(row=3, column=1)
        tk.Button(store_window, text='Cancel', command=store_window.quit).grid(row=4, column=1)

    def __retrieve(self):
        store_window = tk.Toplevel()
        store_window.title("Retrieve")
        store_window.resizable(False, False)

        transaction_label = tk.Label(store_window, text="Transaction ID")
        key_label = tk.Label(store_window, text="Key")

        transaction_entry = tk.Entry(store_window)
        key_entry = tk.Entry(store_window)

        transaction_label.grid(row=0)
        key_label.grid(row=1)
        transaction_entry.grid(row=0, column=1, columnspan=2)
        key_entry.grid(row=1, column=1, columnspan=2)

        tk.Button(store_window, text='Retrieve').grid(row=2, column=1)
        tk.Button(store_window, text='Cancel', command=store_window.quit).grid(row=3, column=1)

    def __create_buttons(self):
        store_button = tk.Button(self.__master)
        store_button.config(text="Store", command=self.__store)
        retrieve_button = tk.Button(self.__master)
        retrieve_button.config(text="Retrieve", command=self.__retrieve)
        store_button.pack(side=tk.LEFT)
        retrieve_button.pack(side=tk.RIGHT)

    def __create_window(self):
        self.__master.geometry('800x600')
        self.__master.resizable(False, False)
        self.__create_title()
        self.__create_status_bar()
        self.__create_buttons()


if __name__ == '__main__':
    root = tk.Tk()
    client = Client(root)
