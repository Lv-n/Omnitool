import time
import threading
import sys
from pynput.mouse import Button, Controller
from pynput.keyboard import Listener, KeyCode, Key
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import keyboard
import pygame
import pyttsx3
from hPyT import *
import re
import time
import pyautogui
import pydirectinput
import ctypes, sys
import re
import time
import base64
import hashlib

version = "1.0"

# --- Initialize Pygame Sound ---
pygame.mixer.init()
try:
    click = pygame.mixer.Sound("Omnitool/nofitication.mp3")
    click.set_volume(0.5)
except FileNotFoundError:
    print("Warning: nofitication.mp3 not found. Sounds will not play.")
    # Dummy sound class to prevent crashes if the file is missing
    class DummySound:
        def play(self): pass
    click = DummySound()

# --- Global Variables ---
# Clicker Variables
TOGGLE_KEY = KeyCode(char="`")
clicking = False
mouse = Controller()
status_label = None
status_frame = None
click_interval = 1.0 
entry_field = None
key_entry_field = None 
info_label = None 
placeholder_text = "e.g., 1"
is_binding = False 
main_listener = None 
global window 
current_mouse_button = Button.left
mouse_button_var = None 

# Typer Variables
text_to_type = ""
trigger_key = ""
typer_status_frame = None
typer_status_label = None
typer_text_entry = None
typer_key_entry = None
current_hotkey_hook = None 
main_listener = None
typer_running = False

# TTS Variables
tts_textbox = None
tts_volume_slider = None
tts_speed_slider = None
tts_is_speaking = False
tts_stop_flag = False
vol_str = None
speed_str = None

# Settings Variables
settings_open = False
settings_frame_overlay = None
show_on_top = False
play_sounds = True

# Built-in console terminal
console_frame = None
console_textbox = None
console_visible = False
console_log = []
console_redirector = None
original_stdout = None
original_stderr = None
console_switch = None

appid = None

class TextRedirector:
    def __init__(self, textbox=None):
        self.textbox = textbox

    def write(self, text):
        global console_log
        if not text:
            return
        console_log.append(text)
        try:
            if self.textbox is not None:
                self.textbox.configure(state='normal')
                self.textbox.insert(tk.END, text)
                self.textbox.see(tk.END)
                self.textbox.configure(state='disabled')
        except Exception:
            pass

    def flush(self):
        pass


def enable_console_redirect():
    global original_stdout, original_stderr, console_redirector
    if original_stdout is None:
        original_stdout = sys.stdout
    if original_stderr is None:
        original_stderr = sys.stderr
    if console_redirector is None:
        console_redirector = TextRedirector()
    sys.stdout = console_redirector
    sys.stderr = console_redirector


def disable_console_redirect():
    global original_stdout, original_stderr
    if original_stdout is not None:
        sys.stdout = original_stdout
    if original_stderr is not None:
        sys.stderr = original_stderr
    original_stdout = None
    original_stderr = None 


def create_console_frame():
    global console_frame, console_textbox, child_window

    child_window = ctk.CTkToplevel(window)
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(str('Lv-n.Omnitool.devtest.'+ version))
    child_window.iconbitmap(default="")
    child_window.title("Omnitool Console")
    child_window.resizable(False, False)
    child_window.after(200, lambda: child_window.iconbitmap("Omnitool/logo.ico"))
    child_window.protocol("WM_DELETE_WINDOW", lambda: [child_window.destroy(), console_switch.toggle(), console_switch.update()])

    if console_frame is not None:
        return
    console_frame = ctk.CTkFrame(child_window, fg_color="#0D0D0D", corner_radius=10)
    console_frame.pack(expand=False, padx=10, pady=(0, 10))

    console_textbox = ctk.CTkTextbox(console_frame, width=410, height=200, fg_color="#0D0D0D", border_color="#0D0D0D", corner_radius=10)
    console_textbox.configure(state='disabled')
    console_textbox.pack(fill="both", expand=True)
    if console_redirector is not None:
        console_redirector.textbox = console_textbox
    populate_console_textbox()


def populate_console_textbox():
    if console_textbox is None:
        return
    try:
        console_textbox.configure(state='normal')
        console_textbox.delete('1.0', tk.END)
        console_textbox.insert(tk.END, ''.join(console_log))
        console_textbox.see(tk.END)
        console_textbox.configure(state='disabled')
    except Exception:
        pass


def destroy_console_frame():
    global console_frame, console_textbox, console_redirector
    if console_frame is not None:
        console_frame.destroy()
        console_frame = None
        child_window.destroy()
    console_textbox = None
    if console_redirector is not None:
        console_redirector.textbox = None


def toggle_console_visibility(state=None):
    global console_visible
    if state is None:
        state = not console_visible
    console_visible = bool(state)
    if console_visible:
        create_console_frame()
    else:
        destroy_console_frame()

# --- Auto Clicker Core Functions ---

def clicker():
    global clicking
    while True:
        if clicking:
            mouse.click(current_mouse_button, 1)
        sleep_time = max(click_interval, 0.001)
        time.sleep(sleep_time)

def update_mouse_button(event=None):
    global current_mouse_button
    play_effect()
    selection = mouse_button_var.get()
    if selection == "Left Click":
        current_mouse_button = Button.left
    elif selection == "Right Click":
        current_mouse_button = Button.right

def is_in_text_field():
    if not window:
        return False
    focused_widget = window.focus_get()
    
    # Updated to also ignore the TTS textbox
    if isinstance(focused_widget, tk.Entry) or isinstance(focused_widget, tk.Text) or 'entry' in str(focused_widget).lower() or 'textbox' in str(focused_widget).lower():
        return True
    return False

def toggle_event(key):
    global is_binding, clicking
    if is_binding:
        return
        
    if is_in_text_field():
        return 

    current_key = None
    try:
        if hasattr(key, 'char') and key.char is not None:
            current_key = KeyCode(char=key.char)
        else:
            current_key = key
    except AttributeError:
        current_key = key 

    if current_key == TOGGLE_KEY:
        clicking = not clicking
        window.after(0, update_status_label)

