from flask import Flask, jsonify, render_template_string, request as flask_request
import json
import os
import sys
import platform
import subprocess
import urllib.request

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
    "fss": "'", "cockpit-mode": "\\" 
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
        .tab-btn { transition: all 0.2s; }
        .tab-btn.active {
            color: #ff8c00;
            border-color: #ff8c00;
            background: rgba(255,140,0,0.1);
            box-shadow: 0 -2px 10px rgba(255,140,0,0.3);
        }
        .tab-btn.active .tab-icon { filter: drop-shadow(0 0 4px rgba(255,140,0,0.6)); }
    </style>
</head>
<body class="text-gray-300 font-mono select-none flex flex-col h-screen tracking-tight overflow-hidden">

    <div class="flex-1 overflow-hidden p-3 pb-16">


        <!-- ==================== SAVAŞ (COMBAT) ==================== -->
        <div id="page-combat" class="page active">

            <div class="grid grid-cols-4 gap-2 text-center text-xs font-bold mb-4">
                <div id="ind-hardp" onclick="komut('wg-hardpoints')" class="ind-btn cursor-pointer border rounded p-3 ind-off transition-all"><div class="text-base mb-1">⚙️</div>HARDPOINTS</div>
                <button onclick="komut('cockpit-mode')" class="btn border border-gray-800 bg-[#0a0a0a] text-indigo-400 rounded p-3 hover:border-indigo-400 hover:shadow-[0_0_10px_rgba(129,140,248,0.2)]"><div class="text-base mb-1">🖥️</div>HUD MODE</button>
                <div id="ind-silent" onclick="komut('silent-running')" class="ind-btn cursor-pointer border rounded p-3 ind-off transition-all"><div class="text-base mb-1">🤫</div>SILENT RUN</div>
                <div id="ind-shield" class="border rounded p-3 ind-off transition-all"><div class="text-base mb-1">🛡️</div>SHIELD</div>
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
        <div id="page-nav" class="page">
            <div class="grid grid-cols-2 gap-2 text-center text-xs font-bold mb-4">
                <div id="ind-sc" onclick="komut('fsd')" class="ind-btn cursor-pointer border rounded p-3 ind-off transition-all"><div class="text-base mb-1">🚀</div>FSD / SC</div>
                <div id="ind-gear" onclick="komut('landing-gear')" class="ind-btn cursor-pointer border rounded p-3 ind-off transition-all"><div class="text-base mb-1">🛬</div>GEAR</div>
                <div id="ind-cargo" onclick="komut('cargo-scoop')" class="ind-btn cursor-pointer border rounded p-3 ind-off transition-all"><div class="text-base mb-1">📦</div>SCOOP</div>
                <div id="ind-light" onclick="komut('lights')" class="ind-btn cursor-pointer border rounded p-3 ind-off transition-all"><div class="text-base mb-1">💡</div>LIGHTS</div>
                <div id="ind-nv" onclick="komut('night-vision')" class="ind-btn cursor-pointer border rounded p-3 ind-off transition-all"><div class="text-base mb-1">👁️</div>N-VISION</div>
                <button onclick="komut('cockpit-mode')" class="btn border border-gray-800 bg-[#0a0a0a] text-indigo-400 rounded p-3 hover:border-indigo-400 hover:shadow-[0_0_10px_rgba(129,140,248,0.2)]"><div class="text-base mb-1">🖥️</div>HUD MODE</button>
            </div>
            <div class="grid grid-cols-3 gap-2 mb-4 text-xs font-bold">
                <button onclick="komut('galaxy-map')" class="btn border border-gray-800 bg-[#0a0a0a] text-gray-400 rounded p-3 hover:border-gray-400"><div class="text-base mb-1">🌌</div>GAL MAP</button>
                <button onclick="komut('system-map')" class="btn border border-gray-800 bg-[#0a0a0a] text-gray-400 rounded p-3 hover:border-gray-400"><div class="text-base mb-1">🪐</div>SYS MAP</button>
                <button onclick="komut('fss')" class="btn border border-gray-800 bg-[#0a0a0a] text-purple-400 rounded p-3 hover:border-purple-400 hover:shadow-[0_0_10px_rgba(192,132,252,0.2)]"><div class="text-base mb-1">📡</div>FSS</button>
            </div>

            <button onclick="komut('menu')" class="btn w-full border border-gray-600 bg-gray-800 text-white rounded p-3 text-xs font-bold hover:border-white shadow-[0_0_10px_rgba(255,255,255,0.1)] tracking-widest">☰ MENU (ESC)</button>
        </div>

        <!-- ==================== BİLGİ (INFO) ==================== -->
        <div id="page-info" class="page">

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

        <!-- ==================== NEAREST SEARCH ==================== -->
        <div id="page-inara" class="page">
            
            <!-- SEARCH FORM VIEW -->
            <div id="near-search-view" class="bg-[#0a0a0a] p-3 rounded border border-gray-800 mb-4 flex-1 flex flex-col min-h-0">
                <div class="text-xs text-gray-400 mb-4 font-bold tracking-widest text-center border-b border-gray-800 pb-2 uppercase">Station Database</div>
                
                <div class="mb-4">
                    <div class="text-[9px] text-gray-500 mb-1 font-bold tracking-wider uppercase">Reference System</div>
                    <input type="text" id="near-sys-input" placeholder="e.g. Sol" class="w-full bg-[#050505] border border-gray-700 text-gray-300 rounded p-3 text-sm focus:border-[#ff8c00] focus:outline-none">
                    <div id="recent-systems" class="flex gap-1.5 mt-2 overflow-x-auto pb-1 empty:hidden"></div>
                    <input type="hidden" id="near-service-input" value="">
                </div>
                
                <button onclick="searchNearest()" class="btn w-full border border-[#ff8c00] bg-orange-900/20 text-[#ff8c00] rounded p-3 text-xs font-bold mb-3 shadow-[0_0_10px_rgba(255,140,0,0.1)] uppercase tracking-widest">Search Database</button>
                
                <div id="near-loading" class="hidden text-center text-xs text-orange-500 py-4 font-black tracking-widest animate-pulse">ACCESSING DATABASE...</div>
            </div>

            <!-- FILTER VIEW -->
            <div id="near-filter-view" class="bg-[#0a0a0a] p-3 rounded border border-gray-800 mb-4 flex-1 flex flex-col min-h-0 hidden">
                <div class="flex justify-between items-center border-b border-gray-800 pb-2 mb-3 sticky top-0 bg-[#0a0a0a] z-20">
                    <button onclick="closeFilters()" class="btn border border-gray-700 bg-[#050505] text-[#ff8c00] hover:text-white rounded px-3 py-1 text-[10px] font-bold">◀ DONE</button>
                    <div class="text-[10px] text-gray-500 font-black tracking-widest uppercase">ADVANCED FILTERS</div>
                </div>
                
                <div class="flex-1 overflow-y-auto min-h-0 pr-1 pb-4">
                    <div class="grid grid-cols-2 gap-2 mb-4 border-b border-gray-800 pb-4">
                        <div>
                            <div class="text-[9px] text-gray-500 mb-1 font-bold">MIN. LANDING PAD</div>
                            <select id="near-pad-input" class="w-full bg-[#050505] border border-gray-700 text-gray-300 rounded p-1.5 text-[10px] focus:border-[#ff8c00] focus:outline-none appearance-none">
                                <option value="any">Any Pad Size</option>
                                <option value="large">Large (L) Only</option>
                            </select>
                        </div>
                        <div>
                            <div class="text-[9px] text-gray-500 mb-1 font-bold">SURFACE STATIONS</div>
                            <select id="near-surface-input" class="w-full bg-[#050505] border border-gray-700 text-gray-300 rounded p-1.5 text-[10px] focus:border-[#ff8c00] focus:outline-none appearance-none">
                                <option value="yes">Include Surface</option>
                                <option value="no">Exclude Surface</option>
                            </select>
                        </div>
                        <div>
                            <div class="text-[9px] text-gray-500 mb-1 font-bold">MAX ARRIVAL (Ls)</div>
                            <select id="near-arrival-input" class="w-full bg-[#050505] border border-gray-700 text-gray-300 rounded p-1.5 text-[10px] focus:border-[#ff8c00] focus:outline-none appearance-none">
                                <option value="any">Any Distance</option>
                                <option value="1000">< 1,000 Ls</option>
                                <option value="5000">< 5,000 Ls</option>
                                <option value="10000">< 10,000 Ls</option>
                            </select>
                        </div>
                        <div>
                            <div class="text-[9px] text-gray-500 mb-1 font-bold">FLEET CARRIERS</div>
                            <select id="near-fc-input" class="w-full bg-[#050505] border border-gray-700 text-gray-300 rounded p-1.5 text-[10px] focus:border-[#ff8c00] focus:outline-none appearance-none">
                                <option value="no">Ignore Fleet Carriers</option>
                                <option value="yes">Include Fleet Carriers</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>

            <!-- MODULE VIEW -->
            <div id="near-module-view" class="bg-[#0a0a0a] p-3 rounded border border-gray-800 mb-4 flex-1 flex flex-col min-h-0 hidden">
                <div class="flex justify-between items-center border-b border-gray-800 pb-2 mb-3 sticky top-0 bg-[#0a0a0a] z-20">
                    <button onclick="closeModuleFinder()" class="btn border border-gray-700 bg-[#050505] text-[#ff8c00] hover:text-white rounded px-3 py-1 text-[10px] font-bold">◀ DONE</button>
                    <div class="text-[10px] text-gray-500 font-black tracking-widest uppercase">OUTFITTING</div>
                </div>
                
                <div class="flex-1 overflow-y-auto min-h-0 pr-1 pb-4">
                    <div class="mb-3 border border-[#ff8c00]/30 p-2 rounded bg-[#ff8c00]/5">
                        <div class="text-[10px] text-[#ff8c00] mb-2 font-black tracking-widest">MODULE / SHIP FINDER</div>
                        <div class="flex h-[180px] border border-gray-800 rounded mb-2">
                            <div class="w-1/3 border-r border-gray-800 flex flex-col bg-[#050505]">
                                <button id="fcat-Ship" onclick="setFCat('Ship')" class="flex-1 text-left px-2 text-[10px] font-bold text-gray-500 hover:text-white border-b border-gray-800 focus:outline-none">SHIPS</button>
                                <button id="fcat-Core" onclick="setFCat('Core')" class="flex-1 text-left px-2 text-[10px] font-bold text-gray-500 hover:text-white border-b border-gray-800 focus:outline-none">CORE</button>
                                <button id="fcat-Optional" onclick="setFCat('Optional')" class="flex-1 text-left px-2 text-[10px] font-bold text-gray-500 hover:text-white border-b border-gray-800 focus:outline-none">OPTIONAL</button>
                                <button id="fcat-Hardpoint" onclick="setFCat('Hardpoint')" class="flex-1 text-left px-2 text-[10px] font-bold text-gray-500 hover:text-white border-b border-gray-800 focus:outline-none">WEAPON</button>
                                <button id="fcat-Utility" onclick="setFCat('Utility')" class="flex-1 text-left px-2 text-[10px] font-bold text-gray-500 hover:text-white focus:outline-none">UTILITY</button>
                            </div>
                            <div id="f-type-container" class="w-2/3 overflow-y-auto p-1.5 bg-[#020202]">
                                <div class="text-center text-gray-600 text-[9px] mt-8 font-bold tracking-widest">SELECT A CATEGORY</div>
                            </div>
                        </div>

                        <input type="hidden" id="mod-build-cat" value="">
                        <input type="hidden" id="mod-build-type" value="">

                        <div id="f-class-rating-container" class="mb-2 opacity-50 pointer-events-none transition-opacity">
                            <div class="mb-2">
                                <div class="text-[8px] text-gray-400 mb-1 font-bold tracking-widest">CLASS (SIZE)</div>
                                <div class="flex bg-[#050505] border border-gray-800 rounded overflow-hidden">
                                    <button onclick="setFClass('1')" id="fbtn-cls-1" class="flex-1 py-1.5 text-[10px] font-bold text-gray-500 hover:text-white border-r border-gray-800 focus:outline-none transition-colors">1</button>
                                    <button onclick="setFClass('2')" id="fbtn-cls-2" class="flex-1 py-1.5 text-[10px] font-bold text-gray-500 hover:text-white border-r border-gray-800 focus:outline-none transition-colors">2</button>
                                    <button onclick="setFClass('3')" id="fbtn-cls-3" class="flex-1 py-1.5 text-[10px] font-bold text-gray-500 hover:text-white border-r border-gray-800 focus:outline-none transition-colors">3</button>
                                    <button onclick="setFClass('4')" id="fbtn-cls-4" class="flex-1 py-1.5 text-[10px] font-bold text-gray-500 hover:text-white border-r border-gray-800 focus:outline-none transition-colors">4</button>
                                    <button onclick="setFClass('5')" id="fbtn-cls-5" class="flex-1 py-1.5 text-[10px] font-bold text-gray-500 hover:text-white border-r border-gray-800 focus:outline-none transition-colors">5</button>
                                    <button onclick="setFClass('6')" id="fbtn-cls-6" class="flex-1 py-1.5 text-[10px] font-bold text-gray-500 hover:text-white border-r border-gray-800 focus:outline-none transition-colors">6</button>
                                    <button onclick="setFClass('7')" id="fbtn-cls-7" class="flex-1 py-1.5 text-[10px] font-bold text-gray-500 hover:text-white border-r border-gray-800 focus:outline-none transition-colors">7</button>
                                    <button onclick="setFClass('8')" id="fbtn-cls-8" class="flex-1 py-1.5 text-[10px] font-bold text-gray-500 hover:text-white focus:outline-none transition-colors">8</button>
                                </div>
                            </div>
                            <div class="mb-2">
                                <div class="text-[8px] text-gray-400 mb-1 font-bold tracking-widest">RATING</div>
                                <div class="flex bg-[#050505] border border-gray-800 rounded overflow-hidden">
                                    <button onclick="setFRating('A')" id="fbtn-rtg-A" class="flex-1 py-1.5 text-[10px] font-bold text-gray-500 hover:text-white border-r border-gray-800 focus:outline-none transition-colors">A</button>
                                    <button onclick="setFRating('B')" id="fbtn-rtg-B" class="flex-1 py-1.5 text-[10px] font-bold text-gray-500 hover:text-white border-r border-gray-800 focus:outline-none transition-colors">B</button>
                                    <button onclick="setFRating('C')" id="fbtn-rtg-C" class="flex-1 py-1.5 text-[10px] font-bold text-gray-500 hover:text-white border-r border-gray-800 focus:outline-none transition-colors">C</button>
                                    <button onclick="setFRating('D')" id="fbtn-rtg-D" class="flex-1 py-1.5 text-[10px] font-bold text-gray-500 hover:text-white border-r border-gray-800 focus:outline-none transition-colors">D</button>
                                    <button onclick="setFRating('E')" id="fbtn-rtg-E" class="flex-1 py-1.5 text-[10px] font-bold text-gray-500 hover:text-white border-r border-gray-800 focus:outline-none transition-colors">E</button>
                                    <button onclick="setFRating('F')" id="fbtn-rtg-F" class="flex-1 py-1.5 text-[10px] font-bold text-gray-500 hover:text-white border-r border-gray-800 focus:outline-none transition-colors">F</button>
                                    <button onclick="setFRating('G')" id="fbtn-rtg-G" class="flex-1 py-1.5 text-[10px] font-bold text-gray-500 hover:text-white border-r border-gray-800 focus:outline-none transition-colors">G</button>
                                    <button onclick="setFRating('I')" id="fbtn-rtg-I" class="flex-1 py-1.5 text-[10px] font-bold text-gray-500 hover:text-white focus:outline-none transition-colors">I</button>
                                </div>
                            </div>
                        </div>

                        <input type="hidden" id="mod-build-class" value="">
                        <input type="hidden" id="mod-build-rating" value="">

                        <button id="mod-build-add-btn" onclick="addModuleQuery()" data-query="" class="w-full bg-[#ff8c00] text-black py-2 mt-2 rounded font-black tracking-widest hover:bg-orange-400 transition-colors opacity-50 pointer-events-none">
                            + ADD MODULE
                        </button>
                        <div id="mod-build-list" class="mt-2 flex flex-wrap gap-1 empty:hidden"></div>
                    </div>
                </div>
            </div>

            <!-- RESULTS VIEW -->
            <div id="near-results-view" class="bg-[#0a0a0a] p-3 rounded border border-gray-800 mb-4 flex-1 flex flex-col min-h-0 hidden">
                <div class="flex justify-between items-center border-b border-gray-800 pb-2 mb-3 sticky top-0 bg-[#0a0a0a] z-20">
                    <button onclick="backToSearch()" class="btn border border-gray-700 bg-[#050505] text-gray-400 hover:text-white rounded px-3 py-1 text-[10px] font-bold">◀ BACK</button>
                    <div class="text-[10px] text-[#ff8c00] font-black tracking-widest uppercase" id="near-results-title">RESULTS</div>
                </div>
                
                <div id="near-results" class="flex-1 overflow-y-auto min-h-0 pr-1 pb-4">
                    <div id="near-list" class="flex flex-col gap-2"></div>
                </div>
            </div>

            <!-- DETAIL VIEW -->
            <div id="near-detail-view" class="bg-[#0a0a0a] p-3 rounded border border-gray-800 mb-4 flex-1 flex flex-col min-h-0 hidden">
                <div class="flex justify-between items-center border-b border-gray-800 pb-2 mb-3 sticky top-0 bg-[#0a0a0a] z-20">
                    <button onclick="backToResults()" class="btn border border-gray-700 bg-[#050505] text-gray-400 hover:text-white rounded px-3 py-1 text-[10px] font-bold">◀ RESULTS</button>
                    <div class="text-[10px] text-[#ff8c00] font-black tracking-widest uppercase">STATION DETAILS</div>
                </div>
                
                <div id="near-detail-content" class="flex-1 overflow-y-auto min-h-0 pr-1 pb-4"></div>
            </div>
            
        </div>

    </div>

    <!-- ==================== TAB BAR ==================== -->
    <div class="fixed bottom-0 left-0 right-0 bg-[#0a0a0a] border-t border-gray-800 grid grid-cols-4 text-center z-50">
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
        <button onclick="switchPage('inara')" id="tab-inara" class="tab-btn py-3 border-t-2 border-transparent text-gray-600">
            <div class="tab-icon text-lg mb-0.5">🌐</div>
            <div class="text-[10px] font-black tracking-widest">DATABASE</div>
        </button>
    </div>

    <script>
        const guiFocusMap = {0: "COCKPIT", 1: "LEFT PANEL", 2: "RIGHT PANEL", 3: "COMMS", 4: "ROLE PANEL", 5: "STATION", 6: "GALAXY MAP", 7: "SYSTEM MAP", 8: "ORION", 9: "FSS", 10: "SAA", 11: "CODEX"};

        function switchPage(name) {
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(t => { t.classList.remove('active'); t.classList.add('text-gray-600'); });
            document.getElementById('page-' + name).classList.add('active');
            const tab = document.getElementById('tab-' + name);
            tab.classList.add('active');
            tab.classList.remove('text-gray-600');
            if (navigator.vibrate) navigator.vibrate(20);
        }

        function openFilters() {
            document.getElementById('near-search-view').classList.add('hidden');
            document.getElementById('near-filter-view').classList.remove('hidden');
            document.getElementById('near-filter-view').classList.add('flex');
        }

        function closeFilters() {
            document.getElementById('near-filter-view').classList.add('hidden');
            document.getElementById('near-filter-view').classList.remove('flex');
            document.getElementById('near-search-view').classList.remove('hidden');
            updateFilterSummary();
        }

        function openModuleFinder() {
            document.getElementById('near-search-view').classList.add('hidden');
            document.getElementById('near-module-view').classList.remove('hidden');
            document.getElementById('near-module-view').classList.add('flex');
            
            if(!document.getElementById('mod-build-cat').value) {
                setFCat('Core'); // select default category
            }
        }

        function closeModuleFinder() {
            document.getElementById('near-module-view').classList.add('hidden');
            document.getElementById('near-module-view').classList.remove('flex');
            document.getElementById('near-search-view').classList.remove('hidden');
            updateFilterSummary();
        }

        function updateFilterSummary() {
            let active = 0;
            if(document.getElementById('near-pad-input').value !== 'any') active++;
            if(document.getElementById('near-surface-input').value !== 'yes') active++;
            if(document.getElementById('near-arrival-input').value !== 'any') active++;
            if(document.getElementById('near-fc-input').value !== 'no') active++;
            
            const addBtn = document.getElementById('mod-build-add-btn');
            const preview = addBtn ? addBtn.dataset.query : '';
            if(addedModules.length > 0 || preview) active++;

            const sum = document.getElementById('filter-summary');
            if(active > 0) {
                sum.innerText = `(${active} CUSTOM FILTER${active > 1 ? 'S' : ''} ACTIVE)`;
                sum.classList.remove('hidden');
            } else {
                sum.classList.add('hidden');
            }
        }
        function backToSearch() {
            document.getElementById('near-results-view').classList.add('hidden');
            document.getElementById('near-search-view').classList.remove('hidden');
            document.getElementById('near-sys-input').focus();
        }

        function backToResults() {
            document.getElementById('near-detail-view').classList.add('hidden');
            document.getElementById('near-results-view').classList.remove('hidden');
        }

        const modTypes = {
            'Ship': ['Adder', 'Alliance Challenger', 'Alliance Chieftain', 'Alliance Crusader', 'Anaconda', 'Asp Explorer', 'Asp Scout', 'Beluga Liner', 'Cobra Mk III', 'Cobra Mk IV', 'Diamondback Explorer', 'Diamondback Scout', 'Dolphin', 'Eagle', 'Federal Assault Ship', 'Federal Corvette', 'Federal Dropship', 'Federal Gunship', 'Fer-de-Lance', 'Hauler', 'Imperial Clipper', 'Imperial Courier', 'Imperial Cutter', 'Imperial Eagle', 'Keelback', 'Krait Mk II', 'Krait Phantom', 'Mamba', 'Mandalay', 'Orca', 'Python', 'Python Mk II', 'Sidewinder', 'Type-6 Transporter', 'Type-7 Transporter', 'Type-8 Transporter', 'Type-9 Heavy', 'Type-10 Defender', 'Viper Mk III', 'Viper Mk IV', 'Vulture'],
            'Core': ['SCO Frame Shift Drive', 'Frame Shift Drive', 'Power Plant', 'Thrusters', 'Life Support', 'Power Distributor', 'Sensors', 'Fuel Tank'],
            'Optional': ['Shield Generator', 'Fuel Scoop', 'Cargo Rack', 'Shield Cell Bank', 'Passenger Cabin', 'Auto Field-Maintenance Unit', 'Hull Reinforcement Package', 'Module Reinforcement Package', 'Detailed Surface Scanner', 'Planetary Vehicle Hangar', 'Fighter Hangar', 'Collector Limpet Controller', 'Prospector Limpet Controller', 'Hatch Breaker Limpet Controller'],
            'Hardpoint': ['Pulse Laser', 'Burst Laser', 'Beam Laser', 'Multi-cannon', 'Cannon', 'Fragment Cannon', 'Missile Rack', 'Torpedo Pylon', 'Plasma Accelerator', 'Rail Gun', 'Mining Laser', 'Seismic Charge Launcher', 'Abrasion Blaster'],
            'Utility': ['Shield Booster', 'Chaff Launcher', 'Heat Sink Launcher', 'Electronic Countermeasure', 'Point Defence', 'Frame Shift Wake Scanner', 'Kill Warrant Scanner', 'Manifest Scanner']
        };

        let addedModules = [];
        let recentSystems = JSON.parse(localStorage.getItem('recentSystems') || '[]');

        function setService(svc) {
            document.getElementById('near-service-input').value = svc;
            document.querySelectorAll('.svc-btn').forEach(btn => {
                if (btn.innerText.includes(svc.toUpperCase().substring(0, 5)) || (svc === 'Interstellar Factors Contact' && btn.innerText === 'INT. FACTORS')) {
                    btn.classList.add('active', 'border-[#ff8c00]', 'text-[#ff8c00]', 'bg-orange-950/20');
                    btn.classList.remove('text-gray-400');
                } else {
                    btn.classList.remove('active', 'border-[#ff8c00]', 'text-[#ff8c00]', 'bg-orange-950/20');
                    btn.classList.add('text-gray-400');
                }
            });
            // Manual fixes for short names
            const map = {
                'Outfitting': 'OUTFITTING',
                'Shipyard': 'SHIPYARD',
                'Material Trader': 'MAT. TRADER',
                'Technology Broker': 'TECH BROKER',
                'Interstellar Factors Contact': 'INT. FACTORS',
                'Black Market': 'BLACK MARKET'
            };
            document.querySelectorAll('.svc-btn').forEach(btn => {
                if (btn.innerText === map[svc]) {
                    btn.classList.add('active', 'border-[#ff8c00]', 'text-[#ff8c00]', 'bg-orange-950/20');
                    btn.classList.remove('text-gray-400');
                } else {
                    btn.classList.remove('active', 'border-[#ff8c00]', 'text-[#ff8c00]', 'bg-orange-950/20');
                    btn.classList.add('text-gray-400');
                }
            });
        }

        function updateRecentSystemsUI() {
            const container = document.getElementById('recent-systems');
            container.innerHTML = recentSystems.map(sys => `
                <button onclick="setSystem('${sys}')" class="bg-[#111] border border-gray-800 text-gray-500 hover:text-white rounded px-2 py-1 text-[9px] font-bold transition-all whitespace-nowrap uppercase">${sys}</button>
            `).join('');
        }

        function setSystem(sys) {
            document.getElementById('near-sys-input').value = sys;
        }

        function addRecentSystem(sys) {
            if (!sys) return;
            recentSystems = [sys, ...recentSystems.filter(s => s !== sys)].slice(0, 3);
            localStorage.setItem('recentSystems', JSON.stringify(recentSystems));
            updateRecentSystemsUI();
        }

        function addModuleQuery() {
            const addBtn = document.getElementById('mod-build-add-btn');
            const preview = addBtn.dataset.query;
            if(preview) {
                if(!addedModules.includes(preview)) {
                    addedModules.push(preview);
                    renderAddedModules();
                }
            }
        }

        function removeModuleQuery(idx) {
            addedModules.splice(idx, 1);
            renderAddedModules();
        }

        function getQueryColor(q) {
            const cls = q.charAt(0);
            const colors = { '0': 'text-gray-400', '1': 'text-white', '2': 'text-green-400', '3': 'text-blue-400', '4': 'text-purple-400', '5': 'text-pink-400', '6': 'text-yellow-400', '7': 'text-orange-400', '8': 'text-red-400' };
            return colors[cls] || 'text-[#ff8c00]';
        }

        function renderAddedModules() {
            const container = document.getElementById('mod-build-list');
            if(addedModules.length === 0) {
                container.innerHTML = '';
                return;
            }
            container.innerHTML = addedModules.map((m, i) => {
                const col = getQueryColor(m);
                return `
                <div class="bg-[#111] ${col} text-[10px] px-2 py-1 rounded flex items-center border border-gray-700 font-bold">
                    ${m} 
                    <button onclick="removeModuleQuery(${i})" class="ml-2 text-red-500 hover:text-red-400">✕</button>
                </div>
            `}).join('');
        }

        function setFCat(cat) {
            ['Ship', 'Core', 'Optional', 'Hardpoint', 'Utility'].forEach(c => {
                const btn = document.getElementById('fcat-'+c);
                if(c === cat) {
                    btn.classList.replace('text-gray-500', 'text-[#ff8c00]');
                    btn.classList.add('bg-gray-800');
                } else {
                    btn.classList.replace('text-[#ff8c00]', 'text-gray-500');
                    btn.classList.remove('bg-gray-800');
                }
            });

            document.getElementById('mod-build-cat').value = cat;
            document.getElementById('mod-build-type').value = '';
            updateModBuildPreview();

            const container = document.getElementById('f-type-container');
            container.innerHTML = modTypes[cat].map(t => `
                <button id="ftyp-${t.replace(/[^a-zA-Z0-9]/g, '')}" onclick="setFType('${t}')" class="block w-full text-left px-2 py-1.5 mb-1 text-[9px] font-bold text-gray-400 hover:text-white bg-[#0a0a0a] border border-gray-800 rounded focus:outline-none transition-colors">
                    ${t}
                </button>
            `).join('');

            const crContainer = document.getElementById('f-class-rating-container');
            if(cat === 'Ship') {
                crContainer.classList.add('opacity-50', 'pointer-events-none');
                setFClass('');
                setFRating('');
            } else {
                crContainer.classList.remove('opacity-50', 'pointer-events-none');
            }
        }

        function setFClass(cls) {
            ['1','2','3','4','5','6','7','8'].forEach(c => {
                const btn = document.getElementById('fbtn-cls-'+c);
                if(btn) {
                    if(c === cls) {
                        btn.classList.replace('text-gray-500', 'text-[#ff8c00]');
                        btn.classList.add('bg-gray-800');
                    } else {
                        btn.classList.replace('text-[#ff8c00]', 'text-gray-500');
                        btn.classList.remove('bg-gray-800');
                    }
                }
            });
            document.getElementById('mod-build-class').value = cls;
            updateModBuildPreview();
        }

        function setFRating(rtg) {
            ['A','B','C','D','E','F','G','I'].forEach(r => {
                const btn = document.getElementById('fbtn-rtg-'+r);
                if(btn) {
                    if(r === rtg) {
                        btn.classList.replace('text-gray-500', 'text-[#ff8c00]');
                        btn.classList.add('bg-gray-800');
                    } else {
                        btn.classList.replace('text-[#ff8c00]', 'text-gray-500');
                        btn.classList.remove('bg-gray-800');
                    }
                }
            });
            document.getElementById('mod-build-rating').value = rtg;
            updateModBuildPreview();
        }

        function setFType(typ) {
            const cat = document.getElementById('mod-build-cat').value;
            modTypes[cat].forEach(t => {
                const btnId = 'ftyp-' + t.replace(/[^a-zA-Z0-9]/g, '');
                const btn = document.getElementById(btnId);
                if(btn) {
                    if(t === typ) {
                        btn.classList.replace('text-gray-400', 'text-white');
                        btn.classList.replace('border-gray-800', 'border-[#ff8c00]');
                        btn.classList.add('bg-gray-800');
                    } else {
                        btn.classList.replace('text-white', 'text-gray-400');
                        btn.classList.replace('border-[#ff8c00]', 'border-gray-800');
                        btn.classList.remove('bg-gray-800');
                    }
                }
            });
            document.getElementById('mod-build-type').value = typ;
            updateModBuildPreview();
        }

        function updateModBuildPreview() {
            const cat = document.getElementById('mod-build-cat').value;
            const cls = document.getElementById('mod-build-class').value;
            const rtg = document.getElementById('mod-build-rating').value;
            const typ = document.getElementById('mod-build-type').value;
            
            let res = '';
            if(typ) {
                if(cat === 'Ship') {
                    res = typ;
                } else {
                    if(cls && rtg) {
                        res = `${cls}${rtg} ${typ}`.trim();
                    }
                }
            }
            
            const addBtn = document.getElementById('mod-build-add-btn');
            let isValid = false;
            
            if(cat === 'Ship' && typ) isValid = true;
            if(cat !== 'Ship' && typ && cls && rtg) isValid = true;

            if(isValid) {
                addBtn.innerText = `+ ADD [ ${res.toUpperCase()} ]`;
                addBtn.classList.remove('opacity-50', 'pointer-events-none');
                addBtn.dataset.query = res;
            } else {
                addBtn.innerText = `+ ADD MODULE`;
                addBtn.classList.add('opacity-50', 'pointer-events-none');
                addBtn.dataset.query = '';
            }
        }

        let detailsData = {};
        let currentSearchResults = [];

        function openStationDetails(i) {
            document.getElementById('near-results-view').classList.add('hidden');
            document.getElementById('near-detail-view').classList.remove('hidden');
            
            const station = currentSearchResults[i];
            const arrivalDist = station.distance_to_arrival ? Math.round(station.distance_to_arrival) : '?';
            const padSize = station.has_large_pad ? 'L' : (station.small_pads > 0 ? 'S/M' : '?');

            let html = `
                <div class="text-[#ff8c00] font-black text-sm mb-1">${station.system_name.toUpperCase()}</div>
                <div class="text-white text-lg font-bold mb-2">${station.name.toUpperCase()}</div>
                <div class="grid grid-cols-2 gap-2 text-xs text-gray-400 border-b border-gray-800 pb-3 mb-3">
                    <div>TYPE: <span class="text-white">${station.type || 'Unknown'}</span></div>
                    <div>ARRIVAL: <span class="text-white">${arrivalDist} Ls</span></div>
                    <div>PAD: <span class="text-white">${padSize}</span></div>
                    <div>FACTION: <span class="text-white">${station.controlling_minor_faction || '-'}</span></div>
                </div>
            `;

            const hasMod = !!detailsData['mod-'+i];
            const hasShp = !!detailsData['shp-'+i];
            
            if (hasMod && hasShp) {
                html += `
                    <div class="flex border-b border-gray-800 mb-3 sticky top-0 bg-[#0a0a0a] z-10 pt-1">
                        <button onclick="switchDetTab('mod')" id="det-tab-mod" class="flex-1 text-[#ff8c00] font-bold border-b border-[#ff8c00] pb-1">MODULES</button>
                        <button onclick="switchDetTab('shp')" id="det-tab-shp" class="flex-1 text-gray-500 font-bold border-b border-transparent pb-1">SHIPS</button>
                    </div>
                    <div id="det-pane-mod">${detailsData['mod-'+i]}</div>
                    <div id="det-pane-shp" class="hidden">${detailsData['shp-'+i]}</div>
                `;
            } else if (hasMod) {
                html += `<div class="text-[#ff8c00] font-bold mb-2 tracking-widest border-b border-gray-800 pb-1 sticky top-0 bg-[#0a0a0a] z-10">MODULES</div>${detailsData['mod-'+i]}`;
            } else if (hasShp) {
                html += `<div class="text-green-500 font-bold mb-2 tracking-widest border-b border-gray-800 pb-1 sticky top-0 bg-[#0a0a0a] z-10">SHIPS</div>${detailsData['shp-'+i]}`;
            } else {
                html += `<div class="text-gray-500 text-center py-4 border border-gray-800 rounded bg-[#050505]">NO DETAILED INVENTORY AVAILABLE</div>`;
            }

            document.getElementById('near-detail-content').innerHTML = html;
        }

        function switchDetTab(tab) {
            if(tab === 'mod') {
                document.getElementById('det-pane-mod').classList.remove('hidden');
                document.getElementById('det-pane-shp').classList.add('hidden');
                document.getElementById('det-tab-mod').className = "flex-1 text-[#ff8c00] font-bold border-b border-[#ff8c00] pb-1";
                document.getElementById('det-tab-shp').className = "flex-1 text-gray-500 font-bold border-b border-transparent pb-1";
            } else {
                document.getElementById('det-pane-shp').classList.remove('hidden');
                document.getElementById('det-pane-mod').classList.add('hidden');
                document.getElementById('det-tab-shp').className = "flex-1 text-green-500 font-bold border-b border-green-500 pb-1";
                document.getElementById('det-tab-mod').className = "flex-1 text-gray-500 font-bold border-b border-transparent pb-1";
            }
        }
        
        function switchModTab(index, cat) {
            ['standard','internal','hardpoint','utility'].forEach(c => {
                const pane = document.getElementById(`mod-${index}-${c}`);
                const btn = document.getElementById(`mod-btn-${index}-${c}`);
                if(pane) pane.classList.add('hidden');
                if(btn) {
                    btn.classList.remove('text-[#ff8c00]', 'border-[#ff8c00]');
                    btn.classList.add('text-gray-500', 'border-transparent');
                }
            });
            const activePane = document.getElementById(`mod-${index}-${cat}`);
            const activeBtn = document.getElementById(`mod-btn-${index}-${cat}`);
            if(activePane) activePane.classList.remove('hidden');
            if(activeBtn) {
                activeBtn.classList.remove('text-gray-500', 'border-transparent');
                activeBtn.classList.add('text-[#ff8c00]', 'border-[#ff8c00]');
            }
        }

        function switchModSubTab(index, cat, typeIdx) {
            const parent = document.getElementById(`mod-${index}-${cat}`);
            if(!parent) return;
            parent.querySelectorAll('.sub-pane').forEach(p => p.classList.add('hidden'));
            parent.querySelectorAll('.sub-btn').forEach(b => {
                b.classList.remove('text-white', 'bg-gray-800');
                b.classList.add('text-gray-500', 'bg-transparent');
            });
            const activePane = document.getElementById(`mod-${index}-${cat}-typ-${typeIdx}`);
            const activeBtn = document.getElementById(`mod-btn-${index}-${cat}-typ-${typeIdx}`);
            if(activePane) activePane.classList.remove('hidden');
            if(activeBtn) {
                activeBtn.classList.remove('text-gray-500', 'bg-transparent');
                activeBtn.classList.add('text-white', 'bg-gray-800');
            }
        }

        function toggleDetails(id) {} // Deprecated, kept to prevent errors

        function getInternalId(query) {
            const ships = {
                'Adder': 'adder', 'Alliance Challenger': 'alliance_challenger', 'Alliance Chieftain': 'alliance_chieftain',
                'Alliance Crusader': 'alliance_crusader', 'Anaconda': 'anaconda', 'Asp Explorer': 'asp',
                'Asp Scout': 'asp_scout', 'Beluga Liner': 'beluga', 'Cobra Mk III': 'cobra_mkiii',
                'Cobra Mk IV': 'cobramkiv', 'Diamondback Explorer': 'diamondback', 'Diamondback Scout': 'diamondback_probus',
                'Dolphin': 'dolphin', 'Eagle': 'eagle', 'Federal Assault Ship': 'federal_assault_ship',
                'Federal Corvette': 'federal_corvette', 'Federal Dropship': 'federal_dropship',
                'Federal Gunship': 'federal_gunship', 'Fer-de-Lance': 'ferdelance', 'Hauler': 'hauler',
                'Imperial Clipper': 'clipper', 'Imperial Courier': 'empire_courier', 'Imperial Cutter': 'cutter',
                'Imperial Eagle': 'empire_eagle', 'Keelback': 'keelback', 'Krait Mk II': 'krait_mkii',
                'Krait Phantom': 'krait_light', 'Mamba': 'mamba', 'Mandalay': 'mandalay', 'Orca': 'orca',
                'Python': 'python', 'Python Mk II': 'python_p_2', 'Sidewinder': 'sidewinder',
                'Type-6 Transporter': 'type6', 'Type-7 Transporter': 'type7', 'Type-8 Transporter': 'type8',
                'Type-9 Heavy': 'type9', 'Type-10 Defender': 'type10', 'Viper Mk III': 'viper',
                'Viper Mk IV': 'viper_mkiv', 'Vulture': 'vulture'
            };

            if (ships[query]) return ships[query];

            const match = query.match(/^([1-8])([A-I])\s+(.+)$/);
            if (!match) return query.toLowerCase().replace(/\s+/g, '_');

            const cls = match[1];
            const rtg = match[2];
            const type = match[3];

            const rtgMap = { 'A': 5, 'B': 4, 'C': 3, 'D': 2, 'E': 1, 'F': 1, 'G': 1, 'I': 1 };
            const rtgDigit = rtgMap[rtg] || 1;

            const typeMap = {
                'Frame Shift Drive': 'hyperdrive',
                'SCO Frame Shift Drive': 'hyperdrive_overcharge',
                'Power Plant': 'powerplant',
                'Thrusters': 'engine',
                'Life Support': 'lifesupport',
                'Power Distributor': 'powerdistributor',
                'Sensors': 'sensors',
                'Fuel Tank': 'fueltank',
                'Shield Generator': 'shieldgenerator',
                'Fuel Scoop': 'fuelscoop',
                'Shield Cell Bank': 'shieldcellbank',
                'Cargo Rack': 'cargorack',
                'Planetary Vehicle Hangar': 'vesselbay',
                'Detailed Surface Scanner': 'detailedsurfacescanner',
                'Collector Limpet Controller': 'limpetcontroller_collector'
            };

            const internalName = typeMap[type] || type.toLowerCase().replace(/\s+/g, '');
            return `int_${internalName}_size${cls}_class${rtgDigit}`;
        }

        function searchNearest() {
            const system = document.getElementById('near-sys-input').value;
            addRecentSystem(system);
            const service = document.getElementById('near-service-input').value;
            if (!system) return;
            
            document.getElementById('near-loading').classList.remove('hidden');
            detailsData = {};
            
            const pad = document.getElementById('near-pad-input').value;
            const surface = document.getElementById('near-surface-input').value;
            const arrival = document.getElementById('near-arrival-input').value;
            const fc = document.getElementById('near-fc-input').value;

            const mappedService = service;

            const payload = {
                filters: {},
                sort: [{ distance: { direction: "asc" } }],
                size: 50,
                reference_system: system
            };

            if (mappedService && mappedService !== "Any") {
                payload.filters.services = { values: [mappedService] };
            }

            if (pad === 'large') payload.filters.has_large_pad = { value: true };
            if (surface === 'no') payload.filters.is_planetary = { value: false };
            if (arrival !== 'any') payload.filters.distance_to_arrival = { min: 0, max: parseInt(arrival) };

            let modulesToSearch = [...addedModules];
            const addBtn = document.getElementById('mod-build-add-btn');
            const currentPreview = addBtn ? addBtn.dataset.query : '';
            if (modulesToSearch.length === 0 && currentPreview) modulesToSearch.push(currentPreview);

            if (modulesToSearch.length > 0) {
                const shipsList = modTypes['Ship'];
                const selectedShips = modulesToSearch.filter(m => shipsList.includes(m)).map(s => getInternalId(s));
                const selectedModules = modulesToSearch.filter(m => !shipsList.includes(m)).map(m => getInternalId(m));
                
                if (selectedModules.length > 0) payload.filters.modules = { values: selectedModules };
                if (selectedShips.length > 0) payload.filters.ships = { values: selectedShips };
            }

            fetch('/api/proxy/spansh', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                document.getElementById('near-loading').classList.add('hidden');
                document.getElementById('near-search-view').classList.add('hidden');
                document.getElementById('near-results-view').classList.remove('hidden');
                
                const shortService = service.split(' ')[0] + (service.includes('Trader') ? ' Trader' : '');
                document.getElementById('near-results-title').innerText = `${shortService} NEAR ${system}`;
                
                if(data && data.results && data.results.length > 0) {
                    let finalResults = data.results;
                    if (fc === 'no') {
                        finalResults = finalResults.filter(r => 
                            r.type !== 'Fleet Carrier' && 
                            r.type !== 'Drake-Class Carrier' && 
                            !r.name.includes('Carrier') &&
                            r.type !== 'Mega Ship'
                        );
                    }
                    finalResults = finalResults.slice(0, 15);
                    currentSearchResults = finalResults;

                    if(finalResults.length === 0) {
                        document.getElementById('near-list').innerHTML = '<div class="text-center text-gray-500 my-4">NO MATCHING STATIONS FOUND</div>';
                        return;
                    }

                    const html = finalResults.map((r, i) => {
                        const dist = r.distance ? Math.round(r.distance) : '?';
                        const arrivalDist = r.distance_to_arrival ? Math.round(r.distance_to_arrival) : '?';
                        const padSize = r.has_large_pad ? 'L' : (r.small_pads > 0 ? 'S/M' : '?');
                        
                        if (r.modules && r.modules.length > 0) {
                            const cats = {
                                'standard': r.modules.filter(m => m.category === 'standard'),
                                'internal': r.modules.filter(m => m.category === 'internal'),
                                'hardpoint': r.modules.filter(m => m.category === 'hardpoint'),
                                'utility': r.modules.filter(m => m.category === 'utility')
                            };
                            
                            let tabsHtml = `<div class="flex border-b border-gray-800 mb-2 sticky top-0 bg-black/90 z-10 pt-1">`;
                            tabsHtml += `<button id="mod-btn-${i}-standard" onclick="switchModTab(${i}, 'standard')" class="flex-1 text-[9px] text-[#ff8c00] font-bold border-b border-[#ff8c00] pb-1">CORE</button>`;
                            tabsHtml += `<button id="mod-btn-${i}-internal" onclick="switchModTab(${i}, 'internal')" class="flex-1 text-[9px] text-gray-500 font-bold border-b border-transparent pb-1">OPT</button>`;
                            tabsHtml += `<button id="mod-btn-${i}-hardpoint" onclick="switchModTab(${i}, 'hardpoint')" class="flex-1 text-[9px] text-gray-500 font-bold border-b border-transparent pb-1">WEP</button>`;
                            tabsHtml += `<button id="mod-btn-${i}-utility" onclick="switchModTab(${i}, 'utility')" class="flex-1 text-[9px] text-gray-500 font-bold border-b border-transparent pb-1">UTIL</button>`;
                            tabsHtml += `</div>`;
                            
                            const sizeColors = { 0: 'text-gray-400', 1: 'text-white', 2: 'text-green-400', 3: 'text-blue-400', 4: 'text-purple-400', 5: 'text-yellow-400', 6: 'text-orange-400', 7: 'text-red-400', 8: 'text-pink-400' };

                            let panesHtml = '';
                            ['standard','internal','hardpoint','utility'].forEach((c, idx) => {
                                const hidden = idx === 0 ? '' : 'hidden';
                                let catHtml = `<div id="mod-${i}-${c}" class="${hidden}">`;
                                if (cats[c].length === 0) {
                                    catHtml += `<div class="text-[9px] text-gray-600 text-center py-2">NONE</div></div>`;
                                } else {
                                    const types = [...new Set(cats[c].map(m => m.name || 'Unknown'))].sort();
                                    catHtml += `<div class="flex gap-2 items-start mt-2">`;
                                    catHtml += `<div class="flex flex-col border border-gray-800/50 rounded bg-[#050505] w-[35%] max-h-[350px] overflow-y-auto" style="scrollbar-width: none;">`;
                                    types.forEach((tName, tIdx) => {
                                        const btnActive = tIdx === 0 ? 'text-white bg-gray-800' : 'text-gray-500 bg-transparent';
                                        const shortName = tName.length > 25 ? tName.substring(0,25) + '..' : tName;
                                        catHtml += `<button id="mod-btn-${i}-${c}-typ-${tIdx}" onclick="switchModSubTab(${i}, '${c}', ${tIdx})" class="sub-btn text-left text-[9px] ${btnActive} font-bold p-2 border-b border-gray-800/50 uppercase transition-colors">${shortName}</button>`;
                                    });
                                    catHtml += `</div>`;
                                    catHtml += `<div class="flex-1 flex flex-col min-w-0 max-h-[350px] overflow-y-auto pr-1">`;
                                    types.forEach((tName, tIdx) => {
                                        const pHidden = tIdx === 0 ? '' : 'hidden';
                                        catHtml += `<div id="mod-${i}-${c}-typ-${tIdx}" class="sub-pane ${pHidden}">`;
                                        const itemsInType = cats[c].filter(m => (m.name||'Unknown') === tName);
                                        itemsInType.sort((a,b) => (b.class||0) - (a.class||0) || (a.rating||'').localeCompare(b.rating||''));
                                        const itemsHtml = itemsInType.map(m => {
                                            const col = sizeColors[m.class] || 'text-white';
                                            const shipSpec = m.ship ? `<div class="text-[8px] text-gray-600 mt-0.5">(${m.ship})</div>` : '';
                                            return `<div class="text-[9px] border border-gray-800 p-1.5 rounded mb-1 bg-[#111] flex flex-col justify-center"><div class="flex justify-between items-center"><span class="${col} font-bold">${m.class||''}${m.rating||''} ${m.name}</span><span class="text-gray-400">${(m.price||0).toLocaleString()} CR</span></div>${shipSpec}</div>`;
                                        }).join('');
                                        catHtml += itemsHtml + `</div>`;
                                    });
                                    catHtml += `</div></div>`;
                                }
                                catHtml += `</div>`;
                                panesHtml += catHtml;
                            });
                            detailsData['mod-'+i] = tabsHtml + panesHtml;
                        }
                        if (r.ships && r.ships.length > 0) {
                            detailsData['shp-'+i] = r.ships.map(s => `<div class="text-[9px] border border-gray-800 p-1 rounded mb-1 text-gray-300 flex justify-between"><span>${s.name}</span><span class="text-gray-500">${(s.price||0).toLocaleString()} CR</span></div>`).join('');
                        }

                        return `
                        <div onclick="openStationDetails(${i})" class="bg-[#111] p-3 border border-gray-800 rounded relative flex flex-col cursor-pointer hover:border-gray-600 transition-colors">
                            <div class="text-[#ff8c00] font-black text-sm mb-1">${r.system_name.toUpperCase()}</div>
                            <div class="text-gray-300 font-bold mb-1">${r.name.toUpperCase()}</div>
                            <div class="grid grid-cols-2 gap-1 text-[10px] text-gray-500 mt-2 border-t border-gray-800 pt-2">
                                <div>TYPE: <span class="text-white">${r.type || 'Unknown'}</span></div>
                                <div>ARRIVAL: <span class="text-white">${arrivalDist} Ls</span></div>
                                <div>PAD: <span class="text-white">${padSize}</span></div>
                                <div>FACTION: <span class="text-white">${(r.controlling_minor_faction || '-').substring(0,15)}</span></div>
                            </div>
                            <div class="text-[9px] text-orange-500 mt-2 font-bold text-right pt-2 border-t border-gray-800">VIEW DETAILS ▶</div>
                        </div>`;
                    }).join('');
                    document.getElementById('near-list').innerHTML = html;
                } else {
                    document.getElementById('near-list').innerHTML = '<div class="text-center text-gray-500 my-4">NO RESULTS FOUND OR SYSTEM NOT RECOGNIZED</div>';
                }
            })
            .catch(err => {
                document.getElementById('near-loading').classList.add('hidden');
                alert("Ağ hatası: " + err);
            });
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
        updateRecentSystemsUI();
        setService('Outfitting');
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

@app.route('/api/proxy/spansh', methods=['POST'])
def spansh_proxy():
    url = "https://spansh.co.uk/api/stations/search"
    req_data = flask_request.get_data()
    req = urllib.request.Request(url, data=req_data, headers={'Content-Type': 'application/json', 'User-Agent': 'EliteControlPanel/1.0'})
    try:
        with urllib.request.urlopen(req) as response:
            return response.read(), response.status, {'Content-Type': 'application/json'}
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)