import tkinter as tk
import tkinter.messagebox
import os
import subprocess


# Titles and Messages:
VERSION = 0.1
VERSION_TITLE = "(Version " + str(VERSION) + ")"
GUI_TITLE = "Secret Wallet"
DEFAULT_STATUS = "Select \'Store\' in order to store, " \
                 "or select \'Retrieve\' in order to retrieve."
STORE_TITLE = "Store"
RETRIEVE_TITLE = "Retrieve"
NAME_LABEL = "Name:"
KEY_LABEL = "Key:"
VALUE_LABEL = "Value:"
ERROR_TITLE = "Error"
HELP_TITLE = "Help"
ABOUT_TITLE = "About"
EMPTY_ENTRY_ERROR = "Error: Empty entries"
NAME_ERROR = "Error: Name is already stored"
INVALID_NAME_ERROR = "Invalid Name"
INVALID_KEY_ERROR = "Invalid Key"
STORE_SUCCESS_MSG = "Successfully Stored!"
STORE_FAILURE_MSG = "Store Failed."
RETRIEVE_SUCCESS_MSG = "Successfully Retrieved!"
RETRIEVE_FAILURE_MSG = "Retrieve Failed."

# Images Attributes:
TITLE_IMAGE = "Title.png"
STORE_IMAGE = "Store.png"
RETRIEVE_IMAGE = "Retrieve.png"
SUB_TITLE_IMAGE = "SubTitle.png"

BAD_STATUS_COLOR = 'red'
GOOD_STATUS_COLOR = 'green'
DEFAULT_STATUS_COLOR = 'black'

EMPTY_ENTRY = ""
WINDOW_SIZE = '760x400'
STATUS_TIMEOUT = 4000