def update_status_label():
    if status_label and status_frame:
        if clicking:
            status_label.configure(text="Status:  ON ", text_color="#00C465")
            status_frame.configure(border_color="#00C465")
        else:
            status_label.configure(text="Status: OFF", text_color="#F7374F")
            status_frame.configure(border_color="#F7374F")
        window.update_idletasks()

def update_interval():
    global click_interval
    play_effect()
    try:
        current_text = entry_field.get()
        new_interval = float(current_text)

        if new_interval <= 0:
            print("Invalid Input", "Interval must be a positive number.")
            messagebox.showerror("Invalid Input", "Interval must be a positive number.")
            return
        if new_interval < 0.00001 or new_interval > 3600:
            print("Warning", "Maximum value is 1e-5 seconds to 3600 seconds (1 hour)")
            messagebox.showerror("Warning", "Maximum value is 1e-5 seconds to 3600 seconds (1 hour)")
            return

        click_interval = new_interval
        print("Success", f"Click interval updated to {click_interval} seconds.")
        messagebox.showinfo("Success", f"Click interval updated to {click_interval} seconds.")
    except ValueError:
        print("Invalid Input", "Please enter a valid number.")
        messagebox.showerror("Invalid Input", "Please enter a valid number.")

def start_key_binding():
    global is_binding, window
    play_effect()
    if main_listener and main_listener.is_alive():
        main_listener.stop()

    is_binding = True
    key_entry_field.configure(state='normal')
    key_entry_field.delete(0, tk.END)
    key_entry_field.insert(0, "Press a key...")
    key_entry_field.configure(state='readonly')
    
    if window:
        window.attributes('-topmost', True)
        window.focus_force()
        window.after(500, lambda: window.attributes('-topmost', True)) 

    temp_listener = Listener(on_release=capture_key)
    temp_listener.start()

def capture_key(key):
    global TOGGLE_KEY, is_binding
    
    if is_binding:
        key_text = ""
        try:
            if hasattr(key, 'char') and key.char is not None:
                TOGGLE_KEY = KeyCode(char=key.char)
                key_text = key.char
            else:
                TOGGLE_KEY = key
                key_text = str(key).replace('Key.', '') 
        except AttributeError:
            TOGGLE_KEY = key
            key_text = str(key)

        is_binding = False
        
        key_entry_field.configure(state='normal')
        key_entry_field.delete(0, tk.END)
        key_entry_field.insert(0, key_text)
        key_entry_field.configure(state='readonly')
        info_label.configure(text=f"Press '{key_text}' to toggle the auto clicker.")
        
        start_keyboard_listener()
        return False
        
    return True 

def validate_length(P):
    return len(P) <= 7

def on_focus_in(event):
    if entry_field.get() == placeholder_text:
        entry_field.delete(0, "end")

def on_focus_out(event):
    if entry_field.get() == "":
        entry_field.insert(0, placeholder_text)

def start_keyboard_listener():
    global main_listener
    if main_listener and main_listener.is_alive():
        main_listener.stop()
    main_listener = Listener(on_release=toggle_event)
    main_listener.start() 


def stop_keyboard_listener():
    global main_listener, clicking
    play_effect()
    if not main_listener:
        print("No active keyboard listener to stop.")
        return
    try:
        if main_listener.is_alive():
            main_listener.stop()
            print("Main listener stopped.")
        else:
            print("Main listener is not running.")
    except Exception as e:
        print(f"Error stopping main listener: {e}")
    finally:
        main_listener = None
        clicking = False
        if window:
            window.after(0, update_status_label)

# --- Auto Typer Core Functions ---
def parse_sheet(sheet_text):
    """
    Generator that extracts characters and chords cleanly.
    Crucially skips spaces and newlines to prevent invisible timing stutters.
    """
    i = 0
    while i < len(sheet_text):
        # Skip formatting characters that cause invisible rhythm gaps
        if sheet_text[i] in "\n\r ":
            i += 1
            continue
            
        if sheet_text[i] == "[":
            end_idx = sheet_text.find("]", i)
            if end_idx == -1:
                end_idx = len(sheet_text)
            # Yield the chord or delay tag with brackets included
            yield f"[{sheet_text[i+1:end_idx]}]"
            i = end_idx + 1
        else:
            yield sheet_text[i]
            i += 1

def _typing_worker(text_to_process, user_interval, tag_map, shift_chars):
    global typer_running, typer_status_label, typer_status_frame
    
    # A tiny stable buffer (0.01) is often more reliable on Windows than 0.0
    pydirectinput.PAUSE = 0.01 

    for item in parse_sheet(text_to_process):
        # Check mid-typing if the stop button was pressed
        if not typer_running:
            break

        # 1. Handle Bracketed Items (Delays, Named Keys, or Chords)
        if item.startswith('[') and item.endswith(']'):
            inner_content = item[1:-1].lower()
            
            # A. Custom Delays like [1s] or [500ms]
            delay_match = re.match(r'(\d+\.?\d*)(s|ms)', inner_content)
            if delay_match:
                value = float(delay_match.group(1))
                unit = delay_match.group(2)
                time.sleep(value if unit == "s" else value / 1000.0)
                continue

            # B. Named Special Tags
            if inner_content in tag_map:
                pydirectinput.press(tag_map[inner_content])
                time.sleep(user_interval)
                continue
                
            # C. Chords (Simultaneous presses with Shift support)
            keys_to_chord = item[1:-1] # Preserve original case for chords
            pressed_keys = []
            shift_held_for_chord = False

            for char in keys_to_chord:
                if not typer_running: 
                    break
                if char.isupper() or char in shift_chars:
                    if not shift_held_for_chord:
                        pydirectinput.keyDown('shift')
                        shift_held_for_chord = True
                    key_to_press = char.lower() if char.isupper() else shift_chars[char]
                else:
                    key_to_press = char.lower()

                pydirectinput.keyDown(key_to_press)
                pressed_keys.append(key_to_press)

            for key_to_release in reversed(pressed_keys):
                pydirectinput.keyUp(key_to_release)

            if shift_held_for_chord:
                pydirectinput.keyUp('shift')

            time.sleep(user_interval)
            continue

        # 2. Handle Single Regular Characters (With Shift support)
        char = item
        if char.isupper():
            pydirectinput.keyDown('shift')
            pydirectinput.press(char.lower())
            pydirectinput.keyUp('shift')
        elif char in shift_chars:
            pydirectinput.keyDown('shift')
            pydirectinput.press(shift_chars[char])
            pydirectinput.keyUp('shift')
        else:
            pydirectinput.press(char.lower())
        
        # Explicit pacing sleep matching the logic that fixed your stutters
        time.sleep(user_interval)

    # Safely revert UI when typing completes naturally
    typer_running = False

