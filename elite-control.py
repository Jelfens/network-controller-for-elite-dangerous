from flask import Flask, jsonify, render_template_string, request as flask_request
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

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>ED Control Panel</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        html, body { background-color: #050505; margin: 0; padding: 0; height: 100vh; overflow: hidden; }
        .ed-text { color: #ff8c00; }
        .ed-border { border-color: #ff8c00; }
        .ed-glow { text-shadow: 0 0 8px rgba(255,140,0,0.6); }
        .btn, .ind-btn {
            background-image: linear-gradient(180deg, rgba(255,255,255,0.07) 0%, transparent 40%, rgba(0,0,0,0.3) 100%);
            box-shadow: 0 3px 6px rgba(0,0,0,0.6), 0 1px 0 rgba(255,255,255,0.05) inset, 0 -2px 4px rgba(0,0,0,0.4) inset;
            transition: all 0.15s ease;
            position: relative;
        }
        .btn:active, .ind-btn:active {
            transform: translateY(2px) scale(0.97);
            box-shadow: 0 1px 2px rgba(0,0,0,0.5), 0 1px 0 rgba(255,255,255,0.03) inset;
        }
        .ind-off {
            border-color: #374151; color: #4B5563; background-color: #0a0a0a;
            box-shadow: 0 3px 6px rgba(0,0,0,0.6), 0 1px 0 rgba(255,255,255,0.05) inset, 0 -2px 4px rgba(0,0,0,0.4) inset;
        }
        .ind-on {
            border-color: #ff8c00; color: #ff8c00; background-color: rgba(255,140,0,0.08);
            box-shadow: 0 3px 8px rgba(0,0,0,0.5), 0 0 15px rgba(255,140,0,0.4), 0 0 15px rgba(255,140,0,0.3) inset, 0 1px 0 rgba(255,200,100,0.15) inset;
        }
        .ind-safe {
            border-color: #10B981; color: #10B981; background-color: rgba(16,185,129,0.08);
            box-shadow: 0 3px 8px rgba(0,0,0,0.5), 0 0 15px rgba(16,185,129,0.4), 0 0 15px rgba(16,185,129,0.3) inset, 0 1px 0 rgba(100,230,180,0.15) inset;
        }
        .fg-on { background-color: #ff8c00; color: #111827; border-color: #ff8c00; box-shadow: 0 3px 8px rgba(0,0,0,0.5), 0 0 12px rgba(255,140,0,0.6); }
        .fg-off { background-color: #111827; color: #4B5563; border-color: #374151; box-shadow: 0 2px 4px rgba(0,0,0,0.4); }
        .section-title {
            background: linear-gradient(90deg, rgba(255,140,0,0.15) 0%, rgba(0,0,0,0) 100%);
            border-left: 4px solid #ff8c00;
        }
        .page { display: none; }
        .page.active { display: flex; flex-direction: column; justify-content: space-evenly; min-height: 100%; flex: 1; }
        #page-nav.active { flex-direction: row; justify-content: flex-start; gap: 0.5rem; height: 100%; min-height: unset; flex: none; overflow: hidden; }
        #page-aux.active { justify-content: flex-start; }
        #page-landing.active { justify-content: flex-start; }
        .tab-btn { transition: all 0.2s; }
        .tab-btn.active {
            color: #ff8c00;
            border-color: #ff8c00;
            background: rgba(255,140,0,0.1);
            box-shadow: 0 -2px 10px rgba(255,140,0,0.3);
        }
        .tab-btn.active .tab-icon { filter: drop-shadow(0 0 4px rgba(255,140,0,0.6)); }
        
        /* Hide scrollbar completely but allow scrolling if absolutely necessary to prevent cutoff */
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
    </style>
</head>
<body class="text-gray-300 font-mono select-none flex flex-col h-screen tracking-tight overflow-hidden">

    <div class="flex-1 flex flex-col overflow-y-auto no-scrollbar p-2 pb-24">

        <!-- ==================== TARGETING MODAL ==================== -->
        <div id="modal-targeting" class="fixed inset-0 bg-[#050505]/98 z-[100] flex-col p-4 backdrop-blur-xl" style="display: none;">
            <!-- Header -->
            <div class="flex justify-between items-center mb-6 border-b-2 border-red-900/50 pb-3">
                <div class="flex items-center gap-3">
                    <div class="w-2 h-6 bg-red-600 shadow-[0_0_8px_rgba(220,38,38,0.5)]"></div>
                    <div class="text-red-500 font-black tracking-[0.2em] text-xl">TARGETING SYSTEMS</div>
                </div>
                <button onclick="document.getElementById('modal-targeting').style.display='none'" class="btn border-2 border-red-900 bg-red-900/30 text-red-500 rounded-full w-12 h-12 text-2xl font-black flex items-center justify-center shadow-[0_0_15px_rgba(220,38,38,0.3)] active:scale-90 transition-transform">×</button>
            </div>
            
            <!-- Main Content -->
            <div class="flex-1 flex flex-col gap-4 overflow-y-auto no-scrollbar">
                
                <!-- Primary Combat Targets -->
                <div class="grid grid-cols-2 gap-2">
                    <button onclick="komut('target-highest')" class="btn col-span-2 border-2 border-red-600 bg-red-900/40 text-red-100 rounded-xl p-3 text-lg font-black shadow-[0_0_10px_rgba(220,38,38,0.3)] tracking-widest active:scale-95 transition-transform">
                        <div class="text-[11px] text-red-400 mb-0.5 opacity-70">PRIORITY</div>
                        HIGHEST THREAT
                    </button>
                    <button onclick="komut('target-hostile-prev')" class="btn border-2 border-red-600 bg-red-900/40 text-red-100 rounded-xl p-3 text-lg font-black shadow-[0_0_10px_rgba(220,38,38,0.3)] tracking-widest active:scale-95 transition-transform">
                        <div class="text-[11px] text-red-400 mb-0.5 opacity-70">HOSTILE</div>
                        PREV HOSTILE
                    </button>
                    <button onclick="komut('target-hostile-next')" class="btn border-2 border-red-600 bg-red-900/40 text-red-100 rounded-xl p-3 text-lg font-black shadow-[0_0_10px_rgba(220,38,38,0.3)] tracking-widest active:scale-95 transition-transform">
                        <div class="text-[11px] text-red-400 mb-0.5 opacity-70">HOSTILE</div>
                        NEXT HOSTILE
                    </button>
                    
                    <button onclick="komut('target-ahead')" class="btn col-span-2 border-2 border-orange-700/50 bg-orange-900/20 text-orange-400 rounded-xl p-2.5 text-base font-bold shadow-md active:scale-95 transition-transform">
                        <div class="text-[10px] mb-0.5 opacity-70">AHEAD</div>
                        TARGET AHEAD
                    </button>
                    <button onclick="komut('target-prev')" class="btn border-2 border-red-800/50 bg-red-900/10 text-red-400 rounded-xl p-2.5 text-base font-bold shadow-md active:scale-95 transition-transform">
                        <div class="text-[10px] mb-0.5 opacity-70">CYCLE</div>
                        PREV TARGET
                    </button>
                    <button onclick="komut('target-next')" class="btn border-2 border-red-800/50 bg-red-900/10 text-red-400 rounded-xl p-2.5 text-base font-bold shadow-md active:scale-95 transition-transform">
                        <div class="text-[10px] mb-0.5 opacity-70">CYCLE</div>
                        NEXT TARGET
                    </button>
                </div>
                
                <!-- Team & Wing Operations -->
                <div class="bg-[#0a0a0a] p-3 rounded-xl border border-blue-900/30 relative mt-1">
                    <div class="absolute top-0 left-8 px-3 -mt-2 bg-[#050505] text-[9px] text-blue-500 font-black tracking-widest border border-blue-900/30 rounded-full">WING OPERATIONS</div>
                    
                    <div class="grid grid-cols-3 gap-1.5 mt-1">
                        <button onclick="komut('target-team-1')" class="btn border border-blue-800/50 bg-blue-900/10 text-blue-400 rounded-lg py-2 text-[10px] font-bold active:scale-95 transition-transform">WING 1</button>
                        <button onclick="komut('target-team-2')" class="btn border border-blue-800/50 bg-blue-900/10 text-blue-400 rounded-lg py-2 text-[10px] font-bold active:scale-95 transition-transform">WING 2</button>
                        <button onclick="komut('target-team-3')" class="btn border border-blue-800/50 bg-blue-900/10 text-blue-400 rounded-lg py-2 text-[10px] font-bold active:scale-95 transition-transform">WING 3</button>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-1.5 mt-1.5">
                        <button onclick="komut('target-team-target')" class="btn border border-blue-600/60 bg-blue-600/20 text-blue-100 rounded-lg py-2.5 text-[10px] font-black tracking-wider active:scale-95 transition-transform">WINGMAN TGT</button>
                        <button onclick="komut('target-navlock')" class="btn border border-cyan-600/60 bg-cyan-600/20 text-cyan-100 rounded-lg py-2.5 text-[10px] font-black tracking-wider active:scale-95 transition-transform">NAV LOCK</button>
                    </div>
                </div>
                
                <!-- Status Indicator at bottom -->
                <div class="mt-auto py-4 text-center border-t border-gray-900">
                    <div class="text-[10px] text-gray-600 font-black tracking-[0.5em] animate-pulse">SYSTEMS ONLINE // SCANNING...</div>
                </div>
            </div>
        </div>
        
        <!-- FIGHTERS MODAL -->
        <div id="modal-fighters" class="fixed inset-0 bg-[#050505]/95 z-50 hidden flex-col p-4 backdrop-blur-sm">
            <div class="flex justify-between items-center mb-4 border-b border-orange-900/50 pb-2">
                <div class="text-orange-500 font-black tracking-[0.3em] text-lg">FIGHTER ORDERS</div>
                <button onclick="document.getElementById('modal-fighters').style.display='none'" class="text-gray-500 hover:text-white transition-colors text-4xl leading-none">&times;</button>
            </div>
            
            <div class="flex-1 flex flex-col gap-4 overflow-y-auto no-scrollbar">
                
                <!-- COMBAT GROUP -->
                <div>
                    <div class="text-[10px] text-red-500 font-black tracking-widest uppercase mb-2 ml-1 opacity-70">Combat Operations</div>
                    <div class="grid grid-cols-2 gap-2">
                        <button onclick="komut('fighter-engage'); document.getElementById('modal-fighters').style.display='none'" class="btn border-2 border-orange-500 bg-orange-600 text-[#111] rounded-lg py-4 text-sm font-black shadow-lg active:scale-95 transition-transform">ENGAGE</button>
                        <button onclick="komut('fighter-attack'); document.getElementById('modal-fighters').style.display='none'" class="btn border-2 border-red-900/50 bg-red-900/10 text-red-500 rounded-lg py-4 text-sm font-black shadow-md active:scale-95 transition-transform">ATTACK</button>
                    </div>
                </div>

                <!-- FORMATION GROUP -->
                <div>
                    <div class="text-[10px] text-blue-500 font-black tracking-widest uppercase mb-2 ml-1 opacity-70">Positioning</div>
                    <div class="grid grid-cols-3 gap-2">
                        <button onclick="komut('fighter-follow'); document.getElementById('modal-fighters').style.display='none'" class="btn border border-gray-700 bg-gray-800/30 text-gray-300 rounded-lg py-3 text-xs font-bold active:scale-95 transition-transform">FOLLOW</button>
                        <button onclick="komut('fighter-hold'); document.getElementById('modal-fighters').style.display='none'" class="btn border border-gray-700 bg-gray-800/30 text-gray-300 rounded-lg py-3 text-xs font-bold active:scale-95 transition-transform">HOLD</button>
                        <button onclick="komut('fighter-formation'); document.getElementById('modal-fighters').style.display='none'" class="btn border border-gray-700 bg-gray-800/30 text-gray-300 rounded-lg py-3 text-xs font-bold active:scale-95 transition-transform">STAY</button>
                    </div>
                </div>

                <!-- SUPPORT GROUP -->
                <div>
                    <div class="text-[10px] text-green-500 font-black tracking-widest uppercase mb-2 ml-1 opacity-70">Support</div>
                    <div class="grid grid-cols-2 gap-2">
                        <button onclick="komut('fighter-defend'); document.getElementById('modal-fighters').style.display='none'" class="btn border border-green-900/50 bg-green-900/10 text-green-500 rounded-lg py-3 text-sm font-bold active:scale-95 transition-transform">DEFEND</button>
                        <button onclick="komut('fighter-recall'); document.getElementById('modal-fighters').style.display='none'" class="btn border border-orange-900/50 bg-orange-900/10 text-orange-400 rounded-lg py-3 text-sm font-bold active:scale-95 transition-transform">RECALL</button>
                    </div>
                </div>

                <button onclick="komut('panel-role'); document.getElementById('modal-fighters').style.display='none'" class="btn mt-auto border border-gray-700 bg-[#0a0a0a] text-gray-500 rounded-lg py-3 text-[10px] font-black tracking-widest uppercase active:scale-95 transition-transform">OPEN ROLE PANEL</button>
            </div>
        </div>
        
        <!-- ==================== SAVAŞ (COMBAT) ==================== -->
        <div id="page-combat" class="page active min-h-full">

            <div class="grid grid-cols-4 gap-2 text-center text-sm font-bold mb-4">
                <div id="ind-hardp" onclick="komut('wg-hardpoints')" class="ind-btn cursor-pointer border rounded p-3 ind-off transition-all"><div class="text-xl mb-1">⚙️</div>HARDPOINTS</div>
                <button onclick="komut('cockpit-mode')" class="btn border border-gray-800 bg-[#0a0a0a] text-indigo-400 rounded p-3 hover:border-indigo-400 hover:shadow-[0_0_10px_rgba(129,140,248,0.2)]"><div class="text-xl mb-1">🖥️</div>HUD MODE</button>
                <div id="ind-silent" onclick="komut('silent-running')" class="ind-btn cursor-pointer border rounded p-3 ind-off transition-all"><div class="text-xl mb-1">🤫</div>SILENT RUN</div>
                <button onclick="document.getElementById('modal-targeting').style.display='flex'" class="btn border border-red-800 bg-red-900/20 text-red-500 rounded p-3 hover:border-red-500 hover:shadow-[0_0_10px_rgba(239,68,68,0.3)]"><div class="text-xl mb-1">🎯</div>TARGETING</button>
            </div>


            <div class="bg-[#0a0a0a] p-3 rounded border border-gray-800 shadow-[0_0_15px_rgba(0,0,0,0.5)] inset mb-4">
                <div class="grid grid-cols-3 gap-3">
                    <div class="flex flex-col">
                        <div class="text-blue-500 text-[10px] font-black text-center mb-1 tracking-widest">SYS</div>
                        <div class="flex justify-center gap-1 mb-2 min-h-[8px]" id="bar-sys"></div>
                        <button onclick="komut('pip-sys')" class="btn w-full border border-gray-800 bg-gray-900 text-blue-500 rounded p-2 text-lg font-bold hover:border-blue-500 hover:shadow-[0_0_10px_rgba(59,130,246,0.3)]">+</button>
                    </div>
                    <div class="flex flex-col">
                        <div class="text-green-500 text-[10px] font-black text-center mb-1 tracking-widest">ENG</div>
                        <div class="flex justify-center gap-1 mb-2 min-h-[8px]" id="bar-eng"></div>
                        <button onclick="komut('pip-eng')" class="btn w-full border border-gray-800 bg-gray-900 text-green-500 rounded p-2 text-lg font-bold hover:border-green-500 hover:shadow-[0_0_10px_rgba(34,197,94,0.3)]">+</button>
                    </div>
                    <div class="flex flex-col">
                        <div class="text-red-500 text-[10px] font-black text-center mb-1 tracking-widest">WEP</div>
                        <div class="flex justify-center gap-1 mb-2 min-h-[8px]" id="bar-wep"></div>
                        <button onclick="komut('pip-wep')" class="btn w-full border border-gray-800 bg-gray-900 text-red-500 rounded p-2 text-lg font-bold hover:border-red-500 hover:shadow-[0_0_10px_rgba(239,68,68,0.3)]">+</button>
                    </div>
                </div>
                <button onclick="komut('pip-rst')" class="btn w-full mt-2 border border-gray-800 bg-[#0f0f0f] text-gray-500 rounded p-2 text-xs font-black hover:border-gray-500 tracking-[0.3em]">↩ RESET PIPS</button>
            </div>

            <div class="grid grid-cols-4 gap-2 mb-4 text-xs font-bold">
                <button onclick="komut('heatsink')" class="btn border border-gray-800 bg-[#0a0a0a] text-blue-500 rounded p-3 hover:border-blue-500 hover:shadow-[0_0_10px_rgba(59,130,246,0.2)]"><div class="text-base mb-1">🧊</div>HEATSINK</button>
                <button onclick="komut('chaff')" class="btn border border-gray-800 bg-[#0a0a0a] text-yellow-500 rounded p-3 hover:border-yellow-500 hover:shadow-[0_0_10px_rgba(234,179,8,0.2)]"><div class="text-base mb-1">✨</div>CHAFF</button>
                <button onclick="komut('scb')" class="btn border border-gray-800 bg-[#0a0a0a] text-teal-400 rounded p-3 hover:border-teal-400 hover:shadow-[0_0_10px_rgba(45,212,191,0.2)]"><div class="text-base mb-1">🔋</div>SHIELD CELL</button>
                <button onclick="document.getElementById('modal-fighters').style.display='flex'" class="btn border border-orange-800 bg-orange-900/20 text-orange-500 rounded p-3 hover:border-orange-500 hover:shadow-[0_0_10px_rgba(249,115,22,0.2)]"><div class="text-base mb-1">🚀</div>FIGHTERS</button>
            </div>


            <div class="bg-[#0a0a0a] p-3 rounded border border-gray-800">
                <div class="flex items-center justify-between gap-2">
                    <button onclick="komut('fg-prev')" class="btn bg-[#0f0f0f] border border-gray-800 text-gray-400 rounded px-3 py-1 font-black text-lg hover:text-white">&lt;</button>
                    <div class="flex flex-1 justify-between" id="fg-strip">
                        <div id="fg-0" class="border w-6 h-6 flex items-center justify-center text-xs font-bold rounded fg-off transition-all">A</div>
                        <div id="fg-1" class="border w-6 h-6 flex items-center justify-center text-xs font-bold rounded fg-off transition-all">B</div>
                        <div id="fg-2" class="border w-6 h-6 flex items-center justify-center text-xs font-bold rounded fg-off transition-all">C</div>
                        <div id="fg-3" class="border w-6 h-6 flex items-center justify-center text-xs font-bold rounded fg-off transition-all">D</div>
                        <div id="fg-4" class="border w-6 h-6 flex items-center justify-center text-xs font-bold rounded fg-off transition-all">E</div>
                        <div id="fg-5" class="border w-6 h-6 flex items-center justify-center text-xs font-bold rounded fg-off transition-all">F</div>
                        <div id="fg-6" class="border w-6 h-6 flex items-center justify-center text-xs font-bold rounded fg-off transition-all">G</div>
                        <div id="fg-7" class="border w-6 h-6 flex items-center justify-center text-xs font-bold rounded fg-off transition-all">H</div>
                    </div>
                    <button onclick="komut('fg-next')" class="btn bg-[#0f0f0f] border border-gray-800 text-gray-400 rounded px-3 py-1 font-black text-lg hover:text-white">&gt;</button>
                </div>
            </div>
        </div>

        <!-- ==================== SEYİR (NAVIGATION) ==================== -->
        <!-- ==================== SEYİR (NAVIGATION) ==================== -->
        <div id="page-nav" class="page h-full p-1 flex-row">
            <div class="flex-1 grid min-w-0 gap-1" style="grid-template-rows: 2fr 5fr 1.5fr; height: 100%;">
            
            <!-- TOP ROW: FSD | COM | Maps -->
            <div class="grid grid-cols-3 gap-2 min-h-0 overflow-hidden">
                <!-- FSD Box -->
                <div class="bg-[#050505] p-1 rounded-xl border border-orange-900/30 relative shadow-md flex flex-col justify-center overflow-hidden">
                    <div class="absolute top-0 left-3 px-1 -mt-2 bg-[#050505] text-[10px] text-orange-600 font-black tracking-widest uppercase">FSD</div>
                    <div class="grid grid-cols-2 gap-1 h-full">
                        <button onclick="komut('fsd-jump')" class="btn h-full border border-orange-700/50 bg-orange-900/10 text-orange-400 rounded text-[10px] font-bold flex flex-col items-center justify-center">
                            <span class="text-base leading-none">🚀</span>
                            HYP
                        </button>
                        <button onclick="komut('fsd-sc')" class="btn h-full border border-orange-700/50 bg-orange-900/10 text-orange-400 rounded text-[10px] font-bold flex flex-col items-center justify-center">
                            <span class="text-base leading-none">⚡</span>
                            SUP
                        </button>
                        <button onclick="komut('fsd')" class="btn col-span-2 h-full border border-gray-700 bg-[#0a0a0a] text-gray-400 rounded text-[11px] font-black uppercase flex items-center justify-center gap-1">
                            <span class="text-base leading-none">🌀</span>
                            FSD
                        </button>
                    </div>
                </div>

                <!-- Center: COM -->
                <button onclick="komut('panel-comms')" class="btn w-full h-full border-2 border-blue-900/50 bg-blue-900/10 text-blue-400 rounded-xl text-[14px] font-black shadow-lg flex flex-col items-center justify-center">
                    <span class="text-2xl leading-none">📡</span>
                    COM
                </button>

                <!-- Maps Box -->
                <div class="bg-[#050505] p-1 rounded-xl border border-blue-900/30 relative shadow-md flex flex-col overflow-hidden">
                    <div class="absolute top-0 right-3 px-1 -mt-2 bg-[#050505] text-[10px] text-blue-500 font-black tracking-widest uppercase">Maps</div>
                    <div class="grid grid-cols-2 gap-px flex-1 min-h-0">
                        <button onclick="komut('target-sub-prev')" class="btn h-full border border-gray-700 bg-[#0a0a0a] text-gray-400 rounded text-[9px] font-bold flex flex-col items-center justify-center leading-none">
                            <span class="text-sm leading-none">🎯◀</span>
                            PREV SUB
                        </button>
                        <button onclick="komut('target-sub-next')" class="btn h-full border border-gray-700 bg-[#0a0a0a] text-gray-400 rounded text-[9px] font-bold flex flex-col items-center justify-center leading-none">
                            <span class="text-sm leading-none">🎯▶</span>
                            NEXT SUB
                        </button>
                        <button onclick="komut('system-map')" class="btn h-full border border-blue-800/50 bg-blue-900/10 text-blue-400 rounded text-[9px] font-bold flex flex-col items-center justify-center leading-none">
                            <span class="text-sm leading-none">🪐</span>
                            SYS
                        </button>
                        <button onclick="komut('galaxy-map')" class="btn h-full border border-blue-800/50 bg-blue-900/10 text-blue-400 rounded text-[9px] font-bold flex flex-col items-center justify-center leading-none">
                            <span class="text-sm leading-none">🌌</span>
                            GAL
                        </button>
                        <button onclick="komut('target-route')" class="btn col-span-2 h-full border border-orange-900/40 bg-orange-900/10 text-orange-400 rounded text-[9px] font-bold flex flex-row items-center justify-center gap-1 leading-none">
                            <span class="text-sm leading-none">🚩</span>
                            NEXT SYS ON ROUTE
                        </button>
                    </div>
                </div>
            </div>

            <!-- MIDDLE ROW: <TAB | EXT | D-PAD | INT | TAB> -->
            <div class="flex items-stretch justify-between gap-1 min-h-0 overflow-hidden">
                <button onclick="komut('tab-prev')" class="btn flex-1 border border-gray-600 bg-gray-800 text-white rounded-xl text-[12px] font-black flex flex-col items-center justify-center">
                    <span class="text-xl leading-none">◀️</span>
                    TAB
                </button>
                <button onclick="komut('panel-external')" class="btn flex-[1.5] border border-orange-900/50 bg-orange-900/10 text-orange-500 rounded-xl text-[14px] font-black flex flex-col items-center justify-center">
                    <span class="text-3xl leading-none">🛰️</span>
                    EXT
                </button>

                <!-- D-PAD -->
                <div class="flex-[3] grid grid-cols-3 gap-1 bg-[#0a0a0a] p-1.5 rounded-2xl border-2 border-gray-800 shadow-inner overflow-hidden">
                    <div></div>
                    <button onclick="komut('menu-up')" class="btn w-full h-full border border-gray-600 bg-gray-800 rounded-lg text-2xl">▲</button>
                    <div></div>
                    <button onclick="komut('menu-left')" class="btn w-full h-full border border-gray-600 bg-gray-800 rounded-lg text-2xl">◀</button>
                    <button onclick="komut('menu-select')" class="btn w-full h-full border-2 border-orange-500 bg-orange-900/30 text-orange-400 rounded-lg font-black text-lg flex flex-col items-center justify-center">
                        <span class="text-xl leading-none">✅</span>
                        OK
                    </button>
                    <button onclick="komut('menu-right')" class="btn w-full h-full border border-gray-600 bg-gray-800 rounded-lg text-2xl">▶</button>
                    <button onclick="komut('menu-back')" class="btn w-full h-full border border-gray-600 bg-gray-800 rounded-lg text-xl flex items-center justify-center">↩️</button>
                    <button onclick="komut('menu-down')" class="btn w-full h-full border border-gray-600 bg-gray-800 rounded-lg text-2xl">▼</button>
                    <div></div>
                </div>

                <button onclick="komut('panel-internal')" class="btn flex-[1.5] border border-orange-900/50 bg-orange-900/10 text-orange-500 rounded-xl text-[14px] font-black flex flex-col items-center justify-center">
                    <span class="text-3xl leading-none">🖥️</span>
                    INT
                </button>
                <button onclick="komut('tab-next')" class="btn flex-1 border border-gray-600 bg-gray-800 text-white rounded-xl text-[12px] font-black flex flex-col items-center justify-center">
                    <span class="text-xl leading-none">▶️</span>
                    TAB
                </button>
            </div>

            <!-- BOTTOM ROW: PAGE | FSS | ROLE | AUX -->
            <div class="grid grid-cols-4 gap-2 min-h-0 overflow-hidden">
                <div class="flex flex-col gap-1 overflow-hidden">
                    <button onclick="komut('ui-page-prev')" class="btn flex-1 border border-gray-700 bg-[#0a0a0a] text-gray-500 rounded text-[10px] font-black flex items-center justify-center gap-1">
                        <span>🔼</span> UP
                    </button>
                    <button onclick="komut('ui-page-next')" class="btn flex-1 border border-gray-700 bg-[#0a0a0a] text-gray-500 rounded text-[10px] font-black flex items-center justify-center gap-1">
                        <span>🔽</span> DOWN
                    </button>
                </div>
                <button onclick="komut('fss')" class="btn w-full h-full border-2 border-orange-900/50 bg-orange-900/10 text-orange-400 rounded-xl text-[13px] font-black shadow-lg flex flex-col items-center justify-center">
                    <span class="text-2xl leading-none">🔭</span>
                    FSS
                </button>
                <button onclick="komut('panel-role')" class="btn w-full h-full border-2 border-blue-900/50 bg-blue-900/10 text-blue-400 rounded-xl text-[13px] font-black shadow-lg flex flex-col items-center justify-center">
                    <span class="text-2xl leading-none">👥</span>
                    ROLE
                </button>
                <button onclick="switchPage('aux')" class="btn w-full h-full border-2 border-gray-600 bg-gray-800 text-gray-300 rounded-xl text-[13px] font-black shadow-lg flex flex-col items-center justify-center">
                    <span class="text-2xl leading-none">🛠️</span>
                    AUX
                </button>
            </div>
            </div>



            <!-- RIGHT SIDE: SPEED COLUMN -->
            <div class="w-16 flex flex-col gap-1 bg-[#050505] p-1 rounded-xl border border-cyan-900/30 shadow-md shrink-0 h-full">
                <button onclick="komut('boost')" class="btn flex-[1.5] border-2 border-cyan-600 bg-cyan-900/30 text-cyan-400 rounded-md text-[13px] font-black tracking-wider shadow-[0_0_15px_rgba(8,145,178,0.4)] transition-all active:scale-95">BOOST</button>
                <button onclick="komut('throttle-inc')" class="btn flex-1 border border-gray-700 bg-gray-800 text-gray-300 rounded-md text-[12px] font-bold active:scale-95">TH +</button>
                <div class="flex-[6] flex flex-col gap-0.5">
                    <button onclick="komut('speed-100')" class="btn flex-1 border border-green-900/60 bg-green-900/10 text-green-500 rounded-md text-[13px] font-black active:scale-95">100%</button>
                    <button onclick="komut('speed-75')" class="btn flex-1 border border-orange-900/60 bg-orange-900/10 text-orange-400 rounded-md text-[13px] font-black active:scale-95">75%</button>
                    <button onclick="komut('speed-50')" class="btn flex-1 border border-blue-900/60 bg-blue-900/10 text-blue-400 rounded-md text-[13px] font-black active:scale-95">50%</button>
                    <button onclick="komut('speed-25')" class="btn flex-1 border border-gray-800 bg-gray-900 text-gray-300 rounded-md text-[13px] font-black active:scale-95">25%</button>
                    <button onclick="komut('speed-0')" class="btn flex-1 border border-red-900/60 bg-red-900/10 text-red-500 rounded-md text-[13px] font-black active:scale-95">0%</button>
                    <button onclick="komut('speed-rev-25')" class="btn flex-1 border border-gray-800 bg-gray-900 text-gray-400 rounded-md text-[13px] font-black active:scale-95">-25%</button>
                    <button onclick="komut('speed-rev-50')" class="btn flex-1 border border-purple-900/60 bg-purple-900/10 text-purple-400 rounded-md text-[13px] font-black active:scale-95">-50%</button>
                    <button onclick="komut('speed-rev-75')" class="btn flex-1 border border-purple-900/60 bg-purple-900/20 text-purple-300 rounded-md text-[13px] font-black active:scale-95">-75%</button>
                    <button onclick="komut('speed-rev-100')" class="btn flex-1 border border-pink-900/60 bg-pink-900/20 text-pink-500 rounded-md text-[13px] font-black active:scale-95">-100%</button>
                </div>
                <button onclick="komut('throttle-dec')" class="btn flex-1 border border-gray-700 bg-gray-800 text-gray-300 rounded-md text-[12px] font-bold active:scale-95">TH -</button>
            </div>
        </div>


        <!-- ==================== AUX ==================== -->
        <div id="page-aux" class="page min-h-full p-3">
            <div class="flex flex-row gap-3 h-full w-full flex-1 min-h-0">
                <!-- Left: Buttons & Utilities -->
                <div class="flex-1 flex flex-col gap-3 min-w-0 overflow-y-auto no-scrollbar pb-2">
                    <div class="grid grid-cols-2 gap-2">
                        <div id="ind-cargo" onclick="komut('cargo-scoop')" class="ind-btn cursor-pointer border-2 rounded-xl py-3 text-xs font-black ind-off transition-all text-center flex flex-col items-center justify-center">
                            <span class="text-3xl mb-1">📦</span>CARGO SCOOP
                        </div>
                        <div id="ind-light" onclick="komut('lights')" class="ind-btn cursor-pointer border-2 rounded-xl py-3 text-xs font-black ind-off transition-all text-center flex flex-col items-center justify-center">
                            <span class="text-3xl mb-1">💡</span>LIGHTS
                        </div>
                        <div id="ind-nv" onclick="komut('night-vision')" class="ind-btn cursor-pointer border-2 rounded-xl py-3 text-xs font-black ind-off transition-all text-center flex flex-col items-center justify-center">
                            <span class="text-3xl mb-1">👁️</span>NIGHT VISION
                        </div>
                        <button onclick="switchPage('landing')" class="btn border-2 border-orange-900/50 bg-orange-900/10 text-orange-500 rounded-xl py-3 text-xs font-black transition-all text-center flex flex-col items-center justify-center active:scale-95">
                            <span class="text-3xl mb-1">⚓</span>LANDING
                        </button>
                        <button onclick="komut('fss')" class="btn border-2 border-orange-900/50 bg-orange-900/10 text-orange-400 rounded-xl py-3 text-xs font-black transition-all text-center flex flex-col items-center justify-center active:scale-95">
                            <span class="text-3xl mb-1">🔭</span>FSS
                        </button>
                        <button onclick="switchPage('nav')" class="btn border-2 border-gray-700 bg-gray-800/20 text-gray-400 rounded-xl py-3 text-xs font-black transition-all text-center flex flex-col items-center justify-center active:scale-95">
                            <span class="text-3xl mb-1">◀</span>NAV
                        </button>
                    </div>

                    <div class="flex flex-col gap-2 mt-2">
                        <div class="text-[11px] text-orange-600 font-black tracking-[0.3em] uppercase border-b border-orange-900/20 pb-1">Utilities</div>
                        <div class="grid grid-cols-1 gap-2">
                            <button onclick="komut('rot-corr')" class="btn border border-gray-700 bg-[#0a0a0a] text-gray-300 rounded-xl py-3 text-[12px] font-black uppercase">Rotation Correction</button>
                            <button onclick="komut('orbit-lines')" class="btn border border-gray-700 bg-[#0a0a0a] text-gray-300 rounded-xl py-3 text-[12px] font-black uppercase">Orbit Lines</button>
                        </div>
                    </div>
                </div>

                <!-- Right: Sensor Zoom Full Height -->
                <div class="w-20 flex flex-col gap-1 shrink-0 h-full">
                    <div class="text-[10px] text-blue-500 font-black text-center uppercase tracking-widest">ZOOM</div>
                    <div class="flex-1 bg-[#0a0a0a] rounded-xl border border-blue-900/20 relative p-1 shadow-inner min-h-0">
                        <div id="zoom-pad" class="relative h-full w-full bg-[#050505] border-2 border-blue-900/40 rounded-lg overflow-hidden cursor-ns-resize touch-none">
                            <div class="absolute inset-0 flex flex-col items-center justify-center opacity-20 pointer-events-none">
                                <div class="w-full h-[1px] bg-blue-500/50"></div>
                            </div>
                            <div id="zoom-handle" class="absolute left-1/2 w-12 h-5 bg-blue-500 rounded-sm shadow-[0_0_15px_rgba(59,130,246,0.8)] -translate-x-1/2 -translate-y-1/2 pointer-events-none transition-[top] duration-75" style="top: 50%;"></div>
                            <div class="absolute top-2 left-1/2 -translate-x-1/2 text-[8px] text-blue-500 font-black opacity-40 uppercase">MAX</div>
                            <div class="absolute bottom-2 left-1/2 -translate-x-1/2 text-[8px] text-blue-500 font-black opacity-40 uppercase">MIN</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>



        <!-- ==================== BİLGİ (INFO) ==================== -->
        <div id="page-info" class="page min-h-full">

            <div class="grid grid-cols-2 gap-2 mb-4">
                <div class="bg-[#050505] border border-orange-900/50 rounded p-3 text-center relative overflow-hidden">
                    <div class="absolute inset-0 bg-gradient-to-t from-orange-900/10 to-transparent"></div>
                    <div class="text-gray-500 text-[12px] font-black uppercase tracking-[0.2em] mb-1 relative z-10">Balance</div>
                    <div id="txt-cr" class="ed-text text-xl font-black tracking-wider relative z-10 ed-glow">- CR</div>
                </div>
                <div class="bg-[#050505] border border-orange-900/50 rounded p-3 text-center relative overflow-hidden">
                    <div class="absolute inset-0 bg-gradient-to-t from-orange-900/10 to-transparent"></div>
                    <div class="text-gray-500 text-[12px] font-black uppercase tracking-[0.2em] mb-1 relative z-10">Cargo</div>
                    <div id="txt-cargo" class="ed-text text-xl font-black tracking-wider relative z-10 ed-glow">- T</div>
                </div>
            </div>

            <div class="grid grid-cols-2 gap-3 text-[12px] text-gray-400 font-bold tracking-wider mb-4">
                <div class="bg-[#0a0a0a] p-2 rounded border border-gray-800">
                    <div class="text-white font-black mb-2 border-b border-gray-800 pb-1 tracking-widest">FLIGHT DATA</div>
                    <div class="flex justify-between mb-1"><span>DEST:</span><span id="txt-dest" class="ed-text">-</span></div>
                    <div class="flex justify-between mb-1"><span>BODY:</span><span id="txt-body" class="ed-text">-</span></div>
                    <div class="flex justify-between mb-1"><span>FOCUS:</span><span id="txt-gui" class="ed-text">-</span></div>
                    <div class="flex justify-between"><span>FUEL:</span><span id="txt-fuel-main" class="ed-text">-</span></div>
                </div>
                <div class="bg-[#0a0a0a] p-2 rounded border border-gray-800">
                    <div class="text-white font-black mb-2 border-b border-gray-800 pb-1 tracking-widest">SURFACE (SFC)</div>
                    <div class="flex justify-between mb-1"><span>LAT:</span><span id="txt-lat" class="ed-text">-</span></div>
                    <div class="flex justify-between mb-1"><span>LON:</span><span id="txt-lon" class="ed-text">-</span></div>
                    <div class="flex justify-between mb-1"><span>ALT:</span><span id="txt-alt" class="ed-text">-</span></div>
                    <div class="flex justify-between"><span>HDG:</span><span id="txt-hdg" class="ed-text">-</span></div>
                </div>
            </div>

            <div class="text-center text-2xl font-black text-gray-600 tracking-[0.2em] mb-4" id="sys-clock">00:00:00 LOC</div>

            <!-- SYSTEM CONTROLS / MENU -->
            <div class="flex justify-end gap-2 p-2">
                <button onclick="komut('discovery')" class="btn border-2 border-orange-900/40 bg-orange-900/10 text-orange-400 rounded-xl px-4 py-3 font-black shadow-lg flex flex-col items-center justify-center transition-all active:scale-95">
                    <span class="text-2xl mb-1">🔭</span>
                    DISCOVERY
                </button>
                <button onclick="komut('menu-social')" class="btn border-2 border-blue-900/40 bg-blue-900/10 text-blue-400 rounded-xl px-4 py-3 font-black shadow-lg flex flex-col items-center justify-center transition-all active:scale-95">
                    <span class="text-2xl mb-1">👥</span>
                    FRIENDS
                </button>
                <button onclick="komut('menu-game')" class="btn border-2 border-red-900/40 bg-red-900/10 text-red-500 rounded-xl px-4 py-3 font-black shadow-lg flex flex-col items-center justify-center transition-all active:scale-95">
                    <span class="text-2xl mb-1">⚙️</span>
                    GAME MENU
                </button>
            </div>
        </div>

        <!-- ==================== İNİŞ (LANDING) ==================== -->
        <div id="page-landing" class="page min-h-full">
            <div class="flex-1 flex flex-col gap-4 p-2">
                
                <!-- LANDING STATUS -->
                <div class="w-full">
                    <div id="ind-gear" onclick="komut('landing-gear')" class="ind-btn cursor-pointer border-2 rounded-xl py-8 text-lg font-black ind-off transition-all text-center flex flex-col items-center justify-center shadow-lg">
                        <span class="text-5xl mb-2">⚓</span>
                        LANDING GEAR
                    </div>
                </div>


                <!-- DUAL PAD CONTROLS -->
                <div class="flex-1 flex gap-3 min-h-0 bg-[#050505] p-3 rounded-2xl border border-blue-900/20 relative shadow-inner">
                    <div class="absolute top-0 left-6 px-3 -mt-2 bg-[#050505] text-[13px] text-blue-500 font-black tracking-widest uppercase">Precision Thrust Control</div>
                    
                    <!-- Vertical Pad (Wider) -->
                    <div class="flex flex-col gap-2 w-20">
                        <div id="v-pad" class="relative flex-1 bg-[#0a0a0a] border-2 border-blue-900/40 rounded-xl overflow-hidden cursor-ns-resize touch-none">
                            <div class="absolute inset-0 flex items-center justify-center opacity-20 pointer-events-none">
                                <div class="w-full h-[1px] bg-blue-500/50"></div>
                            </div>
                            <div id="v-handle" class="absolute left-1/2 w-14 h-3 bg-blue-500 rounded-full shadow-[0_0_15px_rgba(59,130,246,0.8)] -translate-x-1/2 -translate-y-1/2 pointer-events-none transition-[top] duration-75" style="top: 50%;"></div>
                            <div class="absolute top-2 left-1/2 -translate-x-1/2 text-[11px] text-blue-500 font-black opacity-40 uppercase">UP</div>
                            <div class="absolute bottom-2 left-1/2 -translate-x-1/2 text-[11px] text-blue-500 font-black opacity-40 uppercase">DOWN</div>
                        </div>
                        <button onclick="resetVertical()" class="py-2 bg-red-900/10 border border-red-900/40 text-red-500 text-[12px] font-black rounded-lg uppercase active:scale-95 transition-all">RESET V</button>
                    </div>

                    <!-- Lateral/Forward Pad -->
                    <div class="flex flex-col gap-2 flex-1">
                        <div id="lf-pad" class="relative flex-1 bg-[#0a0a0a] border-2 border-blue-900/40 rounded-xl overflow-hidden cursor-crosshair touch-none">
                            <div class="absolute inset-0 flex items-center justify-center opacity-20 pointer-events-none">
                                <div class="w-full h-[1px] bg-blue-500/30"></div>
                                <div class="h-full w-[1px] bg-blue-500/30"></div>
                            </div>
                            <div id="lf-handle" class="absolute w-7 h-7 bg-blue-500 rounded-full shadow-[0_0_15px_rgba(59,130,246,0.9)] -translate-x-1/2 -translate-y-1/2 pointer-events-none transition-[left,top] duration-75" style="left: 50%; top: 50%;"></div>
                            <div class="absolute top-2 left-1/2 -translate-x-1/2 text-[11px] text-blue-500 font-black opacity-40 uppercase">FWD</div>
                            <div class="absolute bottom-2 left-1/2 -translate-x-1/2 text-[11px] text-blue-500 font-black opacity-40 uppercase">BCK</div>
                            <div class="absolute top-1/2 left-2 -translate-y-1/2 text-[11px] text-blue-500 font-black opacity-40 uppercase -rotate-90">LEFT</div>
                            <div class="absolute top-1/2 right-2 -translate-y-1/2 text-[11px] text-blue-500 font-black opacity-40 uppercase rotate-90">RIGHT</div>
                        </div>
                    </div>
                </div>

                <div class="py-2 text-center">
                    <div class="text-[12px] text-gray-600 font-black tracking-[0.4em] uppercase animate-pulse">Docking protocols active</div>
                </div>

                <button onclick="switchPage('nav')" class="w-full py-3 bg-orange-900/20 border border-orange-800/50 text-orange-500 text-[12px] font-black rounded-xl uppercase tracking-widest">&lt; BACK TO NAV</button>
            </div>
        </div>




    </div>

    <!-- ==================== TAB BAR ==================== -->
    <div class="fixed bottom-0 left-0 right-0 bg-[#0a0a0a] border-t border-gray-800 grid grid-cols-3 text-center z-50">
        <button onclick="switchPage('combat')" id="tab-combat" class="tab-btn active py-3 border-t-2 border-transparent">
            <div class="tab-icon text-lg mb-0.5">⚔</div>
            <div class="text-[10px] font-black tracking-widest">COMBAT</div>
        </button>
        <button onclick="switchPage('nav')" id="tab-nav" class="tab-btn py-3 border-t-2 border-transparent text-gray-600">
            <div class="tab-icon text-lg mb-0.5">✦</div>
            <div class="text-[10px] font-black tracking-widest">NAV</div>
        </button>
        <button onclick="switchPage('info')" id="tab-info" class="tab-btn py-3 border-t-2 border-transparent text-gray-600">
            <div class="tab-icon text-lg mb-0.5">◈</div>
            <div class="text-[10px] font-black tracking-widest">INFO</div>
        </button>
    </div>



    <script>
        let lateral = 0;
        let vertical = 0;
        let forward = 0;

        function updateVertical(y) {
            vertical = Math.max(-100, Math.min(100, y));
            const handle = document.getElementById('v-handle');
            if (handle) handle.style.top = ((100 - vertical) / 2) + '%';
            fetch('/axis/vthrust/' + Math.round(vertical));
        }

        function updateLateralForward(x, y) {
            lateral = Math.max(-100, Math.min(100, x));
            forward = Math.max(-100, Math.min(100, y));
            const handle = document.getElementById('lf-handle');
            if (handle) {
                handle.style.left = ((lateral + 100) / 2) + '%';
                handle.style.top = ((100 - forward) / 2) + '%';
            }
            fetch('/axis/lthrust/' + Math.round(lateral));
            fetch('/axis/fthrust/' + Math.round(forward));
        }

        function updateZoom(y) {
            let val = Math.max(-100, Math.min(100, y));
            const handle = document.getElementById('zoom-handle');
            if (handle) handle.style.top = ((100 - val) / 2) + '%';
            fetch('/axis/sensorzoom/' + Math.round(val));
        }

        function resetVertical() {
            updateVertical(0);
        }

        function resetLateralForward() {
            updateLateralForward(0, 0);
        }

        function resetThrusters() {
            resetVertical();
            resetLateralForward();
        }


        document.addEventListener('DOMContentLoaded', () => {
            const vPad = document.getElementById('v-pad');
            const lfPad = document.getElementById('lf-pad');
            if (!vPad || !lfPad) return;

            const setupPad = (el, updateFn, is2D, autoCenter, resetFn) => {
                let isDragging = false;
                const move = (e) => {
                    if (!isDragging) return;
                    const rect = el.getBoundingClientRect();
                    const touch = e.touches ? e.touches[0] : e;
                    let x = ((touch.clientX - rect.left) / rect.width) * 200 - 100;
                    let y = 100 - ((touch.clientY - rect.top) / rect.height) * 200;
                    if (is2D) updateFn(x, y); else updateFn(y);
                };
                el.addEventListener('mousedown', (e) => { isDragging = true; move(e); });
                window.addEventListener('mousemove', move);
                window.addEventListener('mouseup', () => { 
                    if (isDragging && autoCenter) resetFn();
                    isDragging = false; 
                });
                el.addEventListener('touchstart', (e) => { isDragging = true; move(e); }, {passive: false});
                window.addEventListener('touchmove', (e) => { if (isDragging) { move(e); e.preventDefault(); } }, {passive: false});
                window.addEventListener('touchend', () => { 
                    if (isDragging && autoCenter) resetFn();
                    isDragging = false; 
                });
            };

            setupPad(vPad, updateVertical, false, false);
            setupPad(lfPad, updateLateralForward, true, true, resetLateralForward);
            
            const zPad = document.getElementById('zoom-pad');
            if (zPad) {
                setupPad(zPad, (y) => updateZoom(y), false, false);
            }
        });



        const guiFocusMap = {0: "COCKPIT", 1: "LEFT PANEL", 2: "RIGHT PANEL", 3: "COMMS", 4: "ROLE PANEL", 5: "STATION", 6: "GALAXY MAP", 7: "SYSTEM MAP", 8: "ORION", 9: "FSS", 10: "SAA", 11: "CODEX"};

        function switchPage(name) {
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(t => { t.classList.remove('active'); t.classList.add('text-gray-600'); });
            
            const page = document.getElementById('page-' + name);
            if (page) page.classList.add('active');
            
            const tab = document.getElementById('tab-' + name);
            if (tab) {
                tab.classList.add('active');
                tab.classList.remove('text-gray-600');
            }
            if (navigator.vibrate) navigator.vibrate(20);
        }

        


        function updateClock() {
            const el = document.getElementById('sys-clock');
            if (el) el.innerText = new Date().toLocaleTimeString('en-GB', { hour12: false }) + " LOC";
        }
        setInterval(updateClock, 1000);
        updateClock();

        function komut(id) {
            fetch('/action/' + id);
            if (navigator.vibrate) navigator.vibrate(40);
        }

        function setInd(id, is_active, safe_mode = false) {
            const el = document.getElementById(id);
            if (!el) return;
            el.className = el.className.replace(/ind-off|ind-on|ind-safe/g, '').trim() + ' ' + (is_active ? (safe_mode ? 'ind-safe' : 'ind-on') : 'ind-off');
        }

        function cizPips(pipsArray) {
            const renkler = ['bg-blue-500', 'bg-green-500', 'bg-red-500'];
            const idler = ['bar-sys', 'bar-eng', 'bar-wep'];
            const shadow = ['shadow-[0_0_8px_#3b82f6]', 'shadow-[0_0_8px_#22c55e]', 'shadow-[0_0_8px_#ef4444]'];

            for(let i=0; i<3; i++) {
                let html = '';
                let tamKutu = Math.floor(pipsArray[i] / 2);
                let yarimKutu = pipsArray[i] % 2 !== 0;
                
                for(let j=0; j<4; j++) {
                    if (j < tamKutu) html += `<div class="w-4 h-2 ${renkler[i]} ${shadow[i]} rounded-[1px]"></div>`;
                    else if (j === tamKutu && yarimKutu) html += `<div class="w-4 h-2 bg-gray-800 rounded-[1px] relative overflow-hidden"><div class="absolute left-0 top-0 h-full w-1/2 ${renkler[i]} ${shadow[i]}"></div></div>`;
                    else html += `<div class="w-4 h-2 bg-gray-800 rounded-[1px]"></div>`;
                }
                document.getElementById(idler[i]).innerHTML = html;
            }
        }

        function guncelle() {
            fetch('/status').then(r => r.json()).then(d => {
                if (d.hata) return;

                if (d.Flags !== undefined) {
                    const f = d.Flags;
                    setInd('ind-shield', f & 8, true);      
                    setInd('ind-hardp', f & 64, false);     
                    setInd('ind-gear', f & 4, false);       
                    setInd('ind-cargo', f & 512, false);    
                    setInd('ind-cargo-landing', f & 512, false);    
                    setInd('ind-light', f & 256, true);     
                    setInd('ind-nv', f & 8192, true);       
                    setInd('ind-silent', f & 1024, false);  
                    setInd('ind-sc', f & 16, true);         
                }


                if (d.Pips) cizPips(d.Pips);

                if (d.Fuel) {
                    const el = document.getElementById('txt-fuel-main');
                    if (el) el.innerText = d.Fuel.FuelMain.toFixed(1) + ' T';
                }

                if (d.FireGroup !== undefined) {
                    for(let i=0; i<8; i++) {
                        let fgEl = document.getElementById('fg-' + i);
                        if (fgEl) fgEl.className = `border w-6 h-6 flex items-center justify-center text-xs font-bold rounded transition-all ${d.FireGroup === i ? 'fg-on' : 'fg-off'}`;
                    }
                }

                if (d.Balance !== undefined) {
                    const el = document.getElementById('txt-cr');
                    if (el) el.innerText = d.Balance.toLocaleString() + ' CR';
                }
                if (d.Cargo !== undefined) {
                    const el = document.getElementById('txt-cargo');
                    if (el) el.innerText = d.Cargo + ' T';
                }

                const destEl = document.getElementById('txt-dest');
                if (destEl) destEl.innerText = d.Destination ? d.Destination.Name : 'NONE';
                const bodyEl = document.getElementById('txt-body');
                if (bodyEl) bodyEl.innerText = d.BodyName || 'NONE';
                const guiEl = document.getElementById('txt-gui');
                if (guiEl) guiEl.innerText = d.GuiFocus !== undefined ? (guiFocusMap[d.GuiFocus] || d.GuiFocus) : 'NONE';

                if (d.Latitude !== undefined) {
                    const latEl = document.getElementById('txt-lat');
                    if (latEl) latEl.innerText = d.Latitude.toFixed(4);
                    const lonEl = document.getElementById('txt-lon');
                    if (lonEl) lonEl.innerText = d.Longitude.toFixed(4);
                    const altEl = document.getElementById('txt-alt');
                    if (altEl) altEl.innerText = Math.round(d.Altitude).toLocaleString();
                    const hdgEl = document.getElementById('txt-hdg');
                    if (hdgEl) hdgEl.innerText = Math.round(d.Heading) + '°';
                } else {
                    ['txt-lat','txt-lon','txt-alt','txt-hdg'].forEach(id => {
                        const el = document.getElementById(id);
                        if (el) el.innerText = '-';
                    });
                }
            });
        }
        setInterval(guncelle, 1000);
        guncelle();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

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

@app.route('/status')
def get_status():
    # Platform-specific paths to Status.json
    if sys.platform == 'linux':
        possible_paths = [
            # Proton/Steam (common path)
            os.path.expanduser("~/.steam/root/drive_c/users/steamuser/Saved Games/Frontier Developments/Elite Dangerous/Status.json"),
            # Alternative Proton paths
            os.path.expanduser("~/.steamapps/compatdata/626690/pfx/drive_c/users/steamuser/Saved Games/Frontier Developments/Elite Dangerous/Status.json"),
            # Standard Wine paths
            os.path.expanduser("~/.wine/drive_c/users") + "*/Saved Games/Frontier Developments/Elite Dangerous/Status.json",
        ]
    else:
        possible_paths = [
            os.path.expanduser(r"~\Saved Games\Frontier Developments\Elite Dangerous\Status.json"),
        ]
    
    # Try to find the Status.json file
    for path in possible_paths:
        expanded_path = os.path.expanduser(path)
        if os.path.exists(expanded_path):
            try:
                with open(expanded_path, 'r', encoding='utf-8') as f:
                    return jsonify(json.load(f))
            except Exception as e:
                return jsonify({"hata": f"Error reading file: {str(e)}"})
    
    return jsonify({"hata": "Status.json not found. Please check Elite Dangerous data path."})



if __name__ == '__main__':
    initialize_vjoy(debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
