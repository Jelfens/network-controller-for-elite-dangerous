from flask import Flask, jsonify, render_template, request as flask_request
import json
import os
import sys
import platform
import subprocess
import urllib.request
import urllib.error

# vJoy initialization (Windows only)
has_gamepad = False
gamepad = None
if sys.platform == 'win32':
    try:
        import pyvjoy
    except ImportError:
        pyvjoy = None

def initialize_vjoy(debug=True):
    global has_gamepad, gamepad
    if sys.platform != 'win32' or pyvjoy is None:
        return
    
    if debug and os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        return

    try:
        gamepad = pyvjoy.VJoyDevice(1)
        has_gamepad = True
        print("vJoy (Device 1) successfully initialized.")
    except Exception as e:
        if "VJD_STAT_FREE" in str(e):
            print(f"vJoy error: Device 1 already in use.")
        else:
            print(f"vJoy error: {e}")
            has_gamepad = False

import time
import threading

def vjoy_button_press(button_id):
    """Press and release a vJoy button asynchronously"""
    if not has_gamepad or gamepad is None:
        return
    try:
        gamepad.set_button(button_id, 1)
        time.sleep(0.1)
        gamepad.set_button(button_id, 0)
    except:
        pass

# Platform-specific input handling
if sys.platform == 'linux':
    def press_key(key):
        """Send keypress on Linux using xdotool"""
        try:
            subprocess.run(['xdotool', 'key', key], check=False)
        except FileNotFoundError:
            print("Error: xdotool not found.")
else:
    import pydirectinput
    def press_key(key):
        """Send keypress on Windows using pydirectinput"""
        try:
            pydirectinput.press(key)
        except:
            pass

app = Flask(__name__)

# Map commands to vJoy Buttons (1-58)
KOMUTLAR = {
    "wg-hardpoints": 1, "landing-gear": 2, "cargo-scoop": 3,
    "lights": 4, "night-vision": 5, "silent-running": 6,
    "fsd": 7, "heatsink": 8, "chaff": 9, "scb": 10,
    "galaxy-map": 11, "system-map": 12,
    "pip-sys": 13, "pip-eng": 14, "pip-wep": 15, "pip-rst": 16,
    "fg-prev": 17, "fg-next": 18, "menu": 19,
    "fss": 20, "cockpit-mode": 21,
    # Navigation & Menus
    "menu-up": 22, "menu-down": 23, "menu-left": 24, "menu-right": 25, "menu-select": 26,
    "tab-prev": 27, "tab-next": 28,
    # Speed & Thrusters
    "speed-0": 29, "speed-25": 30, "speed-50": 31, "speed-75": 32, "speed-100": 33,
    "throttle-inc": 34, "throttle-dec": 35,
    "thruster-up": 36, "thruster-down": 37,
    "boost": 38,
    # FSD Variants
    "fsd-sc": 39, "fsd-jump": 40,
    # Misc
    "rot-corr": 41, "orbit-lines": 42,
    # Targeting
    "target-ahead": 43, "target-next": 44, "target-highest": 45, "target-prev": 64, "target-hostile-next": 65, "target-hostile-prev": 66,
    "target-team-1": 46, "target-team-2": 47, "target-team-3": 48,
    "target-team-target": 49, "target-navlock": 50, "target-sub-next": 51, "target-sub-prev": 67, "target-route": 52,
    "ui-page-prev": 53, "ui-page-next": 54,
    "panel-external": 55, "panel-comms": 56, "panel-role": 57, "panel-internal": 58,
    "menu-back": 59,
    "speed-rev-25": 60, "speed-rev-50": 61, "speed-rev-75": 62, "speed-rev-100": 63,
    "menu-game": 68, "menu-social": 69, "discovery": 70,
    "fighter-recall": 71, "fighter-defend": 72, "fighter-engage": 73, "fighter-attack": 74,
    "fighter-formation": 75, "fighter-hold": 76, "fighter-follow": 77
}