def type_text_on_hotkey():
    """Triggered by your hotkey; hands execution over to a dedicated background thread."""
    global text_to_type, typer_interval_entry, typer_running
    
    if typer_running:
        return 
    typer_running = True

    try:
        user_interval = float(typer_interval_entry.get())
    except ValueError:
        user_interval = 0.01

    tag_map = {
        "shift": "shift", "ctrl": "ctrl", "alt": "alt",
        "esc": "escape", "enter": "enter", "tab": "tab",
        "capslock": "capslock", "space": "space", "delete": "delete", "backspace": "backspace",
        "up": "up", "down": "down", "left": "left", "right": "right"
    }

    shift_chars = {
        '~': '`', '!': '1', '@': '2', '#': '3', '$': '4', '%': '5',
        '^': '6', '&': '7', '*': '8', '(': '9', ')': '0', '_': '-',
        '+': '=', '{': '[', '}': ']', '|': '\\', ':': ';', '"': "'",
        '<': ',', '>': '.', '?': '/'
    }

    # Start the macro processing loop on its own isolated background thread
    threading.Thread(
        target=_typing_worker, 
        args=(text_to_type, user_interval, tag_map, shift_chars), 
        daemon=True
    ).start()


def stop_typing_hotkey():
    global current_hotkey_hook, typer_running
    play_effect()
    
    # Force the typing loop to drop out immediately
    typer_running = False 
    
    if current_hotkey_hook is None:
        print("No typer hotkey is currently active.")
        messagebox.showerror("error", "No typer hotkey is currently active.")
        return
    try:
        keyboard.remove_hotkey(current_hotkey_hook)
        current_hotkey_hook = None
        typer_status_label.configure(text="Status: OFF", text_color="#F7374F")
        typer_status_frame.configure(border_color="#F7374F", width=125)
        print("Typer hotkey stopped and string sequence cancelled.")
    except Exception as e:
        print(f"Error stopping typer hotkey: {e}")

def apply_typer_settings():
    global text_to_type, trigger_key, current_hotkey_hook
    play_effect()
    
    text_to_type = typer_text_entry.get()
    trigger_key = typer_key_entry.get().lower().strip()
    
    if not text_to_type or not trigger_key:
        print("Both the text and the trigger key must be entered.")
        messagebox.showerror("Input Error", "Both the text and the trigger key must be entered.")
        return

    try:
        if current_hotkey_hook is not None:
            try:
                keyboard.remove_hotkey(current_hotkey_hook)
            except Exception:
                pass
                
        current_hotkey_hook = keyboard.add_hotkey(trigger_key, type_text_on_hotkey, suppress=True)
        typer_status_label.configure(text=f"Status: ON (Key: {trigger_key.upper()})", text_color="#00C465")
        typer_status_frame.configure(border_color="#00C465", width=(len(f"Status: ON (Key: {trigger_key.upper()})")+3) * 10)
    except ValueError as e:
        messagebox.showerror("Hotkey Error", f"Invalid key combination: {e}")
        print(f"Invalid key combination: {e}")

if False: #disabled, a second alternate function for the auto typer
    def type_text_on_hotkey():
        global text_to_type, typer_interval_entry
        
        # Try to get the interval from the UI, default to 0.01 if it's empty/invalid
        try:
            user_interval = float(typer_interval_entry.get())
        except ValueError:
            user_interval = 0.01

        tag_map = {
            "[shift]": "shift", "[ctrl]": "ctrl", "[alt]": "alt",
            "[esc]": "esc", "[enter]": "enter", "[tab]": "tab",
            "[capslock]": "capslock", "[space]": "space",
            "[up]": "up", "[down]": "down", "[left]": "left", "[right]": "right"
        }

        parts = re.split(r'(\[.*?\])', text_to_type)

        for part in parts:
            if not part: continue
            low_part = part.lower()

            # Handle Delays [1s]
            delay_match = re.match(r'\[(\d+\.?\d*)(s|ms)\]', low_part)
            if delay_match:
                value = float(delay_match.group(1))
                unit = delay_match.group(2)
                time.sleep(value if unit == "s" else value / 1000.0)
                continue

            # Handle Tags
            if low_part in tag_map:
                pyautogui.press(tag_map[low_part])
                continue

            # Handle Regular Text with the Dynamic Interval
            if not part.startswith('['):
                # Using the interval from the textbox
                pyautogui.typewrite(part, interval=user_interval)


# --- Text-to-Speech Core Functions ---

def tts_worker_thread(text, rate, volume):
    """Background thread to handle TTS without freezing the UI."""
    global tts_stop_flag, tts_is_speaking
    tts_is_speaking = True
    tts_stop_flag = False

    try:
        # Re-initialize engine every time to prevent the "one-play-only" bug
        engine = pyttsx3.init()
        engine.setProperty('rate', rate)
        engine.setProperty('volume', volume)

        # Inner function to monitor the stop flag
        def on_word(name, location, length):
            if tts_stop_flag:
                engine.stop()

        engine.connect('started-word', on_word)
        
        # Start the speech
        engine.say(text)
        engine.runAndWait()
        
    except Exception as e:
        print(f"TTS Error: {e}")
    finally:
        # Reset speaking state so user can play again
        tts_is_speaking = False
        # Clean up engine reference
        try:
            del engine
        except:
            pass

def play_tts():
    play_effect()
    global tts_is_speaking
    
    # If already speaking, don't start a second overlapping thread
    if tts_is_speaking:
        return 

    text = tts_textbox.get("1.0", tk.END).strip()
    if not text:
        return

    rate = int(tts_speed_slider.get())
    volume = float(tts_volume_slider.get())

    # Create and start the thread
    t = threading.Thread(target=tts_worker_thread, args=(text, rate, volume), daemon=True)
    t.start()

