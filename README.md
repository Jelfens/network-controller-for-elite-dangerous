# Network Controller for Elite Dangerous

A lightweight Python-based local network controller designed specifically for **Elite Dangerous**. This script hosts a responsive, Elite Dangerous-themed web interface on your local network, allowing you to control your ship's systems and monitor live telemetry directly from your smartphone, tablet, or another monitor.

## 🚀 Features

* **Real-time Telemetry:** Reads data directly from Elite Dangerous's `Status.json` file.
* **Live Cockpit Indicators:** Visual feedback for Shields, Hardpoints, Landing Gear, Cargo Scoop, Lights, Night Vision, Silent Running, and FSD.
* **Dynamic Information Displays:** Real-time updates for:
    * Fuel (Main Tank)
    * Power Distributor (PIPS) status with graphical bars
    * Active Fire Group (A-H)
    * Credit Balance
    * Cargo Capacity
    * Navigation Data (Destination, Body Focus, GUI Focus)
    * Planetary Surface Data (Latitude, Longitude, Altitude, Heading)
* **Direct Control:** Send keystrokes to your PC directly from the web interface.
* **Elite Dangerous Theme:** A custom dark and orange UI (`Tailwind CSS`) matching the in-game HUD.
* **System Clock:** Integrated local time display for long sessions.

## 🛠️ Requirements

* **OS:** Windows or Linux (macOS not tested).
* **Python:** 3.6 or higher.
* **Game:** Elite Dangerous (Odyssey or Horizons).
* **For Linux:** `xdotool` for keyboard control.

## 📦 Installation

### Windows

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Linux

1.  **Run the automated setup:**
    ```bash
    chmod +x setup-linux.sh
    ./setup-linux.sh
    ```

    **Or manually:**
    ```bash
    # Install system dependencies
    sudo apt update
    sudo apt install xdotool python3-venv

    # Create and activate virtual environment
    python3 -m venv .venv
    source .venv/bin/activate

    # Install Python dependencies
    pip install -r requirements.txt
    ```

## 🎮 How to Use

### Windows

1.  **Run the script:**
    ```bash
    python elite-control.py
    ```

### Linux

1.  **Activate virtual environment:**
    ```bash
    source .venv/bin/activate
    ```

2.  **Run the script:**
    ```bash
    python elite-control.py
    ```

### Connect via Browser

* **Local:** Go to `http://localhost:5000`.
* **Mobile/Remote:** Find your PC's local IP (e.g., `192.168.1.X`) and enter `http://192.168.1.X:5000`.

### ⚠️ Important for Keyboard Control

- **Windows:** Elite Dangerous must be the active/focused window.
- **Linux:** The game window must be active. For Proton/Steam games, ensure the game is running in focus.

## ⌨️ Default Keybindings

Ensure your in-game settings match these keys (or edit the `KOMUTLAR` dictionary in the script):

| Action | Key | Action | Key |
| :--- | :--- | :--- | :--- |
| Hardpoints | `U` | Heatsink | `V` |
| Landing Gear | `L` | Chaff | `C` |
| Cargo Scoop | `Home` | Shield Cell | `B` |
| Lights | `Insert` | Galaxy Map | `M` |
| Night Vision | `N` | System Map | `O` |
| Silent Running | `Delete` | FSS Mode | `'` |
| FSD / SC | `J` | HUD Mode | `\` |
| PIPS Control | `Arrows` | Fire Groups | `[` and `]` |
| Menu | `ESC` | | |

## ⚠️ Important Notes

* **Status.json Location:**
  - **Windows:** `~\Saved Games\Frontier Developments\Elite Dangerous\Status.json`
  - **Linux (Proton/Steam):** `~/.steam/root/drive_c/users/steamuser/Saved Games/Frontier Developments/Elite Dangerous/Status.json`
  - **Linux (Wine):** Check your Wine prefix location
  
  The script automatically searches for the file in common locations.

* **Network:** Both your PC and mobile device must be on the same local network (Wi-Fi).
* **Safety:** This is a development server for personal local use. Do not expose port 5000 to the public internet.
* **Linux users:** Make sure `xdotool` is installed for keyboard control to work.

## 🐧 Linux Troubleshooting

### xdotool not sending keys

If keyboard controls aren't working on Linux:
1. Make sure the game window is focused/active
2. Verify xdotool is installed: `which xdotool`
3. Test xdotool manually: `xdotool key u` (should send 'u' key)

### Status.json not found

The script checks multiple common paths. If it still can't find your file:
1. Find your Status.json: `find ~ -name "Status.json" 2>/dev/null`
2. Update the `possible_paths` list in the script with your actual path

---
*Fly Dangerously, Commander! o7*
