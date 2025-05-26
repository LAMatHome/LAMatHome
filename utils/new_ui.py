import json
import os
import sys
import platform
import ctypes
import Xlib.display
import customtkinter
import logging
import threading
import _tkinter
import tkinter
from tkinter import PhotoImage
from PIL import Image, ImageTk
from contacts import contacts
from dotenv import set_key, dotenv_values
from customtkinter import CTkImage
from utils import splash_screen
from main import main

PRIMARY_COLOR = "#ff4d06"
CONFIG_FILE = "config.json"
CREDENTIALS_FILE = ".env"
CONTACTS_FILE = 'contacts.py'
ui_instance = None
ui_window = None
main_thread = None
stop_event = threading.Event()
x_offset = 0
y_offset = 0
# --- Config File Handling ---
def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return False

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
# --- Credentials File Handling ---
def load_env():
    try:
        return dotenv_values(CREDENTIALS_FILE)
    except FileNotFoundError:
        return False

def load_credentials():
    if not os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "w") as f:
            f.write("")  # Create an empty .env file if it doesn't exist
    return load_env()

def save_credentials(credentials):
    if not os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "w") as f:
            f.write("")  # Create an empty .env file if it doesn't exist
    for key, value in credentials.items():
        set_key(dotenv_path=CREDENTIALS_FILE, key_to_set=key, value_to_set=value)

def save_contacts(contacts):
    try:
        with open(CONTACTS_FILE, 'w') as f:
            f.write(f"contacts = {json.dumps(contacts, indent=4)}")
        print(f"Contacts saved to {CONTACTS_FILE}")
    except OSError as e:
        print(f"Error creating directory: {e}")
# --- Load Initial Data ---
config = load_config()
credentials = load_credentials()
# --- UI Functions ---
def update_config(key, value):
    config[key] = value
    save_config(config)

def update_credentials(key, value):
    credentials[key] = value
    save_credentials(credentials) 
# --- Tooltip Class ---
class ToolTip:
    current_tooltip = None  # Class variable to keep track of the current tooltip

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        # Hide the current tooltip if there is one
        if ToolTip.current_tooltip:
            ToolTip.current_tooltip.hide_tooltip(None)

        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip = customtkinter.CTkToplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = customtkinter.CTkLabel(self.tooltip, pady=10, padx=10, text=self.text, bg_color=PRIMARY_COLOR, text_color="black")
        label.pack()

        # Set this tooltip as the current tooltip
        ToolTip.current_tooltip = self

    def hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
            # Clear the current tooltip if it is this one
            if ToolTip.current_tooltip == self:
                ToolTip.current_tooltip = None

def create_integration_frame(parent_tab, title):
    frame = customtkinter.CTkFrame(master=parent_tab)
    frame.pack(pady=5, padx=10, fill="both", expand=True)
    label = customtkinter.CTkLabel(master=frame, text=title, font=("Power Grotesk", 22))
    label.pack(pady=2)
    return frame

def create_toggle(parent, key, text, tooltip_text=None):
    toggle = customtkinter.CTkSwitch(master=parent, text=text, command=lambda: update_config(key, toggle.get() == 1))
    toggle.pack(pady=2, anchor="w")
    if config.get(key, False):
        toggle.select()
    else:
        toggle.deselect()
    if tooltip_text:
        ToolTip(toggle, tooltip_text)

def create_mode_toggle(parent, key, text, tooltip_text=None):
    def toggle_mode():
        current_value = config.get(key, 'rabbit')
        new_value = 'cli' if current_value == 'rabbit' else 'rabbit'
        update_config(key, new_value)
        toggle.select() if new_value == 'rabbit' else toggle.deselect()

    toggle = customtkinter.CTkSwitch(master=parent, text=text, command=toggle_mode)
    toggle.pack(pady=2, anchor="w")
    if config.get(key, 'rabbit') == 'rabbit':
        toggle.select()
    else:
        toggle.deselect()
    if tooltip_text:
        ToolTip(toggle, tooltip_text)

def create_input(parent, key, placeholder, tooltip_text=None):
    entry = customtkinter.CTkEntry(master=parent, placeholder_text=placeholder)
    entry.pack(pady=2, fill="x")
    entry.insert(0, config.get(key, ""))  # Set initial value from config

    def update_entry(event=None):
        update_config(key, entry.get())

    entry.bind("<FocusOut>", update_entry)
    entry.bind("<Return>", update_entry)
    if tooltip_text:
        ToolTip(entry, tooltip_text)
        