def stop_tts():
    play_effect()
    global tts_stop_flag
    # Setting this to True tells the on_word callback to kill the engine
    tts_stop_flag = True

# --- Encryption / Decryption Core Functions ---
def encrypt_text(text, key, algorithm, alphabet="abcdefghijklmnopqrstuvwxyz", shift=3):
    try:
        if algorithm == "Base64":
            return base64.b64encode(text.encode('utf-8')).decode('utf-8')
            
        elif algorithm == "XOR Cipher":
            if not key: return "Error: Secret Key required for XOR"
            text_bytes = text.encode('utf-8')
            key_bytes = key.encode('utf-8')
            encrypted = bytearray(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(text_bytes))
            return base64.b64encode(encrypted).decode('utf-8')
            
        elif algorithm == "Caesar Cipher":
            if not alphabet: return "Error: Alphabet structure cannot be blank."
            result = []
            algo_len = len(alphabet)
            
            # Map out standard lowercase/uppercase variations for a dynamic layout
            lower_alpha = alphabet.lower()
            upper_alpha = alphabet.upper()
            
            for char in text:
                if char in lower_alpha:
                    idx = lower_alpha.index(char)
                    result.append(lower_alpha[(idx + shift) % algo_len])
                elif char in upper_alpha:
                    idx = upper_alpha.index(char)
                    result.append(upper_alpha[(idx + shift) % algo_len])
                else:
                    result.append(char)
            return "".join(result)
            
    except Exception as e:
        return f"Encryption Error: {str(e)}"

def decrypt_text(encoded_text, key, algorithm, alphabet="abcdefghijklmnopqrstuvwxyz", shift=3):
    try:
        if algorithm == "Base64":
            return base64.b64decode(encoded_text.encode('utf-8')).decode('utf-8')
            
        elif algorithm == "XOR Cipher":
            if not key: return "Error: Secret Key required for XOR"
            encrypted_bytes = base64.b64decode(encoded_text.encode('utf-8'))
            key_bytes = key.encode('utf-8')
            decrypted = bytearray(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(encrypted_bytes))
            return decrypted.decode('utf-8')
            
        elif algorithm == "Caesar Cipher":
            if not alphabet: return "Error: Alphabet structure cannot be blank."
            result = []
            algo_len = len(alphabet)
            
            lower_alpha = alphabet.lower()
            upper_alpha = alphabet.upper()
            
            for char in encoded_text:
                if char in lower_alpha:
                    idx = lower_alpha.index(char)
                    result.append(lower_alpha[(idx - shift) % algo_len])
                elif char in upper_alpha:
                    idx = upper_alpha.index(char)
                    result.append(upper_alpha[(idx - shift) % algo_len])
                else:
                    result.append(char)
            return "".join(result)
            
    except Exception:
        return "Decryption Error: Invalid text format or configuration."

# Global helper to animate tab transitions from anywhere
def animate_tab_change(new_tab_name):
    play_effect()
    if window:
        window.attributes("-alpha", 0.6)
        def ramp_up(opacity):
            if opacity <= 1.0:
                window.attributes("-alpha", opacity)
                window.after(10, lambda: ramp_up(opacity + 0.03))
        ramp_up(0.6)

# Settinga
def toggle_settings():
    global settings_open, settings_frame_overlay, play_sounds, show_on_top, console_switch
    play_effect() # Uses the new helper[cite: 1]
    animate_tab_change("Settings")
    
    if not settings_open:
        settings_frame_overlay = ctk.CTkFrame(window, fg_color="#0D0D0D", corner_radius=0)
        settings_frame_overlay.place(relx=0, rely=0.06, relwidth=1, relheight=0.94) #[cite: 1]
        
        # --- Stay On Top Toggle ---
        def toggle_topmost():
            global show_on_top
            show_on_top = not show_on_top
            window.attributes("-topmost", show_on_top) #[cite: 1]
            play_effect()

        topmost_switch = ctk.CTkSwitch(settings_frame_overlay, text="Always on Top", 
                                       command=toggle_topmost, progress_color="#4D4D4D")
        if show_on_top: topmost_switch.select() #[cite: 1]
        topmost_switch.pack(pady=10, padx=(0,250))

        # --- Sound Switch Toggle ---
        def toggle_sound_state():
            global play_sounds
            play_sounds = sound_switch.get() # Get state from switch[cite: 1]
            if play_sounds:
                play_effect()

        sound_switch = ctk.CTkSwitch(settings_frame_overlay, text="Enable Sounds", 
                                     command=toggle_sound_state, progress_color="#4D4D4D")
        if play_sounds: sound_switch.select() #[cite: 1]
        sound_switch.pack(pady=10, padx=(0,255))

        # --- Console Display Toggle ---
        console_switch = ctk.CTkSwitch(settings_frame_overlay, text="Show In-App Console", 
                                       command=toggle_console_visibility, progress_color="#4D4D4D")
        if console_visible:
            console_switch.select()
        console_switch.pack(pady=10, padx=(0,225))

        versionLabel = ctk.CTkLabel(settings_frame_overlay, text=f"Version: {version}", font=("Arial Bold",20))
        versionLabel.pack(pady=25)

        settings_open = True
    else:
        settings_frame_overlay.destroy()
        settings_open = False

def play_effect():
    if play_sounds:
        click.play() #

# --- GUI Setup ---

