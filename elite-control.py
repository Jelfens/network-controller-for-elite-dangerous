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




# Platform-specific input handling
if sys.platform == 'linux':
    def press_key(key):
        """Send keypress on Linux using xdotool"""
        try:
            # xdotool key sends the key
            subprocess.run(['xdotool', 'key', key], check=False)
        except FileNotFoundError:
            print("Error: xdotool not found. Install it with: sudo apt install xdotool")
else:
    import pydirectinput
    def press_key(key):
        """Send keypress on Windows using pydirectinput"""
        pydirectinput.press(key)

app = Flask(__name__)

KOMUTLAR = {
    "wg-hardpoints": "u", "landing-gear": "l", "cargo-scoop": "home",
    "lights": "insert", "night-vision": "n", "silent-running": "delete",
    "fsd": "j", "heatsink": "v", "chaff": "c", "scb": "b",
    "galaxy-map": "m", "system-map": "o",
    "pip-sys": "left", "pip-eng": "up", "pip-wep": "right", "pip-rst": "down",
    "fg-prev": "[", "fg-next": "]", "menu": "esc",
    "fss": "'", "cockpit-mode": "\\",
    # Navigation & Menus
    "menu-up": "up", "menu-down": "down", "menu-left": "left", "menu-right": "right", "menu-select": "enter",
    "tab-prev": "q", "tab-next": "e",
    # Speed & Thrusters
    "speed-0": "x", "speed-25": "1", "speed-50": "2", "speed-75": "3", "speed-100": "4",
    "throttle-inc": "w", "throttle-dec": "s",
    "thruster-up": "r", "thruster-down": "f",
    "boost": "tab",
    # FSD Variants
    "fsd-sc": "k", "fsd-jump": "h",
    # Misc
    "rot-corr": "delete", "orbit-lines": "=",
    # Targeting
    "target-ahead": "t", "target-next": "g", "target-highest": "h",
    "target-team-1": "7", "target-team-2": "8", "target-team-3": "9",
    "target-team-target": "0", "target-navlock": "-", "target-sub-next": "y", "target-route": ".",
    "ui-page-prev": "[", "ui-page-next": "]",
    "panel-external": "1", "panel-comms": "2", "panel-role": "3", "panel-internal": "4"
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
        .page.active { display: flex; flex-direction: column; justify-content: space-evenly; height: 100%; }
        #page-nav.active { justify-content: flex-start; gap: 0.5rem; overflow: hidden; }
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

    <div class="flex-1 overflow-y-auto no-scrollbar p-2 pb-16">

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
                    <button onclick="komut('target-highest')" class="btn col-span-2 border-2 border-red-600 bg-red-900/40 text-red-100 rounded-xl p-3 text-base font-black shadow-[0_0_10px_rgba(220,38,38,0.3)] tracking-widest active:scale-95 transition-transform">
                        <div class="text-[9px] text-red-400 mb-0.5 opacity-70">PRIORITY</div>
                        HIGHEST THREAT
                    </button>
                    
                    <button onclick="komut('target-ahead')" class="btn border-2 border-orange-700/50 bg-orange-900/20 text-orange-400 rounded-xl p-2.5 text-sm font-bold shadow-md active:scale-95 transition-transform">
                        <div class="text-[8px] mb-0.5 opacity-70">AHEAD</div>
                        TARGET AHEAD
                    </button>
                    <button onclick="komut('target-next')" class="btn border-2 border-red-800/50 bg-red-900/10 text-red-400 rounded-xl p-2.5 text-sm font-bold shadow-md active:scale-95 transition-transform">
                        <div class="text-[8px] mb-0.5 opacity-70">CYCLE</div>
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
        <!-- ==================== SAVAŞ (COMBAT) ==================== -->
        <div id="page-combat" class="page active overflow-y-auto no-scrollbar h-full">

            <div class="grid grid-cols-4 gap-2 text-center text-xs font-bold mb-4">
                <div id="ind-hardp" onclick="komut('wg-hardpoints')" class="ind-btn cursor-pointer border rounded p-3 ind-off transition-all"><div class="text-base mb-1">⚙️</div>HARDPOINTS</div>
                <button onclick="komut('cockpit-mode')" class="btn border border-gray-800 bg-[#0a0a0a] text-indigo-400 rounded p-3 hover:border-indigo-400 hover:shadow-[0_0_10px_rgba(129,140,248,0.2)]"><div class="text-base mb-1">🖥️</div>HUD MODE</button>
                <div id="ind-silent" onclick="komut('silent-running')" class="ind-btn cursor-pointer border rounded p-3 ind-off transition-all"><div class="text-base mb-1">🤫</div>SILENT RUN</div>
                <button onclick="document.getElementById('modal-targeting').style.display='flex'" class="btn border border-red-800 bg-red-900/20 text-red-500 rounded p-3 hover:border-red-500 hover:shadow-[0_0_10px_rgba(239,68,68,0.3)]"><div class="text-base mb-1">🎯</div>TARGETING</button>
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

            <div class="grid grid-cols-3 gap-2 mb-4 text-xs font-bold">
                <button onclick="komut('heatsink')" class="btn border border-gray-800 bg-[#0a0a0a] text-blue-500 rounded p-3 hover:border-blue-500 hover:shadow-[0_0_10px_rgba(59,130,246,0.2)]"><div class="text-base mb-1">🧊</div>HEATSINK</button>
                <button onclick="komut('chaff')" class="btn border border-gray-800 bg-[#0a0a0a] text-yellow-500 rounded p-3 hover:border-yellow-500 hover:shadow-[0_0_10px_rgba(234,179,8,0.2)]"><div class="text-base mb-1">✨</div>CHAFF</button>
                <button onclick="komut('scb')" class="btn border border-gray-800 bg-[#0a0a0a] text-teal-400 rounded p-3 hover:border-teal-400 hover:shadow-[0_0_10px_rgba(45,212,191,0.2)]"><div class="text-base mb-1">🔋</div>SHIELD CELL</button>
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
        <div id="page-nav" class="page h-full overflow-hidden p-2">
            
            <!-- TOP ROW: FSD | COM | Maps -->
            <div class="flex-[2] grid grid-cols-3 gap-2 mb-2 min-h-0">
                <!-- FSD Box -->
                <div class="bg-[#050505] p-2 rounded-xl border border-orange-900/30 relative shadow-md flex flex-col justify-center">
                    <div class="absolute top-0 left-3 px-1 -mt-2 bg-[#050505] text-[7px] text-orange-600 font-black tracking-widest uppercase">FSD</div>
                    <div class="grid grid-cols-2 gap-1 h-full">
                        <button onclick="komut('fsd-jump')" class="btn h-full border border-orange-700/50 bg-orange-900/10 text-orange-400 rounded text-[9px] font-bold flex flex-col items-center justify-center">
                            <span class="text-xs">🚀</span>
                            HYP
                        </button>
                        <button onclick="komut('fsd-sc')" class="btn h-full border border-orange-700/50 bg-orange-900/10 text-orange-400 rounded text-[9px] font-bold flex flex-col items-center justify-center">
                            <span class="text-xs">⚡</span>
                            SUP
                        </button>
                        <button onclick="komut('fsd')" class="btn col-span-2 h-full border border-gray-700 bg-[#0a0a0a] text-gray-400 rounded text-[10px] font-black uppercase flex items-center justify-center gap-2">
                            <span class="text-xs">🌀</span>
                            FSD
                        </button>
                    </div>
                </div>

                <!-- Center: COM -->
                <button onclick="komut('panel-comms')" class="btn w-full h-full border-2 border-blue-900/50 bg-blue-900/10 text-blue-400 rounded-xl text-[12px] font-black shadow-lg flex flex-col items-center justify-center">
                    <span class="text-xl mb-1">📡</span>
                    COM
                </button>

                <!-- Maps Box -->
                <div class="bg-[#050505] p-2 rounded-xl border border-blue-900/30 relative shadow-md flex flex-col">
                    <div class="absolute top-0 right-3 px-1 -mt-2 bg-[#050505] text-[7px] text-blue-500 font-black tracking-widest uppercase">Maps</div>
                    <div class="grid grid-cols-2 gap-1 flex-1">
                        <button onclick="komut('target-sub-next')" class="btn h-full border border-gray-700 bg-[#0a0a0a] text-gray-400 rounded text-[9px] font-bold flex flex-col items-center justify-center leading-none">
                            <span class="text-[10px]">🎯</span>
                            SUBS
                        </button>
                        <button onclick="komut('target-route')" class="btn h-full border border-orange-900/40 bg-orange-900/10 text-orange-400 rounded text-[9px] font-bold flex flex-col items-center justify-center leading-none">
                            <span class="text-[10px]">🚩</span>
                            ROUTE
                        </button>
                        <button onclick="komut('system-map')" class="btn col-span-2 h-full border border-blue-800/50 bg-blue-900/10 text-blue-400 rounded text-[10px] font-black uppercase flex items-center justify-center gap-2">
                            <span class="text-xs">🪐</span>
                            SYS MAP
                        </button>
                        <button onclick="komut('galaxy-map')" class="btn col-span-2 h-full border border-blue-800/50 bg-blue-900/10 text-blue-400 rounded text-[10px] font-black uppercase flex items-center justify-center gap-2">
                            <span class="text-xs">🌌</span>
                            GAL MAP
                        </button>
                    </div>
                </div>
            </div>

            <!-- MIDDLE ROW: <TAB | EXT | D-PAD | INT | TAB> -->
            <div class="flex-[5] flex items-stretch justify-between gap-1 mb-2 min-h-0">
                <button onclick="komut('tab-prev')" class="btn flex-1 border border-gray-600 bg-gray-800 text-white rounded-xl text-[11px] font-black flex flex-col items-center justify-center">
                    <span class="text-lg mb-2">◀️</span>
                    TAB
                </button>
                <button onclick="komut('panel-external')" class="btn flex-[1.5] border border-orange-900/50 bg-orange-900/10 text-orange-500 rounded-xl text-[13px] font-black flex flex-col items-center justify-center">
                    <span class="text-2xl mb-2">🛰️</span>
                    EXT
                </button>

                <!-- D-PAD -->
                <div class="flex-[3] grid grid-cols-3 gap-1.5 bg-[#0a0a0a] p-2 rounded-2xl border-2 border-gray-800 shadow-inner">
                    <div></div>
                    <button onclick="komut('menu-up')" class="btn w-full h-full border border-gray-600 bg-gray-800 rounded-lg text-2xl">▲</button>
                    <div></div>
                    <button onclick="komut('menu-left')" class="btn w-full h-full border border-gray-600 bg-gray-800 rounded-lg text-2xl">◀</button>
                    <button onclick="komut('menu-select')" class="btn w-full h-full border-2 border-orange-500 bg-orange-900/30 text-orange-400 rounded-lg font-black text-lg flex flex-col items-center justify-center">
                        <span class="text-xl">✅</span>
                        OK
                    </button>
                    <button onclick="komut('menu-right')" class="btn w-full h-full border border-gray-600 bg-gray-800 rounded-lg text-2xl">▶</button>
                    <div></div>
                    <button onclick="komut('menu-down')" class="btn w-full h-full border border-gray-600 bg-gray-800 rounded-lg text-2xl">▼</button>
                    <div></div>
                </div>

                <button onclick="komut('panel-internal')" class="btn flex-[1.5] border border-orange-900/50 bg-orange-900/10 text-orange-500 rounded-xl text-[13px] font-black flex flex-col items-center justify-center">
                    <span class="text-2xl mb-2">🖥️</span>
                    INT
                </button>
                <button onclick="komut('tab-next')" class="btn flex-1 border border-gray-600 bg-gray-800 text-white rounded-xl text-[11px] font-black flex flex-col items-center justify-center">
                    <span class="text-lg mb-2">▶️</span>
                    TAB
                </button>
            </div>

            <!-- BOTTOM ROW: PAGE | ROLE | AUX -->
            <div class="flex-[1.5] grid grid-cols-3 gap-2 min-h-0">
                <div class="flex flex-col gap-1">
                    <button onclick="komut('ui-page-prev')" class="btn flex-1 border border-gray-700 bg-[#0a0a0a] text-gray-500 rounded text-[9px] font-black flex items-center justify-center gap-1">
                        <span>🔼</span> UP
                    </button>
                    <button onclick="komut('ui-page-next')" class="btn flex-1 border border-gray-700 bg-[#0a0a0a] text-gray-500 rounded text-[9px] font-black flex items-center justify-center gap-1">
                        <span>🔽</span> DOWN
                    </button>
                </div>
                <button onclick="komut('panel-role')" class="btn w-full h-full border-2 border-blue-900/50 bg-blue-900/10 text-blue-400 rounded-xl text-[12px] font-black shadow-lg flex flex-col items-center justify-center">
                    <span class="text-xl">👥</span>
                    ROLE
                </button>
                <button onclick="switchPage('aux')" class="btn w-full h-full border-2 border-gray-600 bg-gray-800 text-gray-300 rounded-xl text-[12px] font-black shadow-lg flex flex-col items-center justify-center">
                    <span class="text-xl">🛠️</span>
                    AUX
                </button>
            </div>
        </div>


        <!-- ==================== AUX ==================== -->
        <div id="page-aux" class="page overflow-y-auto no-scrollbar h-full p-3">
            <div class="flex flex-col gap-3">
                <div class="text-[9px] text-orange-600 font-black tracking-[0.3em] uppercase border-b border-orange-900/20 pb-2">Ship Systems</div>
                <div class="grid grid-cols-2 gap-3">
                    <div id="ind-cargo" onclick="komut('cargo-scoop')" class="ind-btn cursor-pointer border-2 rounded-xl py-8 text-xs font-black ind-off transition-all text-center flex flex-col items-center justify-center">
                        <span class="text-2xl mb-1">📦</span>CARGO SCOOP
                    </div>
                    <div id="ind-light" onclick="komut('lights')" class="ind-btn cursor-pointer border-2 rounded-xl py-8 text-xs font-black ind-off transition-all text-center flex flex-col items-center justify-center">
                        <span class="text-2xl mb-1">💡</span>LIGHTS
                    </div>
                    <div id="ind-nv" onclick="komut('night-vision')" class="ind-btn cursor-pointer border-2 rounded-xl py-8 text-xs font-black ind-off transition-all text-center flex flex-col items-center justify-center col-span-2">
                        <span class="text-2xl mb-1">👁️</span>NIGHT VISION
                    </div>
                </div>

                <div class="text-[9px] text-orange-600 font-black tracking-[0.3em] uppercase border-b border-orange-900/20 pb-2 mt-2">Utilities</div>
                <div class="grid grid-cols-1 gap-2">
                    <button onclick="komut('rot-corr')" class="btn border border-gray-700 bg-[#0a0a0a] text-gray-300 rounded-xl py-4 text-[10px] font-black uppercase">Rotation Correction</button>
                    <button onclick="komut('orbit-lines')" class="btn border border-gray-700 bg-[#0a0a0a] text-gray-300 rounded-xl py-4 text-[10px] font-black uppercase">Orbit Lines</button>
                </div>

                <button onclick="switchPage('nav')" class="w-full py-3 bg-orange-900/20 border border-orange-800/50 text-orange-500 text-[10px] font-black rounded-xl uppercase tracking-widest mt-2">&lt; Back to Nav</button>
            </div>
        </div>



        <!-- ==================== BİLGİ (INFO) ==================== -->
        <div id="page-info" class="page overflow-y-auto no-scrollbar h-full">

            <div class="grid grid-cols-2 gap-2 mb-4">
                <div class="bg-[#050505] border border-orange-900/50 rounded p-3 text-center relative overflow-hidden">
                    <div class="absolute inset-0 bg-gradient-to-t from-orange-900/10 to-transparent"></div>
                    <div class="text-gray-500 text-[10px] font-black uppercase tracking-[0.2em] mb-1 relative z-10">Balance</div>
                    <div id="txt-cr" class="ed-text text-lg font-black tracking-wider relative z-10 ed-glow">- CR</div>
                </div>
                <div class="bg-[#050505] border border-orange-900/50 rounded p-3 text-center relative overflow-hidden">
                    <div class="absolute inset-0 bg-gradient-to-t from-orange-900/10 to-transparent"></div>
                    <div class="text-gray-500 text-[10px] font-black uppercase tracking-[0.2em] mb-1 relative z-10">Cargo</div>
                    <div id="txt-cargo" class="ed-text text-lg font-black tracking-wider relative z-10 ed-glow">- T</div>
                </div>
            </div>

            <div class="grid grid-cols-2 gap-3 text-[10px] text-gray-400 font-bold tracking-wider mb-4">
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

            <div class="text-center text-xl font-black text-gray-600 tracking-[0.2em]" id="sys-clock">00:00:00 LOC</div>
        </div>

        <!-- ==================== İNİŞ (LANDING) ==================== -->
        <div id="page-landing" class="page overflow-y-auto no-scrollbar h-full">
            <div class="flex-1 flex flex-col gap-4 p-2">
                
                <!-- LANDING STATUS -->
                <div class="w-full">
                    <div id="ind-gear" onclick="komut('landing-gear')" class="ind-btn cursor-pointer border-2 rounded-xl py-8 text-sm font-black ind-off transition-all text-center flex flex-col items-center justify-center shadow-lg">
                        <span class="text-3xl mb-2">⚓</span>
                        LANDING GEAR
                    </div>
                </div>


                <!-- DUAL PAD CONTROLS -->
                <div class="flex-1 flex gap-3 min-h-0 bg-[#050505] p-3 rounded-2xl border border-blue-900/20 relative shadow-inner">
                    <div class="absolute top-0 left-6 px-3 -mt-2 bg-[#050505] text-[10px] text-blue-500 font-black tracking-widest uppercase">Precision Thrust Control</div>
                    
                    <!-- Vertical Pad (Wider) -->
                    <div class="flex flex-col gap-2 w-20">
                        <div id="v-pad" class="relative flex-1 bg-[#0a0a0a] border-2 border-blue-900/40 rounded-xl overflow-hidden cursor-ns-resize touch-none">
                            <div class="absolute inset-0 flex items-center justify-center opacity-20 pointer-events-none">
                                <div class="w-full h-[1px] bg-blue-500/50"></div>
                            </div>
                            <div id="v-handle" class="absolute left-1/2 w-14 h-3 bg-blue-500 rounded-full shadow-[0_0_15px_rgba(59,130,246,0.8)] -translate-x-1/2 -translate-y-1/2 pointer-events-none transition-[top] duration-75" style="top: 50%;"></div>
                            <div class="absolute top-2 left-1/2 -translate-x-1/2 text-[8px] text-blue-500 font-black opacity-40 uppercase">UP</div>
                            <div class="absolute bottom-2 left-1/2 -translate-x-1/2 text-[8px] text-blue-500 font-black opacity-40 uppercase">DOWN</div>
                        </div>
                        <button onclick="resetVertical()" class="py-2 bg-red-900/10 border border-red-900/40 text-red-500 text-[9px] font-black rounded-lg uppercase active:scale-95 transition-all">RESET V</button>
                    </div>

                    <!-- Lateral/Forward Pad -->
                    <div class="flex flex-col gap-2 flex-1">
                        <div id="lf-pad" class="relative flex-1 bg-[#0a0a0a] border-2 border-blue-900/40 rounded-xl overflow-hidden cursor-crosshair touch-none">
                            <div class="absolute inset-0 flex items-center justify-center opacity-20 pointer-events-none">
                                <div class="w-full h-[1px] bg-blue-500/30"></div>
                                <div class="h-full w-[1px] bg-blue-500/30"></div>
                            </div>
                            <div id="lf-handle" class="absolute w-7 h-7 bg-blue-500 rounded-full shadow-[0_0_15px_rgba(59,130,246,0.9)] -translate-x-1/2 -translate-y-1/2 pointer-events-none transition-[left,top] duration-75" style="left: 50%; top: 50%;"></div>
                            <div class="absolute top-2 left-1/2 -translate-x-1/2 text-[8px] text-blue-500 font-black opacity-40 uppercase">FWD</div>
                            <div class="absolute bottom-2 left-1/2 -translate-x-1/2 text-[8px] text-blue-500 font-black opacity-40 uppercase">BCK</div>
                            <div class="absolute top-1/2 left-2 -translate-y-1/2 text-[8px] text-blue-500 font-black opacity-40 uppercase -rotate-90">LEFT</div>
                            <div class="absolute top-1/2 right-2 -translate-y-1/2 text-[8px] text-blue-500 font-black opacity-40 uppercase rotate-90">RIGHT</div>
                        </div>
                        <button onclick="resetLateralForward()" class="py-2 bg-red-900/10 border border-red-900/40 text-red-500 text-[9px] font-black rounded-lg uppercase active:scale-95 transition-all">RESET L/F</button>
                    </div>
                </div>

                <div class="py-2 text-center">
                    <div class="text-[9px] text-gray-600 font-black tracking-[0.4em] uppercase animate-pulse">Docking protocols active</div>
                </div>
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

            const setupPad = (el, updateFn, is2D) => {
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
                window.addEventListener('mouseup', () => { isDragging = false; });
                el.addEventListener('touchstart', (e) => { isDragging = true; move(e); }, {passive: false});
                window.addEventListener('touchmove', (e) => { if (isDragging) { move(e); e.preventDefault(); } }, {passive: false});
                window.addEventListener('touchend', () => { isDragging = false; });
            };

            setupPad(vPad, updateVertical, false);
            setupPad(lfPad, updateLateralForward, true);
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
        press_key(KOMUTLAR[komut_adi])
        return "OK"
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
