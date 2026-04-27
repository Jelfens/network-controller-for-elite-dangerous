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

* **OS:** Windows (Required for `pydirectinput` and default game paths).
* **Python:** 3.6 or higher.
* **Game:** Elite Dangerous (Odyssey or Horizons).

## 📦 Installation

1.  **Download the script:** Save `app.py` to a folder.
2.  **Install dependencies:**
    ```bash
    pip install flask pydirectinput
    ```

## 🎮 How to Use

1.  **Run the script:**
    ```bash
    python app.py
    ```
2.  **Connect via Browser:**
    * **Local:** Go to `http://localhost:5000`.
    * **Mobile:** Find your PC's local IP (e.g., `192.168.1.X`) and enter `http://192.168.1.X:5000`.
3.  **Ensure Game Focus:** Elite Dangerous must be the active window for controls to work.

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

* **Status.json:** The script looks for the file in `~\Saved Games\Frontier Developments\Elite Dangerous\Status.json`.
* **Network:** Both your PC and mobile device must be on the same local network (Wi-Fi).
* **Safety:** This is a development server for personal local use. Do not expose port 5000 to the public internet.

---
*Fly Dangerously, Commander! o7*