def start_window():
    global status_label, entry_field, key_entry_field, info_label, window, mouse_button_var, status_frame
    global typer_text_entry, typer_key_entry, typer_status_label, current_hotkey_hook, typer_status_frame, typer_interval_entry
    global tts_textbox, tts_speed_slider, tts_volume_slider, console_textbox
    global title_bar

    appid = str('Lv-n.Omnitool.devtest.'+ version) # Any unique string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)
    print(appid)
    window = ctk.CTk()
    window.title("Omnitool")
    window.iconbitmap(default="")  # Removes the default icon if none is provided
    window.geometry(f"450x600+{int(window.winfo_screenwidth()/2 - 400/2)}+{int(window.winfo_screenheight()/2 - 600/2)}")
    window.resizable(False, False)
    window.configure(fg_color="#0D0D0D")
    window.iconbitmap("Omnitool/logo.ico")
    title_bar_color.set(window, color='#0D0D0D')
    all_stuffs.hide(window)
    title_bar_text_color.set(window, color='#0D0D0D')

    def on_closing():
        play_effect()
        # Added this back so the program closes cleanly!
        if main_listener and main_listener.is_alive():
            main_listener.stop()
        if current_hotkey_hook is not None:
            try: keyboard.remove_hotkey(current_hotkey_hook)
            except Exception: pass
        disable_console_redirect()
        window.destroy()
        sys.exit()

    window.protocol("WM_DELETE_WINDOW", on_closing)

    def minimize_app():
        play_effect()
        window.iconify()

    def reset_tts_defaults():
        play_effect()
        tts_volume_slider.set(1.0)
        tts_speed_slider.set(150)
        # Update the number displays manually since set() doesn't always trigger commands
        vol_str.set("1.0")
        speed_str.set("150")

    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]

    def rgb_to_hex(rgb):
        return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])

    def animate_hover(button, start_hex, end_hex, steps=10, duration=15):
        """Linearly interpolates between two colors for a smooth hover effect."""
        start_rgb = hex_to_rgb(start_hex)
        target_rgb = hex_to_rgb(end_hex)
        
        # Calculate the change needed per step
        diff = [(t - s) / steps for s, t in zip(start_rgb, target_rgb)]
        
        def run_step(current_step, current_rgb):
            if current_step < steps:
                new_rgb = [int(current_rgb[i] + diff[i]) for i in range(3)]
                button.configure(fg_color=rgb_to_hex(new_rgb))
                window.after(duration, lambda: run_step(current_step + 1, new_rgb))
        
        run_step(0, start_rgb)

    # --- Title Bar Dragging Logic ---
    def get_pos(event):
        window.xwin = event.x
        window.ywin = event.y

    def move_window(event):
        window.geometry(f'+{event.x_root - window.xwin}+{event.y_root - window.ywin}')

    # --- Custom Title Bar UI ---
    title_bar = ctk.CTkFrame(window, height=35, fg_color="#0D0D0D", corner_radius=10)
    title_bar.pack(fill="x", side="top")

    title_bar.bind("<Button-1>", get_pos)
    title_bar.bind("<B1-Motion>", move_window)

    title_label = ctk.CTkLabel(title_bar, text=" Ω  Omnitool", font=("Arial Bold", 14), text_color="white")
    title_label.pack(side="left", padx=10)

    # [Close Button with Transition]
    close_button = ctk.CTkButton(title_bar, text="✕", width=45, height=35, 
                                 fg_color="#0D0D0D", corner_radius=12, command=on_closing)
    close_button.pack(side="right")
    
    # Red Fade-in
    close_button.bind("<Enter>", lambda e: animate_hover(close_button, "#0D0D0D", "#505050"))
    # Dark Fade-out
    close_button.bind("<Leave>", lambda e: animate_hover(close_button, "#505050", "#0D0D0D"))

    # [Minimize Button with Transition]
    min_button = ctk.CTkButton(title_bar, text="—", width=45, height=35, 
                               fg_color="#0D0D0D", corner_radius=12, 
                               command=minimize_app)
    min_button.pack(side="right")

    # Gray Fade-in
    min_button.bind("<Enter>", lambda e: animate_hover(min_button, "#0D0D0D", "#505050"))
    # Dark Fade-out
    min_button.bind("<Leave>", lambda e: animate_hover(min_button, "#505050", "#0D0D0D"))

    # Add this near your close_button and min_button code
    settings_button = ctk.CTkButton(title_bar, text="⚙", width=45, height=35, 
                                    fg_color="#0D0D0D", corner_radius=12, 
                                    command=lambda: toggle_settings())
    settings_button.pack(side="right")

    # Apply your existing hover animation
    settings_button.bind("<Enter>", lambda e: animate_hover(settings_button, "#0D0D0D", "#505050"))
    settings_button.bind("<Leave>", lambda e: animate_hover(settings_button, "#505050", "#0D0D0D"))

    # --- Tab Transition Logic ---
    def animate_tab_change(new_tab_name):
        play_effect()
        window.attributes("-alpha", 0.6)
        def ramp_up(opacity):
            if opacity <= 1.0:
                window.attributes("-alpha", opacity)
                window.after(10, lambda: ramp_up(opacity + 0.03))
        ramp_up(0.6)

    # (Rest of your TabView and other code remains the same below this)
    # Initialize the Tabview
    tabview = ctk.CTkTabview(
        window, 
        command=lambda: animate_tab_change(tabview.get()),
        # --- Color Customization ---
        segmented_button_selected_color="#4D4D4D",
        segmented_button_unselected_color="#0D0D0D",
        segmented_button_fg_color="#2B2B2B",
        segmented_button_selected_hover_color="#4D4D4D",
        segmented_button_unselected_hover_color="#4D4D4D"
    )

    tabview.pack(padx=10, pady=(0, 10), fill="both", expand=True)

    # Add your tabs
    clicker_tab = tabview.add("Auto Clicker")
    typer_tab = tabview.add("Auto Typer")
    tts_tab = tabview.add("Text to Speech")
    cryptographic_tab = tabview.add("Crypto")

    # ==========================================
    #             TAB 1: AUTO CLICKER
    # ==========================================
    mouse_button_label = ctk.CTkLabel(clicker_tab, text="Mouse Button:", font=("Arial", 17))
    mouse_button_label.pack(pady=(5, 5))

    mouse_button_var = ctk.StringVar(window)
    mouse_button_var.set("Left Click") 
    
    mouse_button_dropdown = ctk.CTkComboBox(
        clicker_tab, variable=mouse_button_var, values=("Left Click", "Right Click"),
        state="readonly", width=150, font=("Arial", 12), command=update_mouse_button, fg_color="#0D0D0D", border_color="#0D0D0D", button_color="#0D0D0D", dropdown_fg_color="#0D0D0D", corner_radius=10
    )
    mouse_button_dropdown.pack(pady=5)
    
    key_text = TOGGLE_KEY.char if hasattr(TOGGLE_KEY, 'char') and TOGGLE_KEY.char is not None else str(TOGGLE_KEY).replace('Key.', '')
    info_label = ctk.CTkLabel(clicker_tab, text=f"Press '{key_text}' to toggle the auto clicker.", font=("Arial", 17))
    info_label.pack(pady=(0, 10))

    status_frame = ctk.CTkFrame(clicker_tab, fg_color="#0D0D0D", height=36, width=125, corner_radius=10, border_color="#F7374F", border_width=3)
    status_frame.pack_propagate(False)
    status_frame.pack()

    status_label = ctk.CTkLabel(status_frame, text="Status: OFF", font=("Arial", 20), text_color="#F7374F")
    status_label.pack()
    status_label.place(relx=0.5, rely=0.5, anchor="center")

    interval_label = ctk.CTkLabel(clicker_tab, text="Click Interval (seconds):", font=("Arial", 15))
    interval_label.pack(pady=(5, 5))

    vcmd = window.register(validate_length)

    entry_field = ctk.CTkEntry(clicker_tab, width=250, font=("Arial", 15), validate="key", validatecommand=(vcmd, '%P'), fg_color="#0D0D0D", border_color="#0D0D0D",  corner_radius=10)
    entry_field.insert(0, placeholder_text)
    entry_field.bind("<FocusIn>", on_focus_in)
    entry_field.bind("<FocusOut>", on_focus_out)
    entry_field.pack()

    update_button = ctk.CTkButton(clicker_tab, text="Set Interval", command=update_interval, fg_color="#0D0D0D", hover_color="#0D0D0D", font=("Arial", 15))
    update_button.pack(pady=10)

    # Gray Fade-in
    update_button.bind("<Enter>", lambda e: animate_hover(update_button, "#0D0D0D", "#505050"))
    # Dark Fade-out
    update_button.bind("<Leave>", lambda e: animate_hover(update_button, "#505050", "#0D0D0D"))

    key_label = ctk.CTkLabel(clicker_tab, text="Set Toggle Key:", font=("Arial", 15))
    key_label.pack(pady=(5, 5))

    key_entry_field = ctk.CTkEntry(clicker_tab, width=150, font=("Arial", 15), justify='center', state='readonly',fg_color="#0D0D0D", border_color="#0D0D0D", corner_radius=10)
    key_entry_field.insert(0, key_text,) 
    key_entry_field.pack(pady=5)

    bind_button = ctk.CTkButton(clicker_tab, text="Change Key", command=start_key_binding, fg_color="#0D0D0D", hover_color="#505050", font=("Arial", 15))
    bind_button.pack(pady=5)

    # Gray Fade-in
    bind_button.bind("<Enter>", lambda e: animate_hover(bind_button, "#0D0D0D", "#505050"))
    # Dark Fade-out
    bind_button.bind("<Leave>", lambda e: animate_hover(bind_button, "#505050", "#0D0D0D"))

    # ==========================================
    #             TAB 2: AUTO TYPER
    # ==========================================
    typer_header = ctk.CTkLabel(typer_tab, text="Hotkey Text Typer", font=("Arial", 20, "bold"))
    typer_header.pack(pady=(15, 20))

    typer_status_frame = ctk.CTkFrame(typer_tab, fg_color="#0D0D0D", height=36, width=125, corner_radius=10, border_color="#F7374F", border_width=3)
    typer_status_frame.pack_propagate(False)
    typer_status_frame.pack()

    typer_status_label = ctk.CTkLabel(typer_status_frame, text="Status: OFF", font=("Arial", 20), text_color="#F7374F")
    typer_status_label.pack()
    typer_status_label.place(relx=0.5, rely=0.5, anchor="center")

    text_label = ctk.CTkLabel(typer_tab, text="Text to Type:", font=("Arial", 15))
    text_label.pack(anchor="w", padx=40)
    
    typer_text_entry = ctk.CTkEntry(typer_tab, width=300, font=("Arial", 15), fg_color="#0D0D0D", border_color="#0D0D0D", corner_radius=10)
    typer_text_entry.pack(pady=(5, 15))

    key_label_typer = ctk.CTkLabel(typer_tab, text="Trigger Key/Combo (e.g. f8, ctrl+m):", font=("Arial", 15))
    key_label_typer.pack(anchor="w", padx=40)

    typer_key_entry = ctk.CTkEntry(typer_tab, width=300, font=("Arial", 15), fg_color="#0D0D0D", border_color="#0D0D0D", corner_radius=10)
    typer_key_entry.insert(0, "f8") 
    typer_key_entry.pack(pady=(5, 25))

    apply_typer_button = ctk.CTkButton(typer_tab, text="Apply Hotkey", command=apply_typer_settings, height=40, fg_color="#0D0D0D", hover_color="#0D0D0D", font=("Arial", 15))
    apply_typer_button.pack()

    # Gray Fade-in
    apply_typer_button.bind("<Enter>", lambda e: animate_hover(apply_typer_button, "#0D0D0D", "#505050"))
    # Dark Fade-out
    apply_typer_button.bind("<Leave>", lambda e: animate_hover(apply_typer_button, "#505050", "#0D0D0D"))

    interval_label_typer = ctk.CTkLabel(typer_tab, text="Typing Speed (seconds per key):", font=("Arial", 15))
    interval_label_typer.pack(anchor="w", padx=40, pady=(5, 0))

    typer_interval_entry = ctk.CTkEntry(typer_tab, width=300, font=("Arial", 15), fg_color="#0D0D0D", border_color="#0D0D0D", corner_radius=10)
    typer_interval_entry.insert(0, "0.01") # Default speed
    typer_interval_entry.pack(pady=(5, 15))

    stop_keyboard_listener_btn = ctk.CTkButton(typer_tab, text="Stop", fg_color="#0D0D0D", hover_color="#505050", command=stop_typing_hotkey)
    stop_keyboard_listener_btn.pack()

    # Gray Fade-in
    stop_keyboard_listener_btn.bind("<Enter>", lambda e: animate_hover(stop_keyboard_listener_btn, "#0D0D0D", "#505050"))
    # Dark Fade-out
    stop_keyboard_listener_btn.bind("<Leave>", lambda e: animate_hover(stop_keyboard_listener_btn, "#505050", "#0D0D0D"))

   # ==========================================
    #             TAB 3: TEXT TO SPEECH
    # ==========================================
    tts_header = ctk.CTkLabel(tts_tab, text="Text-to-Speech Engine", font=("Arial", 20, "bold"))
    tts_header.pack(pady=(10, 10))

    tts_textbox = ctk.CTkTextbox(tts_tab, width=380, height=100, font=("Arial", 15), fg_color="#0D0D0D", border_color="#0D0D0D", corner_radius=10)
    tts_textbox.pack(pady=5)
    tts_textbox.insert("1.0", "Hello! Type anything here and I will say it out loud.")

    # StringVars to hold the live numbers
    vol_str = ctk.StringVar(value="1.0")
    speed_str = ctk.StringVar(value="150")

    # Controls Frame
    controls_frame = ctk.CTkFrame(tts_tab, fg_color="#0D0D0D")
    controls_frame.pack(pady=10, fill="x", padx=20)

    # Volume Control
    vol_label = ctk.CTkLabel(controls_frame, text="Volume:", font=("Arial", 15))
    vol_label.grid(row=0, column=0, padx=10, sticky="w")
    
    tts_volume_slider = ctk.CTkSlider(
        controls_frame, from_=0.0, to=1.0, width=150,
        command=lambda v: vol_str.set(f"{float(v):.1f}") # Updates the label live
    )
    tts_volume_slider.set(1.0)
    tts_volume_slider.grid(row=0, column=1, pady=5)
    tts_volume_slider.configure(progress_color="#7A7A7A",button_color="#818181")

    vol_num_display = ctk.CTkLabel(controls_frame, textvariable=vol_str, font=("Arial", 15, "bold"), width=40)
    vol_num_display.grid(row=0, column=2, padx=5)

    # Speed Control
    speed_label = ctk.CTkLabel(controls_frame, text="Speed:", font=("Arial", 15))
    speed_label.grid(row=1, column=0, padx=10, sticky="w")

    tts_speed_slider = ctk.CTkSlider(
        controls_frame, from_=50, to=300, width=150,
        command=lambda v: speed_str.set(f"{int(float(v))}") # Updates the label live
    )
    tts_speed_slider.set(150)
    tts_speed_slider.grid(row=1, column=1, pady=5)
    tts_speed_slider.configure(progress_color="#7A7A7A",button_color="#818181")

    speed_num_display = ctk.CTkLabel(controls_frame, textvariable=speed_str, font=("Arial", 15, "bold"), width=40)
    speed_num_display.grid(row=1, column=2, padx=5)

    # Reset Button (placed under the sliders)
    reset_button = ctk.CTkButton(tts_tab, text="Reset to Defaults", command=reset_tts_defaults, 
                              width=150, height=30, fg_color="#0D0D0D", hover_color="#0D0D0D", font=("Arial", 15))
    reset_button.pack(pady=(0, 10))

    # Gray Fade-in
    reset_button.bind("<Enter>", lambda e: animate_hover(reset_button, "#0D0D0D", "#505050"))
    # Dark Fade-out
    reset_button.bind("<Leave>", lambda e: animate_hover(reset_button, "#505050", "#0D0D0D"))

    # Buttons Frame
    btn_frame = ctk.CTkFrame(tts_tab, fg_color="transparent")
    btn_frame.pack(pady=5)

    play_button = ctk.CTkButton(btn_frame, text="▶ Play", command=play_tts, width=120, fg_color="#0D0D0D", hover_color="#0D0D0D")
    play_button.grid(row=0, column=0, padx=15)

    # Gray Fade-in
    play_button.bind("<Enter>", lambda e: animate_hover(play_button, "#0D0D0D", "#505050"))
    # Dark Fade-out
    play_button.bind("<Leave>", lambda e: animate_hover(play_button, "#505050", "#0D0D0D"))

    stop_button = ctk.CTkButton(btn_frame, text="⏹ Stop", command=stop_tts, width=120, fg_color="#0D0D0D", hover_color="#0D0D0D")
    stop_button.grid(row=0, column=1, padx=15)

    # Gray Fade-in
    stop_button.bind("<Enter>", lambda e: animate_hover(stop_button, "#0D0D0D", "#505050"))
    # Dark Fade-out
    stop_button.bind("<Leave>", lambda e: animate_hover(stop_button, "#505050", "#0D0D0D"))

    # ==========================================
    #             TAB 4: CRYPTO
    # ==========================================
    cryptographic_header = ctk.CTkLabel(cryptographic_tab, text="Text Encrypter & Decrypter", font=("Arial", 20, "bold"))
    cryptographic_header.pack(pady=(5, 5))

    # Crypto Selection Dropdown
    algo_label = ctk.CTkLabel(cryptographic_tab, text="Select Algorithm:", font=("Arial", 14))
    algo_label.pack(anchor="w", padx=35)

    algo_var = ctk.StringVar(value="Base64")
    
    def on_algo_change(choice):
        play_effect()
        # Dynamically switch visible layout widgets depending on algorithmic constraints
        if choice == "Base64":
            key_container.pack_forget()
            caesar_container.pack_forget()
        elif choice == "XOR Cipher":
            caesar_container.pack_forget()
            key_container.pack(before=cryptographic_btn_frame, pady=3)
        elif choice == "Caesar Cipher":
            key_container.pack_forget()
            caesar_container.pack(before=cryptographic_btn_frame, pady=3)

    algo_dropdown = ctk.CTkComboBox(
        cryptographic_tab, variable=algo_var, values=("Base64", "XOR Cipher", "Caesar Cipher"),
        state="readonly", width=380, font=("Arial", 13), command=on_algo_change,
        fg_color="#0D0D0D", border_color="#0D0D0D", button_color="#0D0D0D", dropdown_fg_color="#0D0D0D", corner_radius=10
    )
    algo_dropdown.pack(pady=(0, 5))

    cryptographic_input_label = ctk.CTkLabel(cryptographic_tab, text="Input Text:", font=("Arial", 14))
    cryptographic_input_label.pack(anchor="w", padx=35)

    cryptographic_input_textbox = ctk.CTkTextbox(cryptographic_tab, width=380, height=70, font=("Arial", 15), fg_color="#0D0D0D", border_color="#0D0D0D", corner_radius=10)
    cryptographic_input_textbox.pack(pady=3)

    # Contextual Container 1: Symmetric Secret Key (XOR)
    key_container = ctk.CTkFrame(cryptographic_tab, fg_color="transparent")
    cryptographic_key_label = ctk.CTkLabel(key_container, text="Secret Key:", font=("Arial", 14))
    cryptographic_key_label.pack(anchor="w", padx=25)
    cryptographic_key_entry = ctk.CTkEntry(key_container, width=380, font=("Arial", 15), fg_color="#0D0D0D", border_color="#0D0D0D", corner_radius=10, show="*", placeholder_text="Enter encryption key")
    cryptographic_key_entry.pack()

    # Contextual Container 2: Dynamic Caesar Shift Blocks
    caesar_container = ctk.CTkFrame(cryptographic_tab, fg_color="transparent")
    
    sub_flex_frame = ctk.CTkFrame(caesar_container, fg_color="transparent")
    sub_flex_frame.pack(fill="x")
    
    # Custom Shift Configuration Input
    shift_block = ctk.CTkFrame(sub_flex_frame, fg_color="transparent")
    shift_block.pack(side="left", padx=(25, 5))
    ctk.CTkLabel(shift_block, text="Shift Amount:", font=("Arial", 14)).pack(anchor="w")
    caesar_shift_entry = ctk.CTkEntry(shift_block, width=100, font=("Arial", 15), fg_color="#0D0D0D", border_color="#0D0D0D", corner_radius=10)
    caesar_shift_entry.insert(0, "3")
    caesar_shift_entry.pack()
    
    # Custom Custom Alphabet Structure Definition Entry
    alpha_block = ctk.CTkFrame(sub_flex_frame, fg_color="transparent")
    alpha_block.pack(side="right", padx=(5, 25))
    ctk.CTkLabel(alpha_block, text="Target Alphabet:", font=("Arial", 14)).pack(anchor="w")
    caesar_alpha_entry = ctk.CTkEntry(alpha_block, width=270, font=("Arial", 15), fg_color="#0D0D0D", border_color="#0D0D0D", corner_radius=10)
    caesar_alpha_entry.insert(0, "abcdefghijklmnopqrstuvwxyz")
    caesar_alpha_entry.pack()

    cryptographic_btn_frame = ctk.CTkFrame(cryptographic_tab, fg_color="transparent")
    cryptographic_btn_frame.pack(pady=8)

    def trigger_encrypt():
        play_effect()
        text = cryptographic_input_textbox.get("1.0", tk.END).strip()
        key = cryptographic_key_entry.get().strip()
        algorithm = algo_var.get()
        
        alphabet_val = caesar_alpha_entry.get().strip()
        try:
            shift_val = int(caesar_shift_entry.get().strip())
        except ValueError:
            shift_val = 3
        
        if not text:
            update_cryptographic_output("Error: Input text field cannot be empty.")
            return
            
        res = encrypt_text(text, key, algorithm, alphabet=alphabet_val, shift=shift_val)
        update_cryptographic_output(res)

    def trigger_decrypt():
        play_effect()
        text = cryptographic_input_textbox.get("1.0", tk.END).strip()
        key = cryptographic_key_entry.get().strip()
        algorithm = algo_var.get()
        
        alphabet_val = caesar_alpha_entry.get().strip()
        try:
            shift_val = int(caesar_shift_entry.get().strip())
        except ValueError:
            shift_val = 3
        
        if not text:
            update_cryptographic_output("Error: Input text field cannot be empty.")
            return
            
        res = decrypt_text(text, key, algorithm, alphabet=alphabet_val, shift=shift_val)
        update_cryptographic_output(res)

    def update_cryptographic_output(output_string):
        cryptographic_output_textbox.configure(state="normal")
        cryptographic_output_textbox.delete("1.0", tk.END)
        cryptographic_output_textbox.insert("1.0", output_string)
        cryptographic_output_textbox.configure(state="disabled")

    encrypt_button = ctk.CTkButton(cryptographic_btn_frame, text="🔒 Encrypt", command=trigger_encrypt, width=150, fg_color="#0D0D0D", hover_color="#0D0D0D", font=("Arial", 15))
    encrypt_button.grid(row=0, column=0, padx=15)
    encrypt_button.bind("<Enter>", lambda e: animate_hover(encrypt_button, "#0D0D0D", "#505050"))
    encrypt_button.bind("<Leave>", lambda e: animate_hover(encrypt_button, "#505050", "#0D0D0D"))

    decrypt_button = ctk.CTkButton(cryptographic_btn_frame, text="🔓 Decrypt", command=trigger_decrypt, width=150, fg_color="#0D0D0D", hover_color="#0D0D0D", font=("Arial", 15))
    decrypt_button.grid(row=0, column=1, padx=15)
    decrypt_button.bind("<Enter>", lambda e: animate_hover(decrypt_button, "#0D0D0D", "#505050"))
    decrypt_button.bind("<Leave>", lambda e: animate_hover(decrypt_button, "#505050", "#0D0D0D"))

    cryptographic_output_label = ctk.CTkLabel(cryptographic_tab, text="Output Text:", font=("Arial", 14))
    cryptographic_output_label.pack(anchor="w", padx=35)

    cryptographic_output_textbox = ctk.CTkTextbox(cryptographic_tab, width=380, height=70, font=("Arial", 15), fg_color="#0D0D0D", border_color="#0D0D0D", corner_radius=10)
    cryptographic_output_textbox.configure(state="disabled")
    cryptographic_output_textbox.pack(pady=3)

    # Run default setup hidden view states instantly on initialization
    on_algo_change("Base64")

    window.mainloop()

# --- Program Initialization ---
enable_console_redirect()
click_thread = threading.Thread(target=clicker, daemon=True)
click_thread.start()

start_keyboard_listener()

if __name__ == "__main__":
    start_window()
