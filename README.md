# 👁️ OMEGA — Roblox ESP Overlay

> External ESP overlay for Roblox using memory reading and a transparent OpenGL overlay.  
> Works via `ReadProcessMemory` — no injection, no DLL.

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
- Python **3.10+**
- Roblox (RobloxPlayerBeta.exe) running
- **Run as Administrator** (required for memory reading)

### Python Dependencies

```
PyQt5
PyOpenGL
numpy
psutil
requests
```

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/youruser/omega.git
cd omega
```

### 2. Run the setup (installs everything + registers `omega` command)

```bat
setup.bat
```

> ⚠️ Run `setup.bat` as **Administrator** so it can register the system command.

### 3. Launch from anywhere

After setup, open any CMD window and type:

```
omega
```

---

## ⚙️ Configuration

All settings are at the top of `main.py`:

```python
# Toggle features
ENABLE_ESP       = True

# Visual settings
ESP_SHOW_BOX      = True
ESP_SHOW_TRACER   = True
ESP_SHOW_NAME     = True
ESP_SHOW_DISTANCE = True
ESP_SHOW_HEALTH   = True
ESP_CORNER_BOX    = False   # Corner-style box instead of full rectangle
ESP_DYNAMIC_HEALTH_COLOR = True  # Health bar color changes with HP

# Colors [R, G, B, A]
ESP_BOX_COLOR      = [255, 255, 255, 255]
ESP_TRACER_COLOR   = [255, 255, 255, 255]
ESP_NAME_COLOR     = [255, 255, 255, 255]
ESP_DISTANCE_COLOR = [255, 255, 255, 255]
ESP_HEALTH_COLOR   = [0, 255, 0, 255]

# Filters
IGNORE_TEAM   = True   # Skip players on your team
IGNORE_DEAD   = True   # Skip dead players
MAX_DISTANCE  = 500    # Max distance in studs (0 = unlimited)

# Debug
DEBUG_MODE = True      # Show console logs
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
omega/
├── main.py          # Main script (ESP logic + overlay)
├── setup.bat        # Installer & system command register
└── README.md        # This file
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

Offsets are fetched remotely and versioned — they auto-update when Roblox updates.

---

## ❓ FAQ

**The overlay shows nothing / ESP is blank**  
→ Make sure you're running as Administrator.  
→ Wait a few seconds after launching Roblox before starting OMEGA.

**`omega` command not found after setup**  
→ Close and reopen CMD after running `setup.bat`.  
→ Or re-run `setup.bat` as Administrator.

**Offsets mismatch warning**  
→ The remote server hasn't updated yet after a Roblox update. Wait a few hours and try again.

---

## 📜 License

This project is for **educational purposes only**.  
Use at your own risk. The author is not responsible for any consequences.
