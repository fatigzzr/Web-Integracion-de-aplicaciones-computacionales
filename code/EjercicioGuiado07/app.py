import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
import json
import threading
import time
from datetime import datetime
import os
import pickle

class MicroserviceClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Microservice JWT Client")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2b2b2b')
        
        # Configure ttk styles for dark mode
        self.configure_dark_theme()
        
        # Configuration storage
        self.config_file = "microservice_config.pkl"
        self.load_config()
        
        # JWT tokens
        self.access_token = None
        self.refresh_token = None
        self.current_user = None
        
        # Create GUI
        self.create_widgets()
        
        # Start health check thread
        self.start_health_monitor()
        
        # Bind mouse wheel to canvas
        self.bind_mousewheel()
        
        # Bind additional Mac trackpad gestures
        self.bind_mac_gestures()
    
    def configure_dark_theme(self):
        """Configure ttk styles for dark mode"""
        style = ttk.Style()
        
        # Configure LabelFrame style
        style.configure('TLabelframe', background='#2b2b2b', foreground='white')
        style.configure('TLabelframe.Label', background='#2b2b2b', foreground='white')
        
        # Configure Entry style
        style.configure('TEntry', fieldbackground='#404040', foreground='white', 
                       bordercolor='#666666', lightcolor='#666666', darkcolor='#666666')
        
        # Configure Label style
        style.configure('TLabel', background='#2b2b2b', foreground='white')
        
        # Configure ScrolledText style
        style.configure('TScrolledText', background='#404040', foreground='white')
    
    def bind_mousewheel(self):
        """Bind mouse wheel to canvas for scrolling - Mac compatible"""
        def _on_mousewheel(event):
            # Handle both Windows and Mac scroll events
            if event.delta:
                # Windows
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            else:
                # Mac
                if event.num == 4:
                    self.canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.canvas.yview_scroll(1, "units")
        
        def _bind_to_mousewheel(event):
            # Bind both MouseWheel and Button-4/5 for Mac compatibility
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
            self.canvas.bind_all("<Button-4>", _on_mousewheel)
            self.canvas.bind_all("<Button-5>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
        
        self.canvas.bind('<Enter>', _bind_to_mousewheel)
        self.canvas.bind('<Leave>', _unbind_from_mousewheel)
    
    def bind_mac_gestures(self):
        """Bind Mac trackpad gestures for scrolling"""
        def _on_trackpad_scroll(event):
            # Handle Mac trackpad scroll events
            if hasattr(event, 'delta'):
                if event.delta > 0:
                    self.canvas.yview_scroll(-1, "units")
                else:
                    self.canvas.yview_scroll(1, "units")
        
        # Bind trackpad scroll events
        self.canvas.bind("<MouseWheel>", _on_trackpad_scroll)
        
        # Also bind to the scrollable frame for better coverage
        self.scrollable_frame.bind("<MouseWheel>", _on_trackpad_scroll)
    
    def do_refresh_token(self):
        """NEW refresh token method"""
        self.log_message("=== DO REFRESH TOKEN CALLED ===")
        
        if not self.refresh_token:
            self.log_message("No refresh token available")
            messagebox.showerror("Error", "No refresh token available")
            return
        
        self.log_message("Making refresh request...")
        
        try:
            data = {'refresh_token': self.refresh_token}
            url = f"{self.base_url}/api/auth/refresh"
            self.log_message(f"URL: {url}")
            self.log_message(f"Data: {data}")
            
            response = requests.post(url, json=data, timeout=10)
            
            self.log_message(f"Response: {response.status_code}")
            self.log_message(f"Response text: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get('access_token')
                self.token_text.delete(1.0, tk.END)
                self.token_text.insert(1.0, self.access_token)
                self.log_message("SUCCESS: Token refreshed!")
                messagebox.showinfo("Success", "Token refreshed!")
            else:
                self.log_message(f"ERROR: {response.status_code}")
                messagebox.showerror("Error", f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_message(f"EXCEPTION: {e}")
            messagebox.showerror("Error", str(e))
    
    def load_config(self):
        """Load configuration from local storage"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'rb') as f:
                    config = pickle.load(f)
                    self.base_url = config.get('base_url', 'http://34.42.91.86:5003')
                    self.ip = config.get('ip', '34.42.91.86')
                    self.port = config.get('port', '5003')
            else:
                self.base_url = 'http://34.42.91.86:5003'
                self.ip = '34.42.91.86'
                self.port = '5003'
        except:
            self.base_url = 'http://34.42.91.86:5003'
            self.ip = '34.42.91.86'
            self.port = '5003'
    
    def save_config(self):
        """Save configuration to local storage"""
        try:
            config = {
                'base_url': self.base_url,
                'ip': self.ip,
                'port': self.port
            }
            with open(self.config_file, 'wb') as f:
                pickle.dump(config, f)
        except Exception as e:
            self.log_message(f"Error saving config: {e}")
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Create main canvas and scrollbar
        self.canvas = tk.Canvas(self.root, bg='#2b2b2b')
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Main container
        main_frame = ttk.Frame(self.scrollable_frame, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Update canvas scroll region when window is resized
        def configure_scroll_region(event=None):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        self.scrollable_frame.bind("<Configure>", configure_scroll_region)
        
        # Title
        title_label = tk.Label(main_frame, text="Microservice JWT Client", 
                              font=('Arial', 16, 'bold'), bg='#2b2b2b', fg='white')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Health Status Indicator
        self.create_health_section(main_frame, row=1)
        
        # Settings Section
        self.create_settings_section(main_frame, row=2)
        
        # Authentication Section
        self.create_auth_section(main_frame, row=3)
        
        # Registration Section
        self.create_register_section(main_frame, row=4)
        
        # Token Refresh Section
        self.create_refresh_section(main_frame, row=5)
        
        # Protected Endpoints Section
        self.create_protected_section(main_frame, row=6)
        
        # Log Display
        self.create_log_section(main_frame, row=7)
    
    def create_health_section(self, parent, row):
        """Create health status indicator"""
        health_frame = ttk.LabelFrame(parent, text="Health Status", padding="10")
        health_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.health_label = tk.Label(health_frame, text="Checking...", 
                                   font=('Arial', 12, 'bold'), bg='orange', fg='white')
        self.health_label.grid(row=0, column=0, padx=10)
        
        self.health_status = tk.Label(health_frame, text="Status: Unknown", 
                                    font=('Arial', 10), bg='#2b2b2b', fg='white')
        self.health_status.grid(row=0, column=1, padx=10)
    
    def create_settings_section(self, parent, row):
        """Create settings section for IP, port, and endpoints"""
        settings_frame = ttk.LabelFrame(parent, text="Microservice Settings", padding="10")
        settings_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # IP and Port
        ttk.Label(settings_frame, text="IP:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.ip_var = tk.StringVar(value=self.ip)
        ip_entry = ttk.Entry(settings_frame, textvariable=self.ip_var, width=15)
        ip_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(settings_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.port_var = tk.StringVar(value=self.port)
        port_entry = ttk.Entry(settings_frame, textvariable=self.port_var, width=10)
        port_entry.grid(row=0, column=3, padx=5)
        
        # Update button
        update_btn = tk.Button(settings_frame, text="Update Settings", 
                            command=self.update_settings, bg='white', fg='black',
                            activebackground='#f0f0f0', activeforeground='black',
                            relief='raised', bd=2)
        update_btn.grid(row=0, column=4, padx=10)
        
        # Current URL display
        self.url_label = tk.Label(settings_frame, text=f"Current URL: {self.base_url}", 
                                font=('Arial', 10), bg='#2b2b2b', fg='white')
        self.url_label.grid(row=1, column=0, columnspan=5, pady=5)
    
    def create_auth_section(self, parent, row):
        """Create login section"""
        auth_frame = ttk.LabelFrame(parent, text="Login", padding="10")
        auth_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Username
        ttk.Label(auth_frame, text="Username/Email:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(auth_frame, textvariable=self.username_var, width=30)
        username_entry.grid(row=0, column=1, padx=5)
        
        # Password
        ttk.Label(auth_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(auth_frame, textvariable=self.password_var, show="*", width=30)
        password_entry.grid(row=1, column=1, padx=5)
        
        # Login button
        login_btn = tk.Button(auth_frame, text="Login", command=self.login, 
                            bg='white', fg='black', width=15,
                            activebackground='#f0f0f0', activeforeground='black',
                            relief='raised', bd=2)
        login_btn.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Current user display
        self.user_label = tk.Label(auth_frame, text="Not logged in", 
                                 font=('Arial', 10), bg='#2b2b2b', fg='white')
        self.user_label.grid(row=3, column=0, columnspan=2, pady=5)
    
    def create_register_section(self, parent, row):
        """Create registration section"""
        register_frame = ttk.LabelFrame(parent, text="Register New User", padding="10")
        register_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Registration fields
        ttk.Label(register_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.reg_username_var = tk.StringVar()
        ttk.Entry(register_frame, textvariable=self.reg_username_var, width=25).grid(row=0, column=1, padx=5)
        
        ttk.Label(register_frame, text="Email:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.reg_email_var = tk.StringVar()
        ttk.Entry(register_frame, textvariable=self.reg_email_var, width=25).grid(row=0, column=3, padx=5)
        
        ttk.Label(register_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.reg_password_var = tk.StringVar()
        ttk.Entry(register_frame, textvariable=self.reg_password_var, show="*", width=25).grid(row=1, column=1, padx=5)
        
        # Register button
        register_btn = tk.Button(register_frame, text="Register", command=self.register, 
                               bg='white', fg='black', width=15,
                               activebackground='#f0f0f0', activeforeground='black',
                               relief='raised', bd=2)
        register_btn.grid(row=2, column=0, columnspan=4, pady=10)
    
    def create_refresh_section(self, parent, row):
        """Create token refresh section"""
        refresh_frame = ttk.LabelFrame(parent, text="Token Management", padding="10")
        refresh_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Refresh button - NEW METHOD
        refresh_btn = tk.Button(refresh_frame, text="Refresh Token", command=self.do_refresh_token, 
                              bg='white', fg='black', width=15,
                              activebackground='#f0f0f0', activeforeground='black',
                              relief='raised', bd=2)
        refresh_btn.grid(row=0, column=0, padx=5)
        
        
        # Logout button
        logout_btn = tk.Button(refresh_frame, text="Logout", command=self.logout, 
                             bg='white', fg='black', width=15,
                             activebackground='#f0f0f0', activeforeground='black',
                             relief='raised', bd=2)
        logout_btn.grid(row=0, column=1, padx=5)
        
        # JWT Token display
        ttk.Label(refresh_frame, text="Access Token:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.token_text = scrolledtext.ScrolledText(refresh_frame, height=3, width=80, 
                                                  bg='#404040', fg='white', 
                                                  insertbackground='white')
        self.token_text.grid(row=2, column=0, columnspan=2, pady=5)
    
    def create_protected_section(self, parent, row):
        """Create protected endpoints section"""
        protected_frame = ttk.LabelFrame(parent, text="Protected Endpoints", padding="10")
        protected_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Profile button
        profile_btn = tk.Button(protected_frame, text="Get Profile", command=self.get_profile, 
                              bg='white', fg='black', width=15,
                              activebackground='#f0f0f0', activeforeground='black',
                              relief='raised', bd=2)
        profile_btn.grid(row=0, column=0, padx=5)
        
        # Items button
        items_btn = tk.Button(protected_frame, text="Get Items", command=self.get_items, 
                            bg='white', fg='black', width=15,
                            activebackground='#f0f0f0', activeforeground='black',
                            relief='raised', bd=2)
        items_btn.grid(row=0, column=1, padx=5)
        
        # Create item button
        create_item_btn = tk.Button(protected_frame, text="Create Item", command=self.create_item_dialog, 
                                  bg='white', fg='black', width=15,
                                  activebackground='#f0f0f0', activeforeground='black',
                                  relief='raised', bd=2)
        create_item_btn.grid(row=0, column=2, padx=5)
        
        # Response display
        self.response_text = scrolledtext.ScrolledText(protected_frame, height=6, width=80,
                                                     bg='#404040', fg='white',
                                                     insertbackground='white')
        self.response_text.grid(row=1, column=0, columnspan=3, pady=10)
    
    def create_log_section(self, parent, row):
        """Create log display section"""
        log_frame = ttk.LabelFrame(parent, text="Request/Response Log", padding="10")
        log_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=100,
                                                bg='#404040', fg='white',
                                                insertbackground='white')
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for scrolling
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        parent.rowconfigure(row, weight=1)
    
    def log_message(self, message):
        """Add message to log display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def update_settings(self):
        """Update microservice settings"""
        self.ip = self.ip_var.get()
        self.port = self.port_var.get()
        self.base_url = f"http://{self.ip}:{self.port}"
        self.url_label.config(text=f"Current URL: {self.base_url}")
        self.save_config()
        self.log_message(f"Settings updated: {self.base_url}")
    
    def start_health_monitor(self):
        """Start health monitoring in background thread"""
        def monitor():
            while True:
                self.check_health()
                time.sleep(5)  # Check every 5 seconds
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def check_health(self):
        """Check microservice health"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=3)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    self.health_label.config(text="ONLINE", bg='green')
                    self.health_status.config(text=f"Status: {data.get('status')} | DB: {data.get('db')}")
                else:
                    self.health_label.config(text="ERROR", bg='red')
                    self.health_status.config(text=f"Status: {data.get('status')}")
            else:
                self.health_label.config(text="ERROR", bg='red')
                self.health_status.config(text=f"HTTP {response.status_code}")
        except requests.exceptions.RequestException:
            self.health_label.config(text="OFFLINE", bg='red')
            self.health_status.config(text="Connection failed")
        except Exception as e:
            self.health_label.config(text="ERROR", bg='red')
            self.health_status.config(text=f"Error: {str(e)}")
    
    def login(self):
        """Login user"""
        username = self.username_var.get()
        password = self.password_var.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return
        
        try:
            data = {
                'username': username,
                'password': password
            }
            
            self.log_message(f"Login attempt: {username}")
            response = requests.post(f"{self.base_url}/api/auth/login", json=data)
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get('access_token')
                self.refresh_token = result.get('refresh_token')
                
                self.log_message(f"Access token saved: {self.access_token[:50]}...")
                self.log_message(f"Refresh token saved: {self.refresh_token[:50]}...")
                
                self.user_label.config(text=f"Logged in as: {username}")
                self.token_text.delete(1.0, tk.END)
                self.token_text.insert(1.0, self.access_token)
                
                self.log_message(f"Login successful: {result}")
                messagebox.showinfo("Success", "Login successful!")
            else:
                error_msg = response.json().get('msg', 'Login failed')
                self.log_message(f"Login failed: {error_msg}")
                messagebox.showerror("Error", error_msg)
                
        except Exception as e:
            self.log_message(f"Login error: {str(e)}")
            messagebox.showerror("Error", f"Login error: {str(e)}")
    
    def register(self):
        """Register new user"""
        username = self.reg_username_var.get()
        email = self.reg_email_var.get()
        password = self.reg_password_var.get()
        
        if not all([username, email, password]):
            messagebox.showerror("Error", "Please fill all fields")
            return
        
        try:
            data = {
                'username': username,
                'email': email,
                'password': password
            }
            
            self.log_message(f"Registration attempt: {username}")
            response = requests.post(f"{self.base_url}/api/auth/register", json=data)
            
            if response.status_code == 201:
                result = response.json()
                self.log_message(f"Registration successful: {result}")
                messagebox.showinfo("Success", "User registered successfully!")
                # Clear form
                self.reg_username_var.set("")
                self.reg_email_var.set("")
                self.reg_password_var.set("")
            else:
                error_msg = response.json().get('msg', 'Registration failed')
                self.log_message(f"Registration failed: {error_msg}")
                messagebox.showerror("Error", error_msg)
                
        except Exception as e:
            self.log_message(f"Registration error: {str(e)}")
            messagebox.showerror("Error", f"Registration error: {str(e)}")
    
    def refresh_token(self):
        """Refresh access token - NEW VERSION"""
        self.log_message("=== REFRESH TOKEN METHOD CALLED ===")
        
        if not self.refresh_token:
            self.log_message("ERROR: No refresh token available")
            messagebox.showerror("Error", "No refresh token available")
            return
        
        self.log_message(f"Refresh token exists: {self.refresh_token[:50]}...")
        
        try:
            data = {'refresh_token': self.refresh_token}
            url = f"{self.base_url}/api/auth/refresh"
            self.log_message(f"Making request to: {url}")
            
            response = requests.post(url, json=data, timeout=10)
            self.log_message(f"Response received: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get('access_token')
                self.token_text.delete(1.0, tk.END)
                self.token_text.insert(1.0, self.access_token)
                self.log_message("Token refreshed successfully!")
                messagebox.showinfo("Success", "Token refreshed successfully!")
            else:
                self.log_message(f"Error: HTTP {response.status_code}")
                messagebox.showerror("Error", f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_message(f"Exception: {str(e)}")
            messagebox.showerror("Error", str(e))
    
    def logout(self):
        """Logout user"""
        if not self.refresh_token:
            messagebox.showerror("Error", "No refresh token available")
            return
        
        try:
            data = {'refresh_token': self.refresh_token}
            self.log_message("Logging out...")
            response = requests.post(f"{self.base_url}/api/auth/logout", json=data)
            
            if response.status_code == 200:
                self.access_token = None
                self.refresh_token = None
                self.current_user = None
                
                self.user_label.config(text="Not logged in")
                self.token_text.delete(1.0, tk.END)
                self.response_text.delete(1.0, tk.END)
                
                self.log_message("Logout successful")
                messagebox.showinfo("Success", "Logged out successfully!")
            else:
                error_msg = response.json().get('msg', 'Logout failed')
                self.log_message(f"Logout failed: {error_msg}")
                messagebox.showerror("Error", error_msg)
                
        except Exception as e:
            self.log_message(f"Logout error: {str(e)}")
            messagebox.showerror("Error", f"Logout error: {str(e)}")
    
    def get_profile(self):
        """Get user profile"""
        if not self.access_token:
            messagebox.showerror("Error", "Please login first")
            return
        
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            self.log_message("Getting profile...")
            response = requests.get(f"{self.base_url}/api/profile", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                self.response_text.delete(1.0, tk.END)
                self.response_text.insert(1.0, json.dumps(result, indent=2))
                self.log_message(f"Profile retrieved: {result}")
            else:
                error_msg = response.json().get('msg', 'Failed to get profile')
                self.log_message(f"Profile request failed: {error_msg}")
                messagebox.showerror("Error", error_msg)
                
        except Exception as e:
            self.log_message(f"Profile request error: {str(e)}")
            messagebox.showerror("Error", f"Profile request error: {str(e)}")
    
    def get_items(self):
        """Get user items"""
        if not self.access_token:
            messagebox.showerror("Error", "Please login first")
            return
        
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            self.log_message("Getting items...")
            response = requests.get(f"{self.base_url}/api/items", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                self.response_text.delete(1.0, tk.END)
                self.response_text.insert(1.0, json.dumps(result, indent=2))
                self.log_message(f"Items retrieved: {result}")
            else:
                error_msg = response.json().get('msg', 'Failed to get items')
                self.log_message(f"Items request failed: {error_msg}")
                messagebox.showerror("Error", error_msg)
                
        except Exception as e:
            self.log_message(f"Items request error: {str(e)}")
            messagebox.showerror("Error", f"Items request error: {str(e)}")
    
    def create_item_dialog(self):
        """Create item dialog"""
        if not self.access_token:
            messagebox.showerror("Error", "Please login first")
            return
        
        # Create dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("Create Item")
        dialog.geometry("400x200")
        dialog.configure(bg='#2b2b2b')
        
        # Title field
        ttk.Label(dialog, text="Title:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        title_var = tk.StringVar()
        title_entry = ttk.Entry(dialog, textvariable=title_var, width=40)
        title_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # Description field
        ttk.Label(dialog, text="Description:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        desc_var = tk.StringVar()
        desc_entry = ttk.Entry(dialog, textvariable=desc_var, width=40)
        desc_entry.grid(row=1, column=1, padx=10, pady=5)
        
        # Buttons
        def create_item():
            title = title_var.get()
            description = desc_var.get()
            
            if not title:
                messagebox.showerror("Error", "Title is required")
                return
            
            try:
                data = {
                    'title': title,
                    'description': description
                }
                
                headers = {'Authorization': f'Bearer {self.access_token}'}
                self.log_message(f"Creating item: {title}")
                response = requests.post(f"{self.base_url}/api/items", json=data, headers=headers)
                
                if response.status_code == 201:
                    result = response.json()
                    self.response_text.delete(1.0, tk.END)
                    self.response_text.insert(1.0, json.dumps(result, indent=2))
                    self.log_message(f"Item created: {result}")
                    messagebox.showinfo("Success", "Item created successfully!")
                    dialog.destroy()
                else:
                    error_msg = response.json().get('msg', 'Failed to create item')
                    self.log_message(f"Item creation failed: {error_msg}")
                    messagebox.showerror("Error", error_msg)
                    
            except Exception as e:
                self.log_message(f"Item creation error: {str(e)}")
                messagebox.showerror("Error", f"Item creation error: {str(e)}")
        
        tk.Button(dialog, text="Create", command=create_item, 
                 bg='white', fg='black',
                 activebackground='#f0f0f0', activeforeground='black',
                 relief='raised', bd=2).grid(row=2, column=0, padx=10, pady=10)
        tk.Button(dialog, text="Cancel", command=dialog.destroy, 
                 bg='white', fg='black',
                 activebackground='#f0f0f0', activeforeground='black',
                 relief='raised', bd=2).grid(row=2, column=1, padx=10, pady=10)

def main():
    root = tk.Tk()
    app = MicroserviceClient(root)
    root.mainloop()

if __name__ == "__main__":
    main()
