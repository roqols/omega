# 👁️ OMEGA — Roblox ESP Overlay

> External ESP overlay for Roblox using memory reading and a transparent OpenGL overlay.  
> Works via `ReadProcessMemory` — no injection, no DLL.

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-Educational-red)](#-license)

</div>

---

## ✨ Features

| Feature | Description |
|---|---|
| **ESP Box** | 2D bounding box around players (full or corner style) |
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
- Python **3.10+** *(setup.bat installs it automatically if missing)*
- Roblox (`RobloxPlayerBeta.exe`) running
- **Run as Administrator** (required for memory reading)

### Python Dependencies

```
PyQt5
PyOpenGL
numpy
psutil
requests
```

> `setup.bat` checks and installs all missing dependencies automatically.

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/roqols/omega.git
cd omega
```

### 2. Run the setup

```
Right-click setup.bat → Run as administrator
```

The setup will:
- Install **Python 3.12** via `winget` if not present
- Check and install all missing Python packages
- Register the `omega` command system-wide

### 3. Launch from anywhere

Open any **new** CMD window and type:

```
omega
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
ESP_CORNER_BOX    = False
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
├── omega.py      # Main script — ESP logic + overlay
├── setup.bat     # Auto-installer + system command register
└── README.md     # This file
```

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
→ Wait a few seconds after launching Roblox before running `omega`.

**`omega` command not found after setup**  
→ Close the current CMD window and open a **new** one.  
→ If still missing, re-run `setup.bat` as Administrator.

**Offsets mismatch warning on startup**  
→ Roblox updated and the remote offsets haven't caught up yet. Wait a few hours and try again.

**Python was installed but `omega` still doesn't work**  
→ Close CMD and open a new window so the updated PATH takes effect.

---

## 📜 License

This project is for **educational purposes only**.  
Use at your own risk. The author is not responsible for any consequences.