# Keep original key map as fallback
FALLBACK_KEYS = {
    "wg-hardpoints": "u", "landing-gear": "l", "cargo-scoop": "home",
    "lights": "insert", "night-vision": "n", "silent-running": "delete",
    "fsd": "j", "heatsink": "v", "chaff": "c", "scb": "b",
    "galaxy-map": "m", "system-map": "o",
    "pip-sys": "left", "pip-eng": "up", "pip-wep": "right", "pip-rst": "down",
    "menu-up": "up", "menu-down": "down", "menu-left": "left", "menu-right": "right", "menu-select": "enter",
    "tab-prev": "q", "tab-next": "e", "boost": "tab", "menu-back": "backspace", "menu-game": "esc", "menu-social": "p", "discovery": "'",
    "fighter-recall": "numpad0", "fighter-defend": "numpad1", "fighter-engage": "numpad2", "fighter-attack": "numpad3",
    "fighter-formation": "numpad4", "fighter-hold": "numpad5", "fighter-follow": "numpad6"
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/action/<komut_adi>')
def action(komut_adi):
    if komut_adi in KOMUTLAR:
        btn_id = KOMUTLAR[komut_adi]
        # Always try vJoy if available
        if has_gamepad and gamepad:
            threading.Thread(target=vjoy_button_press, args=(btn_id,)).start()
            return "OK (vJoy)"
        
        # Fallback to keyboard if vJoy not available and fallback exists
        key = FALLBACK_KEYS.get(komut_adi)
        if key:
            press_key(key)
            return "OK (Keyboard)"
            
        return "OK (vJoy not active)"
    return "Hata", 400

@app.route('/axis/<axis_name>/<value>')
def handle_axis(axis_name, value):
    if not has_gamepad: return "No vJoy Device", 500
    try:
        val = int(value)
        # Convert -100...100 range to vJoy 0x0000...0x8000 (0 to 32768)
        # -100 -> 0, 0 -> 16384, 100 -> 32768
        axis_val = int(((val + 100) / 200.0) * 32768)
        axis_val = max(0, min(32768, axis_val)) # clamp
        
        if axis_name == 'vthrust':
            gamepad.set_axis(pyvjoy.HID_USAGE_Y, axis_val)
        elif axis_name == 'lthrust':
            gamepad.set_axis(pyvjoy.HID_USAGE_X, axis_val)
        elif axis_name == 'fthrust':
            gamepad.set_axis(pyvjoy.HID_USAGE_Z, axis_val)
        elif axis_name == 'sensorzoom':
            gamepad.set_axis(pyvjoy.HID_USAGE_RX, axis_val)


            
    except Exception as e:
        print(f"Axis error: {e}")
        return "Error", 500
    return "OK"

def get_latest_journal_info(path_dir):
    try:
        files = [f for f in os.listdir(path_dir) if f.startswith('Journal.') and f.endswith('.log')]
        if not files: return None
        latest_file = max(files, key=lambda x: os.path.getmtime(os.path.join(path_dir, x)))
        system, station, capacity = "Unknown", "", 32.0
        logs = []
        
        with open(os.path.join(path_dir, latest_file), 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Parse for status info (latest first)
            for line in reversed(lines):
                try:
                    data = json.loads(line)
                    event = data.get('event')
                    if event in ['Location', 'FSDJump'] and system == "Unknown":
                        system = data.get('StarSystem', system)
                        station = data.get('StationName', station)
                    elif event == 'Docked' and not station:
                        station = data.get('StationName', station)
                    elif event == 'LoadGame':
                        capacity = data.get('FuelCapacity', capacity)
                except: continue
            
            # Parse for logs (last 15 events)
            for line in lines[-50:]: # Look at last 50 lines to find 15 good events
                try:
                    data = json.loads(line)
                    event = data.get('event')
                    msg = ""
                    if event == 'FSDJump': msg = f"Jumped to {data.get('StarSystem')}"
                    elif event == 'Docked': msg = f"Docked at {data.get('StationName')}"
                    elif event == 'Undocked': msg = f"Undocked from {data.get('StationName')}"
                    elif event == 'Bounty': msg = f"Bounty claimed: {data.get('TotalReward'):,} CR"
                    elif event == 'CommitCrime': msg = f"CRIME: {data.get('CrimeType')}"
                    elif event == 'Died': msg = "SHIP DESTROYED"
                    elif event == 'ShieldState': msg = "Shields " + ("UP" if data.get('ShieldsUp') else "DOWN")
                    elif event == 'MarketBuy': msg = f"Bought {data.get('Count')} {data.get('Type')}"
                    
                    if msg:
                        time_str = data.get('timestamp')[11:16] # HH:MM
                        logs.append({"t": time_str, "m": msg.upper()})
                except: continue
                
        return {"System": system, "Station": station, "FuelCapacity": capacity, "Logs": logs[-10:]}
    except: return None

@app.route('/status')
def get_status():
    if sys.platform == 'linux':
        possible_paths = [
            os.path.expanduser("~/.steam/root/drive_c/users/steamuser/Saved Games/Frontier Developments/Elite Dangerous/"),
            os.path.expanduser("~/.steamapps/compatdata/626690/pfx/drive_c/users/steamuser/Saved Games/Frontier Developments/Elite Dangerous/"),
        ]
    else:
        possible_paths = [
            os.path.expanduser(r"~\Saved Games\Frontier Developments\Elite Dangerous\\"),
        ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                status_path = os.path.join(path, "Status.json")
                res = {}
                if os.path.exists(status_path):
                    with open(status_path, 'r', encoding='utf-8') as f:
                        res = json.load(f)
                
                journal_info = get_latest_journal_info(path)
                if journal_info:
                    res.update(journal_info)
                
                return jsonify(res)
            except Exception as e:
                return jsonify({"hata": str(e)})
    
    return jsonify({"hata": "Elite Dangerous data path not found."})



if __name__ == '__main__':
    initialize_vjoy(debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)