def create_credential_input(parent, key, placeholder, tooltip_text=None):
    frame = customtkinter.CTkFrame(master=parent)
    frame.pack(pady=2, fill="x")

    entry = customtkinter.CTkEntry(master=frame, placeholder_text=placeholder, show="*")
    entry.pack(side="left", fill="x", expand=True)
    entry.insert(0, credentials.get(key, ""))  # Set initial value from credentials

    def update_entry(event=None):
        update_credentials(key, entry.get())

    entry.bind("<FocusOut>", update_entry)
    entry.bind("<Return>", update_entry)

    if tooltip_text:
        ToolTip(entry, tooltip_text)

    def toggle_visibility():
        if entry.cget("show") == "*":
            entry.configure(show="")
        else:
            entry.configure(show="*")

    visibility_toggle = customtkinter.CTkSwitch(master=frame, text="Show", command=toggle_visibility)
    visibility_toggle.pack(side="right")
    
def create_slider(parent, key, from_, to_, text, tooltip_text=None):
    label = customtkinter.CTkLabel(master=parent, text=text)
    label.pack(pady=(5, 0), anchor="w")

    def update_slider(value):
        # Convert the value to float with two decimal places
        formatted_value = float("{:.2f}".format(float(value)))
        update_config(key, formatted_value)
        label.configure(text=f"Current Value: {formatted_value}")

    # Ensure the value in config is correctly set as float
    initial_value = float(config.get(key, 0.1))
    
    slider = customtkinter.CTkSlider(master=parent, from_=from_, to=to_, command=update_slider)
    slider.pack(pady=2, fill="x")
    slider.set(initial_value)  # Set initial value from config

    if tooltip_text:
        ToolTip(slider, tooltip_text)

def create_integer_slider(parent, key, text, tooltip_text=None):
    label = customtkinter.CTkLabel(master=parent, text=text)
    label.pack(pady=(5, 0), anchor="w")

    def update_slider(value):
        update_config(key, int(value))
        label.configure(text=f"Current Value: {int(slider.get())}")

    slider = customtkinter.CTkSlider(master=parent, from_=1, to=30, command=update_slider)
    slider.pack(pady=2, fill="x")
    slider.set(config.get(key, 1))  # Set initial value from config
    if tooltip_text:
        ToolTip(slider, tooltip_text)

def get_screen_size():
    system = platform.system()
    if system == 'Windows':
        return get_screen_size_windows()
    elif system == 'Darwin':  # macOS
        return get_screen_size_macos()
    elif system == 'Linux':
        return get_screen_size_linux()
    else:
        return None, None  # Handle other platforms as needed

def get_screen_size_windows():
    user32 = ctypes.windll.user32
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

def get_screen_size_macos():
    from AppKit import NSScreen, NSRect
    main_screen = NSScreen.mainScreen().frame()
    return int(main_screen.size.width), int(main_screen.size.height)

def get_screen_size_linux():
    display = Xlib.display.Display()
    screen = display.screen()
    return screen.width_in_pixels, screen.height_in_pixels

def toggle_ui():
    global ui_window
    try:
        if ui_window is None or not ui_window.winfo_exists():
            ui_window = create_ui()
        else:
            if ui_window.state() == 'withdrawn':
                ui_window.deiconify()
            else:
                ui_window.withdraw()
    except _tkinter.TclError as e:
        ui_window = None

def start_drag(event):
    global x_offset, y_offset
    x_offset = event.x
    y_offset = event.y

def do_drag(event):
    try:
        x = root.winfo_pointerx() - x_offset
        y = root.winfo_pointery() - y_offset
        root.geometry(f"+{x}+{y}")
    except NameError:
        pass

def run_main_in_thread():
    global main_thread
    stop_event.clear()
    main_thread = threading.Thread(target=main)
    main_thread.start()

def stop_main_thread():
    stop_event.set()
    print(splash_screen.colored_splash_goodbye)
    os.kill(os.getpid(), 2)  # Send SIGINT signal to simulate Ctrl+C

# def get_python_command():
#     if sys.executable.endswith("python.exe"):
#         return "python"
#     elif sys.executable.endswith("python3"):
#         return "python3"
#     else:
#         return "py"

def restart_program():
    print(splash_screen.colored_splash_goodbye)
    root.destroy()
    os.execv(sys.executable, [sys.executable] + [os.path.join(os.getcwd(), "main.py")])
    
