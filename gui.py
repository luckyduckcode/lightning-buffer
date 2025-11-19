import customtkinter as ctk
import threading
import os
import sys
import uvicorn
import logging
from dotenv import load_dotenv, set_key
import main  # Import the FastAPI app

# Configure appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class TextRedirector(object):
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, str):
        self.widget.configure(state="normal")
        self.widget.insert("end", str, (self.tag,))
        self.widget.see("end")
        self.widget.configure(state="disabled")

    def flush(self):
        pass

class BufferServerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Lightning Buffer")
        self.geometry("900x700")
        
        self.server_thread = None
        self.server = None
        self.env_file = ".env"
        
        # Grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) # Header
        self.grid_rowconfigure(1, weight=0) # Config
        self.grid_rowconfigure(2, weight=0) # Controls
        self.grid_rowconfigure(3, weight=1) # Logs

        self.create_widgets()
        self.load_config()
        
        # Redirect stdout/stderr
        sys.stdout = TextRedirector(self.log_box, "stdout")
        sys.stderr = TextRedirector(self.log_box, "stderr")

    def create_widgets(self):
        # --- Header ---
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        self.status_label = ctk.CTkLabel(
            self.header_frame, 
            text="Server Status: STOPPED", 
            font=("Roboto", 20, "bold"),
            text_color="red"
        )
        self.status_label.pack(pady=10)

        # --- Configuration ---
        self.config_frame = ctk.CTkFrame(self)
        self.config_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.config_frame.grid_columnconfigure(1, weight=1)

        # API Key 1
        ctk.CTkLabel(self.config_frame, text="Automation API Key:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.entry_auto_key = ctk.CTkEntry(self.config_frame, placeholder_text="Key from Automation Repo")
        self.entry_auto_key.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # API Key 2
        ctk.CTkLabel(self.config_frame, text="Buffer API Key:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.entry_buffer_key = ctk.CTkEntry(self.config_frame, placeholder_text="Optional key for Bot to use")
        self.entry_buffer_key.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        # Host Dir
        ctk.CTkLabel(self.config_frame, text="Automations Dir:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.entry_host_dir = ctk.CTkEntry(self.config_frame, placeholder_text=r"D:\AI-Automations")
        self.entry_host_dir.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        self.btn_save_config = ctk.CTkButton(self.config_frame, text="Save Configuration", command=self.save_config, fg_color="green")
        self.btn_save_config.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

        # --- Controls ---
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_start = ctk.CTkButton(self.controls_frame, text="Start Server", command=self.start_server, width=150, height=40)
        self.btn_start.pack(side="left", padx=20, pady=20, expand=True)
        
        self.btn_restart = ctk.CTkButton(self.controls_frame, text="Restart", command=self.restart_server, width=150, height=40, state="disabled")
        self.btn_restart.pack(side="left", padx=20, pady=20, expand=True)

        self.btn_stop = ctk.CTkButton(self.controls_frame, text="Stop Server", command=self.stop_server, width=150, height=40, fg_color="darkred", state="disabled")
        self.btn_stop.pack(side="left", padx=20, pady=20, expand=True)

        # --- Logs ---
        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.grid(row=3, column=0, padx=20, pady=(10, 20), sticky="nsew")
        
        self.log_box = ctk.CTkTextbox(self.log_frame, font=("Consolas", 12), state="disabled")
        self.log_box.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Colors for logs
        self.log_box.tag_config("stdout", foreground="white")
        self.log_box.tag_config("stderr", foreground="orange")

    def load_config(self):
        load_dotenv(self.env_file)
        self.entry_auto_key.insert(0, os.getenv("AUTOMATION_API_KEY", ""))
        self.entry_buffer_key.insert(0, os.getenv("BUFFER_API_KEY", ""))
        self.entry_host_dir.insert(0, os.getenv("AUTOMATIONS_HOST_DIR", ""))

    def save_config(self):
        # Update .env file
        set_key(self.env_file, "AUTOMATION_API_KEY", self.entry_auto_key.get())
        set_key(self.env_file, "BUFFER_API_KEY", self.entry_buffer_key.get())
        set_key(self.env_file, "AUTOMATIONS_HOST_DIR", self.entry_host_dir.get())
        print("Configuration saved to .env")

    def run_uvicorn(self):
        config = uvicorn.Config(app=main.app, host="0.0.0.0", port=8000, log_level="info")
        self.server = uvicorn.Server(config)
        self.server.run()

    def start_server(self):
        if self.server_thread and self.server_thread.is_alive():
            return

        print("Starting server...")
        self.server_thread = threading.Thread(target=self.run_uvicorn, daemon=True)
        self.server_thread.start()
        
        self.update_ui_state(running=True)

    def stop_server(self):
        if self.server:
            print("Stopping server...")
            self.server.should_exit = True
            self.update_ui_state(running=False)
            # We don't join the thread here to keep UI responsive, it will die eventually
            self.server = None

    def restart_server(self):
        self.stop_server()
        # Wait a bit for cleanup (simple approach)
        self.after(2000, self.start_server)

    def update_ui_state(self, running):
        if running:
            self.status_label.configure(text="Server Status: RUNNING", text_color="green")
            self.btn_start.configure(state="disabled")
            self.btn_restart.configure(state="normal")
            self.btn_stop.configure(state="normal")
        else:
            self.status_label.configure(text="Server Status: STOPPED", text_color="red")
            self.btn_start.configure(state="normal")
            self.btn_restart.configure(state="disabled")
            self.btn_stop.configure(state="disabled")

    def on_closing(self):
        if self.server:
            self.server.should_exit = True
        self.destroy()

if __name__ == "__main__":
    app = BufferServerGUI()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