class ClientGUI:

    def __init__(self, master):
        """ Initialize the GUI window for the client. """
        self.__transactions = {'1': ('2', '3')}

        self.__master = master
        self.__status = tk.Label(master, text=DEFAULT_STATUS)
        self.__create_window()
        self.__master.mainloop()

    # ==----   GUI Creation Functions   ----== #

    def __create_title(self):
        """ Creates the title of the main window. """
        self.__master.title(GUI_TITLE + " " + VERSION_TITLE)
        title_frame = tk.Frame(self.__master)
        title_image = tk.PhotoImage(file=TITLE_IMAGE)
        title = tk.Label(title_frame, image=title_image)
        title.image = title_image  # Required for displaying the image.
        title.pack()
        title_frame.pack()

    def __create_sub_title(self):
        """ Creates the secondary title of the main window. """
        sub_title_frame = tk.Frame(self.__master)
        sub_title_image = tk.PhotoImage(file=SUB_TITLE_IMAGE)
        sub_title = tk.Label(sub_title_frame, image=sub_title_image)
        sub_title.image = sub_title_image  # Required for displaying the image.
        sub_title.pack()

        sub_title_frame.pack()

    def __create_status_bar(self):
        """ Creates the status bar of the GUI. """
        self.__status.config(bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.__status.pack(side=tk.BOTTOM, fill=tk.X)

    @staticmethod
    def __top_secret():
        file_path = os.getcwd() + os.path.sep + "TopSecret.mp3"
        subprocess.Popen(r'vlc ' + file_path, shell=True)

    def __create_menu(self):
        """ Creates the top main menu of the GUI. """
        # The Main Menu panel.
        main_menu = tk.Menu(self.__master, tearoff=False)
        self.__master.config(menu=main_menu)

        # Tools Menu:
        tools_menu = tk.Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label="Tools", menu=tools_menu)
        # Tools --> Top Secret.
        tools_menu.add_command(label="Top Secret", command=self.__top_secret)
        tools_menu.add_separator()
        # Tools --> Command:
        command_menu = tk.Menu(tools_menu, tearoff=False)
        tools_menu.add_cascade(label="Command", menu=command_menu)
        command_menu.add_command(label="Store", command=self.__store)
        command_menu.add_command(label="Retrieve", command=self.__retrieve)
        tools_menu.add_separator()
        # Tools --> Exit.
        tools_menu.add_command(label="Exit", command=self.__master.quit)

        # Help Menu:
        help_menu = tk.Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label="Help", menu=help_menu)
        # Help --> Help.
        help_menu.add_command(label="Help", command=self.__help)
        # Help --> About.
        help_menu.add_command(label="About", command=self.__about)

    def __create_buttons(self):
        """ Creates the buttons of the main window. """
        button_bar = tk.Frame(self.__master)
        button_bar.pack(side=tk.TOP, fill=tk.X)
        store_icon = tk.PhotoImage(file=STORE_IMAGE).subsample(2, 2)
        retrieve_icon = tk.PhotoImage(file=RETRIEVE_IMAGE).subsample(2, 2)

        store_button = tk.Button(button_bar, command=self.__store)
        store_button.config(image=store_icon)
        store_button.image = store_icon

        retrieve_button = tk.Button(button_bar, command=self.__retrieve)
        retrieve_button.config(image=retrieve_icon)
        retrieve_button.image = retrieve_icon

        store_button.pack(side=tk.LEFT, padx=100, pady=15)
        retrieve_button.pack(side=tk.RIGHT, padx=100, pady=15)

    def __create_window(self):
        """ Creates the GUI main window using all the above functions. """
        self.__master.geometry(WINDOW_SIZE)
        self.__master.resizable(False, False)
        self.__create_title()
        self.__create_sub_title()
        self.__create_status_bar()
        self.__create_buttons()
        self.__create_menu()

    # ==----   GUI Commands Functions   ----== #

    def __reset_status(self):
        """ Resets the status label in the status bar. """
        self.__status.config(text=DEFAULT_STATUS, fg=DEFAULT_STATUS_COLOR)

    def __status_change(self, status_message, bad=False):
        """ Changes the status label in the status bar to the
        given status message. The 'bad' parameter determines the color
        of the text in the status label. """
        color = BAD_STATUS_COLOR if bad else GOOD_STATUS_COLOR
        self.__status.config(text=status_message, fg=color)
        self.__status.after(STATUS_TIMEOUT, self.__reset_status)

    def __store(self):
        store_window = tk.Toplevel()
        store_window.title(STORE_TITLE)
        store_window.resizable(False, False)

        transaction_frame = tk.Frame(store_window)
        transaction_label = tk.Label(transaction_frame, width=10, text=NAME_LABEL, anchor='w')
        transaction_entry = tk.Entry(transaction_frame, width=30)
        transaction_frame.pack(side=tk.TOP, fill=tk.X, padx=3, pady=3)
        transaction_label.pack(side=tk.LEFT)
        transaction_entry.pack(side=tk.RIGHT, fill=tk.X, expand=tk.YES)

        key_frame = tk.Frame(store_window)
        key_label = tk.Label(key_frame, width=10, text=KEY_LABEL, anchor='w')
        key_entry = tk.Entry(key_frame, width=30)
        key_frame.pack(side=tk.TOP, fill=tk.X, padx=3, pady=3)
        key_label.pack(side=tk.LEFT)
        key_entry.pack(side=tk.RIGHT, fill=tk.X, expand=tk.YES)

        value_frame = tk.Frame(store_window)
        value_label = tk.Label(value_frame, width=10, text=VALUE_LABEL, anchor='w')
        value_entry = tk.Entry(value_frame, width=30)
        value_frame.pack(side=tk.TOP, fill=tk.X, padx=3, pady=3)
        value_label.pack(side=tk.LEFT)
        value_entry.pack(side=tk.RIGHT, fill=tk.X, expand=tk.YES)

        info_label = tk.Label(store_window)
        info_label.pack(fill=tk.X, expand=tk.YES)

        def store_command(transaction_id, key, value):
            # Reset entries highlight.
            transaction_entry.config(highlightbackground="grey")
            key_entry.config(highlightbackground="grey")
            value_entry.config(highlightbackground="grey")

            # Highlight empty entries.
            if transaction_id == EMPTY_ENTRY or key == EMPTY_ENTRY or value == EMPTY_ENTRY:
                if transaction_id == EMPTY_ENTRY:
                    transaction_entry.config(highlightbackground="red")
                if key == EMPTY_ENTRY:
                    key_entry.config(highlightbackground="red")
                if value == EMPTY_ENTRY:
                    value_entry.config(highlightbackground="red")

                info_label.config(text=EMPTY_ENTRY_ERROR, fg='red')
                self.__status_change(STORE_FAILURE_MSG, True)
                return

            if transaction_id in self.__transactions.keys():
                info_label.config(text=NAME_ERROR, fg='red')
                self.__status_change(STORE_FAILURE_MSG, True)
                return

            self.__transactions[transaction_id] = (key, value)
            info_label.config(text=STORE_SUCCESS_MSG, fg='green')
            self.__status_change(STORE_SUCCESS_MSG)

        button_frame = tk.Frame(store_window)
        store_button = tk.Button(button_frame, text='Store',
                                 command=lambda: store_command(transaction_entry.get(),
                                                               key_entry.get(),
                                                               value_entry.get()))
        cancel_button = tk.Button(button_frame, text='Cancel',
                                  command=store_window.destroy)
        button_frame.pack(side=tk.TOP, fill=tk.X, padx=3, pady=3)
        store_button.pack()
        cancel_button.pack()

        print(self.__transactions)

    def __retrieve(self):
        retrieve_window = tk.Toplevel()
        retrieve_window.title(RETRIEVE_TITLE)
        retrieve_window.resizable(False, False)

        transaction_frame = tk.Frame(retrieve_window)
        transaction_label = tk.Label(transaction_frame, width=10,
                                     text=NAME_LABEL, anchor='w')
        transaction_entry = tk.Entry(transaction_frame, width=30)
        transaction_frame.pack(side=tk.TOP, fill=tk.X, padx=3, pady=3)
        transaction_label.pack(side=tk.LEFT)
        transaction_entry.pack(side=tk.RIGHT, fill=tk.X, expand=tk.YES)

        key_frame = tk.Frame(retrieve_window)
        key_label = tk.Label(key_frame, width=10, text=KEY_LABEL, anchor='w')
        key_entry = tk.Entry(key_frame, width=30)
        key_frame.pack(side=tk.TOP, fill=tk.X, padx=3, pady=3)
        key_label.pack(side=tk.LEFT)
        key_entry.pack(side=tk.RIGHT, fill=tk.X, expand=tk.YES)

        value_frame = tk.Frame(retrieve_window)
        value_label = tk.Label(value_frame, width=10, text=VALUE_LABEL,
                               anchor='w')
        value_string = tk.StringVar()
        value_entry = tk.Entry(value_frame, width=30, fg='black', state=tk.DISABLED, textvariable=value_string)
        value_frame.pack(side=tk.TOP, fill=tk.X, padx=3, pady=3)
        value_label.pack(side=tk.LEFT)
        value_entry.pack(side=tk.RIGHT, fill=tk.X, expand=tk.YES)

        info_label = tk.Label(retrieve_window)
        info_label.pack(fill=tk.X, expand=tk.YES)

        def retrieve_command(transaction_id, key):
            # Reset entries highlight.
            transaction_entry.config(highlightbackground="grey")
            key_entry.config(highlightbackground="grey")

            # Highlight empty entries.
            if transaction_id == EMPTY_ENTRY or key == EMPTY_ENTRY:
                if transaction_id == EMPTY_ENTRY:
                    transaction_entry.config(highlightbackground="red")
                if key == EMPTY_ENTRY:
                    key_entry.config(highlightbackground="red")

                info_label.config(text=EMPTY_ENTRY_ERROR, fg='red')
                self.__status_change(RETRIEVE_FAILURE_MSG, True)
                return

            if transaction_id not in self.__transactions.keys():
                info_label.config(text=INVALID_NAME_ERROR, fg='red')
                tkinter.messagebox.showerror(ERROR_TITLE, INVALID_NAME_ERROR)
                self.__status_change(RETRIEVE_FAILURE_MSG, True)
                return

            real_key, real_value = self.__transactions[transaction_id]
            if key != real_key:
                info_label.config(text=INVALID_KEY_ERROR, fg='red')
                self.__status_change(RETRIEVE_FAILURE_MSG, True)
            else:
                value_string.set(real_value)
                self.__status_change(RETRIEVE_SUCCESS_MSG)

        button_frame = tk.Frame(retrieve_window)
        store_button = tk.Button(button_frame, text='Retrieve',
                                 command=lambda: retrieve_command(transaction_entry.get(),
                                                                  key_entry.get()))
        cancel_button = tk.Button(button_frame, text='Cancel',
                                  command=retrieve_window.destroy)
        button_frame.pack(side=tk.TOP, fill=tk.X, padx=3, pady=3)
        store_button.pack()
        cancel_button.pack()

        print(self.__transactions)

    @staticmethod
    def __help():
        """ Opens help window with information to the user. """
        info_window = tk.Toplevel()
        info_window.resizable(width=False, height=False)
        info_window.title("Help")
        info_image = tk.PhotoImage(file="Help.png")
        info_msg = tk.Label(info_window, image=info_image)
        info_msg.image = info_image  # Required for displaying the image.
        info_msg.pack()

    @staticmethod
    def __about():
        """ Opens about window with information about the application. """
        about_window = tk.Toplevel()
        about_window.resizable(width=False, height=False)
        about_window.title("About")
        about_image = tk.PhotoImage(file="About.png")
        info_msg = tk.Label(about_window, image=about_image)
        info_msg.image = about_image  # Required for displaying the image.
        info_msg.pack()


if __name__ == '__main__':
    root = tk.Tk()
    client = ClientGUI(root)