def popup():
    customtkinter.set_appearance_mode("dark")
    customtkinter.set_default_color_theme("utils/rabbit_color.json")
    global root
    root = customtkinter.CTk()
    root.title("LAMatHome")
    root.iconbitmap('assets/favicon.ico')
    global icon
    
    root.bind("<Button-1>", start_drag)
    root.bind("<B1-Motion>", do_drag)

    # Set the window background to be transparent
    root.attributes('-alpha', 0.97)

    # Load the image
    image_path = "assets/LAH_splash.png"
    try:
        image = Image.open(image_path)
    except FileNotFoundError:
        logging.error(f"Image not found at {image_path}")
        root.destroy()
        exit()

    # Get screen dimensions
    screen_width, screen_height = get_screen_size()

    # Calculate maximum allowed dimensions (20% of screen size)
    max_width = int(screen_width * 0.25)
    max_height = int(screen_height * 0.25)

    # Resize the image if it exceeds the maximum allowed dimensions
    image_width, image_height = image.size
    if image_width > max_width or image_height > max_height:
        scaling_factor = min(max_width / image_width, max_height / image_height)
        new_width = int((image_width * scaling_factor) * 1.2)
        new_height = int((image_height * scaling_factor) * 1.2)
        image = image.resize((new_width , new_height), Image.LANCZOS)
    else:
        new_width, new_height = image_width, image_height

    # Convert the image to a CTkImage
    ctk_image = CTkImage(light_image=image, dark_image=image, size=(new_width, new_height))

    # Create the button with the image and transparent background
    toggle_button = customtkinter.CTkButton(master=root, image=ctk_image, text="", command=toggle_ui, fg_color="#161B22", border_color="#ff4d06", border_width=1, hover_color="#ff4d06", corner_radius=8)
    toggle_button.pack(padx=15, pady=15)  # Adding padding to ensure button isn't touching the edges

    # Adjust the button size to match the image size
    toggle_button.configure(width=new_width, height=new_height)
    
    # Calculate the space required for buttons
    button_frame_height = 50  # Adjust this based on your button sizes and padding

    # Calculate the total height needed for the image and button frame
    total_height = new_height + button_frame_height + 40

    # Calculate the position to center the window
    x_position = (screen_width - new_width) // 2
    y_position = (screen_height - total_height) // 2
    
    root.geometry(f"{new_width}x{total_height}+{x_position}+{y_position}")

    # Frame to hold start/stop buttons with black background
    button_frame = customtkinter.CTkFrame(master=root)
    button_frame.pack(pady=10, padx=10)

    # Add a start button to the UI
    start_button = customtkinter.CTkButton(master=button_frame, text="Start", command=run_main_in_thread, fg_color="#161B22", border_color="#ff4d06", border_width=1, hover_color="#ff4d06", corner_radius=8, bg_color="#000000")
    start_button.pack(side="left", padx=(5, 5))

    # Add a stop button to the UI
    stop_button = customtkinter.CTkButton(master=button_frame, text="Stop", command=stop_main_thread, fg_color="#161B22", border_color="#ff4d06", border_width=1, hover_color="#ff4d06", corner_radius=8, bg_color="#000000")
    stop_button.pack(side="left", padx=(5, 5))

    # Add a restart button to the UI
    restart_button = customtkinter.CTkButton(master=button_frame, text="Restart", command=restart_program, fg_color="#161B22", border_color="#ff4d06", border_width=1, hover_color="#ff4d06", corner_radius=8, bg_color="#000000")
    restart_button.pack(side="left", padx=(5, 5))

    # Start the GUI event loop
    root.mainloop()
    main()
# --- UI Setup ---

def on_closing():
    global ui_instance
    ui_instance.destroy()
    ui_instance = None

        
