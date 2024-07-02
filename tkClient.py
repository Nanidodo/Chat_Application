import socket
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime

HOST = '127.0.0.1'
PORT = 12340

#'192.168.43.219'
#'192.168.43.245'

class Client:
    def __init__(self, root):
        self.root = root
        self.nickname = simpledialog.askstring("Nickname", "Choose your nickname:", parent=root)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((HOST, PORT))
        self.current_chat = "Broadcast"
        self.active_users = []
        self.private_chats = {}
        self.broadcast_messages = []

        self.create_gui()
        self.receive_thread = threading.Thread(target=self.receive)
        self.receive_thread.start()

    def create_gui(self):
        self.root.title("Chat Application")
        self.root.geometry("600x400")

        # Create frames
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=1)

        self.chat_frame = tk.Frame(self.main_frame, bd=5, relief=tk.SUNKEN)
        self.chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        self.users_frame = tk.Frame(self.main_frame, bd=5, relief=tk.SUNKEN)
        self.users_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Chat frame widgets
        self.chat_text = tk.Text(self.chat_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.chat_text.pack(fill=tk.BOTH, expand=1)

        self.message_entry = tk.Entry(self.chat_frame)
        self.message_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        self.message_entry.bind("<Return>", self.send_message)

        self.send_button = tk.Button(self.chat_frame, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT)

        # Users frame widgets
        self.users_label = tk.Label(self.users_frame, text="Active Users")
        self.users_label.pack()

        self.users_listbox = tk.Listbox(self.users_frame, selectmode=tk.SINGLE)
        self.users_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        self.users_listbox.bind("<Double-Button-1>", self.select_user_chat)

        self.scrollbar = tk.Scrollbar(self.users_frame, orient=tk.VERTICAL, command=self.users_listbox.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.users_listbox.config(yscrollcommand=self.scrollbar.set)

        # Buttons for switching message view
        self.view_frame = tk.Frame(self.root)
        self.view_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.users_button = tk.Button(self.view_frame, text="Users", command=self.show_user_messages)
        self.users_button.pack(side=tk.LEFT)

        self.broadcasts_button = tk.Button(self.view_frame, text="Broadcasts", command=self.show_broadcast_messages)
        self.broadcasts_button.pack(side=tk.LEFT)

        self.username_label = tk.Label(self.view_frame, text=f"Logged in as: {self.nickname}")
        self.username_label.pack(side=tk.RIGHT)

    def receive(self):
        while True:
            try:
                message = self.client.recv(1024).decode('utf-8')
                if message.startswith('NICK'):
                    self.client.send(self.nickname.encode('utf-8'))
                elif message.startswith('USERLIST'):
                    self.update_user_list(message)
                else:
                    self.store_message(message)
                    print('Huh1')
                    self.display_message(message)
            except Exception as e:
                messagebox.showerror("Error", "An error occurred!")
                self.client.close()
                break

    def update_user_list(self, message):
        user_list = message.split()[1:]
        self.active_users = user_list
        self.users_listbox.delete(0, tk.END)
        for user in self.active_users:
            self.users_listbox.insert(tk.END, user)

    def store_message(self, message):
        l = len(message)
        if message.startswith('BROADCAST'):
            self.broadcast_messages.append(message)
        elif message.startswith('PRIVATE'):
            parts = message.split()
            sender = parts[1]
            recipient = parts[2]
            print(message)
            print(sender)
            print(recipient)
            if sender == self.nickname or recipient == self.nickname:
                chat_partner = sender if recipient == self.nickname else recipient
                if chat_partner not in self.private_chats:
                    self.private_chats[chat_partner] = []
                self.private_chats[chat_partner].append(message)

    def display_message(self, message):
        if self.current_chat == "Broadcast" and message.startswith('BROADCAST'):
            self.chat_text.config(state=tk.NORMAL)
            self.chat_text.insert(tk.END, message + '\n')
            self.chat_text.config(state=tk.DISABLED)
            self.chat_text.see(tk.END)
        elif self.current_chat in self.private_chats and (message.startswith(f'PRIVATE {self.current_chat}') or message.startswith(f'PRIVATE {self.nickname}')):
            self.chat_text.config(state=tk.NORMAL)
            self.chat_text.insert(tk.END, message + '\n')
            self.chat_text.config(state=tk.DISABLED)
            self.chat_text.see(tk.END)

    def send_message(self, event=None):
        message = self.message_entry.get()
        if message:
            # timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if self.current_chat == "Broadcast":
                formatted_message = f"BROADCAST {self.nickname}: {message}"
                self.client.send(formatted_message.encode('utf-8'))
                self.store_message(formatted_message)  # Store and display the user's own broadcast messages
                print('Huh2')
                self.display_message(formatted_message)
            elif self.current_chat in self.active_users:
                formatted_message = f"PRIVATE {self.nickname} {self.current_chat} {message}"
                self.client.send(formatted_message.encode('utf-8'))
                # print(formatted_message)
                self.store_message(formatted_message)  # Store and display the user's own private messages
                print('Huh3')
                self.display_message(formatted_message)
            self.message_entry.delete(0, tk.END)

    def select_user_chat(self, event=None):
        selected_indices = self.users_listbox.curselection()
        if selected_indices:
            self.current_chat = self.active_users[selected_indices[0]]
            self.chat_text.config(state=tk.NORMAL)
            self.chat_text.delete(1.0, tk.END)
            if self.current_chat in self.private_chats:
                for message in self.private_chats[self.current_chat]:
                    self.chat_text.insert(tk.END, message + '\n')
            self.chat_text.config(state=tk.DISABLED)
            self.chat_text.see(tk.END)

    def show_user_messages(self):
        selected_indices = self.users_listbox.curselection()
        if selected_indices:
            self.current_chat = self.active_users[selected_indices[0]]
            self.chat_text.config(state=tk.NORMAL)
            self.chat_text.delete(1.0, tk.END)
            if self.current_chat in self.private_chats:
                for message in self.private_chats[self.current_chat]:
                    self.chat_text.insert(tk.END, message + '\n')
            self.chat_text.config(state=tk.DISABLED)
            self.chat_text.see(tk.END)

    def show_broadcast_messages(self):
        self.current_chat = "Broadcast"
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete(1.0, tk.END)
        for message in self.broadcast_messages:
            self.chat_text.insert(tk.END, message + '\n')
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)

root = tk.Tk()
client = Client(root)
root.mainloop()
