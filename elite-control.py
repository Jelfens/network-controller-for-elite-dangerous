from flask import Flask, jsonify, render_template_string
import json
import os
import sys
import platform
import subprocess

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
        body { background-color: #050505; }
        .ed-text { color: #ff8c00; }
        .ed-border { border-color: #ff8c00; }
        .ed-glow { text-shadow: 0 0 8px rgba(255,140,0,0.6); }
        .btn:active, .ind-btn:active { transform: scale(0.95); opacity: 0.8; }
        .ind-off { border-color: #374151; color: #4B5563; background: #0a0a0a; }
        .ind-on { border-color: #ff8c00; color: #ff8c00; background: rgba(255,140,0,0.05); box-shadow: 0 0 12px rgba(255,140,0,0.4) inset, 0 0 12px rgba(255,140,0,0.4); }
        .ind-safe { border-color: #10B981; color: #10B981; background: rgba(16,185,129,0.05); box-shadow: 0 0 12px rgba(16,185,129,0.4) inset, 0 0 12px rgba(16,185,129,0.4); }
        .fg-on { background-color: #ff8c00; color: #111827; border-color: #ff8c00; box-shadow: 0 0 12px rgba(255,140,0,0.6); }
        .fg-off { background-color: #111827; color: #4B5563; border-color: #374151; }
        .section-title {
            background: linear-gradient(90deg, rgba(255,140,0,0.15) 0%, rgba(0,0,0,0) 100%);
            border-left: 4px solid #ff8c00;
        }
    </style>
</head>
<body class="text-gray-300 font-mono p-3 select-none flex flex-col min-h-screen tracking-tight">

    <h2 class="text-2xl font-black ed-text tracking-[0.3em] mb-6 text-center border-y border-gray-800 py-3 bg-gradient-to-r from-transparent via-orange-900/20 to-transparent ed-glow">
        COCKPIT CONTROL
    </h2>

    <div class="mb-5">
        <h3 class="text-sm font-black ed-text mb-3 uppercase tracking-widest pl-3 py-1 section-title ed-glow">Systems & Control</h3>
        
        <div class="grid grid-cols-4 gap-2 text-center text-xs font-bold mb-4" id="indicators">
            <div id="ind-shield" class="border rounded p-2 ind-off transition-all">SHIELD</div>
            <div id="ind-hardp" onclick="komut('wg-hardpoints')" class="ind-btn cursor-pointer border rounded p-2 ind-off transition-all">WEAPONS</div>
            <div id="ind-gear" onclick="komut('landing-gear')" class="ind-btn cursor-pointer border rounded p-2 ind-off transition-all">GEAR</div>
            <div id="ind-cargo" onclick="komut('cargo-scoop')" class="ind-btn cursor-pointer border rounded p-2 ind-off transition-all">SCOOP</div>
            <div id="ind-light" onclick="komut('lights')" class="ind-btn cursor-pointer border rounded p-2 ind-off transition-all">LIGHTS</div>
            <div id="ind-nv" onclick="komut('night-vision')" class="ind-btn cursor-pointer border rounded p-2 ind-off transition-all">N-VISION</div>
            <div id="ind-silent" onclick="komut('silent-running')" class="ind-btn cursor-pointer border rounded p-2 ind-off transition-all">SILENT</div>
            <div id="ind-sc" onclick="komut('fsd')" class="ind-btn cursor-pointer border rounded p-2 ind-off transition-all">FSD / SC</div>
        </div>
        
        <div class="grid grid-cols-1 gap-3 bg-[#0a0a0a] p-3 rounded border border-gray-800 shadow-[0_0_15px_rgba(0,0,0,0.5)] inset">
            
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
            <button onclick="komut('pip-rst')" class="btn w-full mt-1 border border-gray-800 bg-[#0f0f0f] text-gray-500 rounded p-2 text-xs font-black hover:border-gray-500 tracking-[0.3em]">RESET PIPS</button>
            
            <div class="mt-1 border-t border-gray-800 pt-3 flex items-center justify-between gap-2">
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

    <h3 class="text-sm font-black ed-text mb-3 uppercase tracking-widest pl-3 py-1 section-title ed-glow">Tactical & Navigation</h3>
    <div class="grid grid-cols-4 gap-2 mb-5 text-xs font-bold">
        <button onclick="komut('heatsink')" class="btn border border-gray-800 bg-[#0a0a0a] text-blue-500 rounded p-3 hover:border-blue-500 hover:shadow-[0_0_10px_rgba(59,130,246,0.2)]">HEATSNK</button>
        <button onclick="komut('chaff')" class="btn border border-gray-800 bg-[#0a0a0a] text-yellow-500 rounded p-3 hover:border-yellow-500 hover:shadow-[0_0_10px_rgba(234,179,8,0.2)]">CHAFF</button>
        <button onclick="komut('scb')" class="btn border border-gray-800 bg-[#0a0a0a] text-teal-400 rounded p-3 col-span-2 hover:border-teal-400 hover:shadow-[0_0_10px_rgba(45,212,191,0.2)]">SHIELD CELL</button>
        
        <button onclick="komut('galaxy-map')" class="btn border border-gray-800 bg-[#0a0a0a] text-gray-400 rounded p-3 hover:border-gray-400">GAL MAP</button>
        <button onclick="komut('system-map')" class="btn border border-gray-800 bg-[#0a0a0a] text-gray-400 rounded p-3 hover:border-gray-400">SYS MAP</button>
        <button onclick="komut('fss')" class="btn border border-gray-800 bg-[#0a0a0a] text-purple-400 rounded p-3 hover:border-purple-400 hover:shadow-[0_0_10px_rgba(192,132,252,0.2)]">FSS</button>
        <button onclick="komut('cockpit-mode')" class="btn border border-gray-800 bg-[#0a0a0a] text-indigo-400 rounded p-3 hover:border-indigo-400 hover:shadow-[0_0_10px_rgba(129,140,248,0.2)]">HUD MODE</button>
        
        <button onclick="komut('menu')" class="btn border border-gray-600 bg-gray-800 text-white rounded p-3 col-span-4 hover:border-white shadow-[0_0_10px_rgba(255,255,255,0.1)] tracking-widest">MENU (ESC)</button>
    </div>

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

    <div class="mt-auto border-t border-gray-800 pt-3 grid grid-cols-2 gap-3 text-[10px] text-gray-400 font-bold tracking-wider mb-4">
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

    <div class="mt-2 text-center text-xl font-black text-gray-600 tracking-[0.2em]" id="sys-clock">
        00:00:00 LOC
    </div>

    <script>
        const guiFocusMap = {0: "COCKPIT", 1: "LEFT PANEL", 2: "RIGHT PANEL", 3: "COMMS", 4: "ROLE PANEL", 5: "STATION", 6: "GALAXY MAP", 7: "SYSTEM MAP", 8: "ORION", 9: "FSS", 10: "SAA", 11: "CODEX"};

        function updateClock() {
            const now = new Date();
            document.getElementById('sys-clock').innerText = now.toLocaleTimeString('en-GB', { hour12: false }) + " LOC";
        }
        setInterval(updateClock, 1000);
        updateClock();

        function komut(id) {
            fetch('/action/' + id);
            if (navigator.vibrate) navigator.vibrate(40);
        }

        function setInd(id, is_active, safe_mode = false) {
            const el = document.getElementById(id);
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
                    document.getElementById('txt-fuel-main').innerText = d.Fuel.FuelMain.toFixed(1) + ' T';
                }

                if (d.FireGroup !== undefined) {
                    for(let i=0; i<8; i++) {
                        let fgEl = document.getElementById('fg-' + i);
                        if (fgEl) fgEl.className = `border w-6 h-6 flex items-center justify-center text-xs font-bold rounded transition-all ${d.FireGroup === i ? 'fg-on' : 'fg-off'}`;
                    }
                }

                if (d.Balance !== undefined) {
                    document.getElementById('txt-cr').innerText = d.Balance.toLocaleString() + ' CR';
                }
                if (d.Cargo !== undefined) {
                    document.getElementById('txt-cargo').innerText = d.Cargo + ' T';
                }

                document.getElementById('txt-dest').innerText = d.Destination ? d.Destination.Name : 'NONE';
                document.getElementById('txt-body').innerText = d.BodyName || 'NONE';
                document.getElementById('txt-gui').innerText = d.GuiFocus !== undefined ? (guiFocusMap[d.GuiFocus] || d.GuiFocus) : 'NONE';

                if (d.Latitude !== undefined) {
                    document.getElementById('txt-lat').innerText = d.Latitude.toFixed(4);
                    document.getElementById('txt-lon').innerText = d.Longitude.toFixed(4);
                    document.getElementById('txt-alt').innerText = Math.round(d.Altitude).toLocaleString();
                    document.getElementById('txt-hdg').innerText = Math.round(d.Heading) + '°';
                } else {
                    document.getElementById('txt-lat').innerText = '-';
                    document.getElementById('txt-lon').innerText = '-';
                    document.getElementById('txt-alt').innerText = '-';
                    document.getElementById('txt-hdg').innerText = '-';
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
    app.run(host='0.0.0.0', port=5000)