def create_ui():
    global ui_instance
    if ui_instance is None or not ui_instance.winfo_exists():
        ui_instance = customtkinter.CTk()
        screen_width = ui_instance.winfo_screenwidth()
        screen_height = ui_instance.winfo_screenheight()
        
        min_width = int(screen_width * 0.6)
        min_height = int(screen_height * 0.6)
        
        ui_instance.minsize(width=min_width, height=min_height)
        ui_instance.state('normal')  
        ui_instance.title("LAMatHome")
        
        ui_instance.protocol("WM_DELETE_WINDOW", on_closing)

    # --- Style ---

        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("utils/rabbit_color.json")

        # --- Tabs ---
        tabview = customtkinter.CTkTabview(master=ui_instance)
        tabview.pack(pady=10, padx=10, fill="both", expand=True)
        tabview.add("Configuration")
        tabview.add("Credentials")
        tabview.add('Contacts')

        # --- Configuration Tab ---
        config_tab = tabview.tab("Configuration")

        # --- Scrollable Frame for Configuration Tab ---
        scrollable_frame = customtkinter.CTkScrollableFrame(master=config_tab)
        scrollable_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # --- Mode Toggle ---
        mode_frame = create_integration_frame(scrollable_frame, "Mode Selection")
        create_mode_toggle(mode_frame, "mode", "Rabbit Mode", "Toggle between Rabbit mode and CLI mode")
       
        
        lamathome_save_path_frame = create_integration_frame(scrollable_frame, "LAMatHome Save Path")
        save_path_entry = customtkinter.CTkEntry(master=lamathome_save_path_frame, placeholder_text="eg: ~/Pictures/LAMatHome")
        save_path_entry.pack(pady=2, padx=4, fill="x")
        save_path_entry.insert(0, config.get("lamathomesave_path", ""))
        ToolTip(save_path_entry, "This is the path to the folder that will store journal resources.")
        create_toggle(lamathome_save_path_frame, "lamathomesave_isenabled", "Enable Magic Cam AutoSave", "Enable or disable Autosave integration")
        
        def update_save_path(event=None):
            updated_path = save_path_entry.get()
            if updated_path.startswith("~/"):
                update_config("lamathomesave_path", updated_path)
            elif not updated_path.startswith("~/"):
                save_path_entry.insert(0, "~/")

        save_path_entry.bind("<FocusOut>", update_save_path)
        save_path_entry.bind("<Return>", update_save_path)




        # --- Google Integration ---
        google_frame = create_integration_frame(scrollable_frame, "Google Integration")
        create_toggle(google_frame, "google_isenabled", "Enable Google Integration", "Enable or disable Google integration")
        create_toggle(google_frame, "googlehome_isenabled", "Enable Google Home", "Enable or disable Google Home integration")
        create_input(google_frame, "googlehomeautomations", "Google Home Automations (comma-separated)", "Comma-separated list of Google Home automations")

        # --- LAMatHomee Integration ---
        lamathome_frame = create_integration_frame(scrollable_frame, "LAMatHome Integration")
        create_toggle(lamathome_frame, "lamathome_isenabled", "Enable LAMatHome", "Enable or disable LAMatHome integration")
        create_toggle(lamathome_frame, "lamathometerminate_isenabled", "Enable LAMatHome Termination", "Enable or disable LAMatHome termination")

        # --- Open Interpreter Integration ---
        openinterpreter_frame = create_integration_frame(scrollable_frame, "Open Interpreter Integration")
        create_toggle(openinterpreter_frame, "openinterpreter_isenabled", "Enable Open Interpreter", "Enable or disable Open Interpreter integration")
        create_toggle(openinterpreter_frame, "openinterpreter_auto_run_isenabled", "Enable Auto Run", "Enable or disable auto run for Open Interpreter")
        create_toggle(openinterpreter_frame, "openinterpreter_verbose_mode_isenabled", "Enable Verbose Mode", "Enable or disable verbose mode for Open Interpreter")
        create_input(openinterpreter_frame, "openinterpreter_llm_api_base", "LLM API Base", "Base URL for the LLM API")
        create_input(openinterpreter_frame, "openinterpreter_llm_model", "LLM Model", "Model name for the LLM")
        create_slider(openinterpreter_frame, "openinterpreter_llm_temperature", 0.1, 1.0, "LLM Temperature", "Temperature setting for the LLM")

        # --- Telegram Integration ---
        telegram_frame = create_integration_frame(scrollable_frame, "Telegram Integration")
        create_toggle(telegram_frame, "telegram_isenabled", "Enable Telegram", "Enable or disable Telegram integration")
        create_toggle(telegram_frame, "telegramtext_isenabled", "Enable Telegram Text", "Enable or disable Telegram text integration")

        # --- Credentials Tab ---
        credentials_tab = tabview.tab("Credentials")

        # --- Scrollable Frame for Credentials Tab ---
        scrollable_frame_credentials = customtkinter.CTkScrollableFrame(master=credentials_tab)
        scrollable_frame_credentials.pack(pady=10, padx=10, fill="both", expand=True)

        # --- Rabbithole Access Token ---
        rabbithole_frame = create_integration_frame(scrollable_frame_credentials, "Rabbithole Access Token")
        create_credential_input(rabbithole_frame, "RH_ACCESS_TOKEN", "Rabbithole Access Token", "Access token for Rabbithole journal")

        # --- API Keys ---
        api_frame = create_integration_frame(scrollable_frame_credentials, "API Keys")
        create_credential_input(api_frame, "GROQ_API_KEY", "Groq API Key", "API key for Groq")
        create_credential_input(api_frame, "OI_API_KEY", "Open Interpreter API Key", "API key for Open Interpreter")

        # --- Account Credentials ---
        account_frame = create_integration_frame(scrollable_frame_credentials, "Account Credentials")
        create_credential_input(account_frame, "DC_EMAIL", "Discord Email", "Email for Discord account")
        create_credential_input(account_frame, "DC_PASS", "Discord Password", "Password for Discord account")
        create_credential_input(account_frame, "FB_EMAIL", "Facebook Email", "Email for Facebook account")
        create_credential_input(account_frame, "FB_PASS", "Facebook Password", "Password for Facebook account")
        create_credential_input(account_frame, "G_HOME_EMAIL", "Google Home Email", "Email for Google Home account")
        create_credential_input(account_frame, "G_HOME_PASS", "Google Home Password", "Password for Google Home account")

        reminder_label = customtkinter.CTkLabel(master=scrollable_frame_credentials, text="Press Enter after inputing the last value to ensure you save it.")
        reminder_label.pack(pady=10, padx=11, anchor="w")
        
        tabview.add("Customization")

        # --- Customization Tab ---
        customization_tab = tabview.tab("Customization")
        create_integer_slider(customization_tab, "vol_up_step_value", "Volume Up Step Value", "Step value for volume increase")
        create_integer_slider(customization_tab, "vol_down_step_value", "Volume Down Step Value", "Step value for volume decrease")
        create_integer_slider(customization_tab, "rolling_transcript_size", "Rolling Transcript Size", "Number of entries in rolling transcript")
        create_integer_slider(customization_tab, "rabbithole_api_max_retry", "Rabbithole API Max Retry", "Maximum retry attempts for Rabbithole API")

        # --- Contacts Tab ---
        contacts_tab = tabview.tab("Contacts")

        scrollable_frame = customtkinter.CTkScrollableFrame(master=contacts_tab)
        scrollable_frame.pack(pady=2, padx=10, fill='both', expand=True)

        def create_contact_frame(platform):
            frame = create_integration_frame(scrollable_frame, f"{platform.capitalize()} Contacts")
            entry_name = customtkinter.CTkEntry(master=frame, placeholder_text=f"Add {platform} contact name")
            entry_name.pack(pady=2, padx=4, fill="x")

            entry_nicknames = customtkinter.CTkEntry(master=frame, placeholder_text=f"Add {platform} contact nicknames (comma-separated)")
            entry_nicknames.pack(pady=2, padx=4, fill="x")

            add_button = customtkinter.CTkButton(master=frame, text="Add", command=lambda: add_contact(platform, entry_name.get(), entry_nicknames.get()))
            add_button.pack(pady=2, padx=4, anchor="w")

            contacts_list = customtkinter.CTkScrollableFrame(master=frame)
            contacts_list.pack(pady=2, padx=4, fill="both", expand=True)

            def update_contacts_list():
                for widget in contacts_list.winfo_children():
                    widget.destroy()
                for contact in contacts[platform]:
                    contact_frame = customtkinter.CTkFrame(master=contacts_list)
                    contact_frame.pack(pady=2, padx=4, fill="x")
                    label = customtkinter.CTkLabel(master=contact_frame, text=f"Name: {contact['name']}, Nicknames: {', '.join(contact['nicknames'])}")
                    label.pack(side="left", pady=2, padx=4)
                    delete_button = customtkinter.CTkButton(master=contact_frame, text="Delete", command=lambda c=contact: delete_contact(platform, c))
                    delete_button.pack(side="right", pady=2, padx=4)

            def add_contact(platform, name, nicknames):
                if name:
                    nicknames_list = [nickname.strip() for nickname in nicknames.split(',')]
                    contact_found = False
                    for contact in contacts[platform]:
                        if contact["name"].lower() == name.lower():
                            contact["nicknames"] = nicknames_list
                            contact_found = True
                            break
                    if not contact_found:
                        contacts[platform].append({"name": name, "nicknames": nicknames_list})
                    save_contacts(contacts)
                    update_contacts_list()

            def delete_contact(platform, contact):
                if contact in contacts[platform]:
                    contacts[platform].remove(contact)
                    save_contacts(contacts)
                    update_contacts_list()

            update_contacts_list()

        for platform in contacts.keys():
            create_contact_frame(platform)



        ui_instance.mainloop()
        
        return ui_instance
