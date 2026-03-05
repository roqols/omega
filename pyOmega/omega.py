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

# ====================================
# IMPORTS
# ====================================
import sys
import os
import traceback
from ctypes import *
from ctypes.wintypes import DWORD, LONG, BYTE, HMODULE
from struct import unpack, pack
from numpy import array, float32, dot
from math import sqrt
from time import time, sleep
from threading import Thread
from requests import get
from psutil import Process, HIGH_PRIORITY_CLASS, process_iter, NoSuchProcess
from PyQt5.QtWidgets import QApplication, QOpenGLWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QSurfaceFormat, QFont, QPainter, QPen
from OpenGL.GL import *

# ====================================
# OCULTAR JANELA DE CONSOLE
# ====================================
if not DEBUG_MODE:
    hwnd = windll.kernel32.GetConsoleWindow()
    if hwnd:
        windll.user32.ShowWindow(hwnd, 0)

# ====================================
# CONSTANTES WINDOWS API
# ====================================
PROCESS_ALL_ACCESS  = 0x1F0FFF
TH32CS_SNAPPROCESS  = 0x00000002
TH32CS_SNAPMODULE   = 0x00000008 | 0x00000010
GWL_EXSTYLE         = -20
WS_EX_LAYERED       = 0x80000
WS_EX_TRANSPARENT   = 0x20

# ====================================
# ESTRUTURAS
# ====================================
class PROCESSENTRY32(Structure):
    _fields_ = [
        ("dwSize",           DWORD),
        ("cntUsage",         DWORD),
        ("th32ProcessID",    DWORD),
        ("th32DefaultHeapID",c_void_p),
        ("th32ModuleID",     DWORD),
        ("cntThreads",       DWORD),
        ("th32ParentProcessID", DWORD),
        ("pcPriClassBase",   c_ulong),
        ("dwFlags",          DWORD),
        ("szExeFile",        c_wchar * 260),
    ]

class MODULEENTRY32(Structure):
    _fields_ = [
        ("dwSize",       DWORD),
        ("th32ModuleID", DWORD),
        ("th32ProcessID",DWORD),
        ("GlblcntUsage", DWORD),
        ("ProccntUsage", DWORD),
        ("modBaseAddr",  c_void_p),
        ("modBaseSize",  DWORD),
        ("hModule",      HMODULE),
        ("szModule",     c_char * 256),
        ("szExePath",    c_char * 260),
    ]

class RECT(Structure):
    _fields_ = [('left', LONG), ('top', LONG), ('right', LONG), ('bottom', LONG)]

class POINT(Structure):
    _fields_ = [('x', LONG), ('y', LONG)]

# ====================================
# MEMORY CLASS
# ====================================
class Memory:
    def __init__(self):
        self.process_handle = None
        self.process_id     = 0
        self.base_address   = 0

    def get_pid_by_name(self, process_name):
        try:
            for proc in process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and proc.info['name'].lower() == process_name.lower():
                        log(f'[+] Process found: {proc.info["name"]} (PID: {proc.info["pid"]})')
                        return proc.info['pid']
                except:
                    continue
        except Exception as e:
            log(f'[!] Error searching for process: {e}')

        try:
            snapshot = windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
            if snapshot == -1:
                return None
            entry = PROCESSENTRY32()
            entry.dwSize = sizeof(PROCESSENTRY32)
            if windll.kernel32.Process32FirstW(snapshot, byref(entry)):
                while True:
                    try:
                        if entry.szExeFile.lower() == process_name.lower():
                            pid = entry.th32ProcessID
                            windll.kernel32.CloseHandle(snapshot)
                            log(f'[+] Process found: {entry.szExeFile} (PID: {pid})')
                            return pid
                    except:
                        pass
                    if not windll.kernel32.Process32NextW(snapshot, byref(entry)):
                        break
            windll.kernel32.CloseHandle(snapshot)
        except Exception as e:
            log(f'[!] Error: {e}')
        return None

    def open_process(self, pid):
        try:
            self.process_id     = pid
            self.process_handle = windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
            if not self.process_handle or self.process_handle == 0:
                self.process_handle = windll.kernel32.OpenProcess(
                    0x0010 | 0x0400, False, pid
                )
            if self.process_handle and self.process_handle != 0:
                log(f'[+] Process opened! Handle: {self.process_handle}')
                return True
            log(f'[!] Failed to open process. Error: {windll.kernel32.GetLastError()}')
            log('[!] Run as Administrator!')
            return False
        except Exception as e:
            log(f'[!] Exception: {e}')
            return False

    def get_module_base(self, module_name="RobloxPlayerBeta.exe"):
        try:
            snapshot = windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, self.process_id)
            if snapshot == -1:
                return 0
            entry = MODULEENTRY32()
            entry.dwSize = sizeof(MODULEENTRY32)
            if windll.kernel32.Module32First(snapshot, byref(entry)):
                while True:
                    try:
                        mod_name = entry.szModule.decode('utf-8', errors='ignore')
                        if mod_name.lower() == module_name.lower():
                            base = entry.modBaseAddr
                            windll.kernel32.CloseHandle(snapshot)
                            log(f'[+] Module {mod_name} - Base: {hex(base)}')
                            return base
                    except:
                        pass
                    if not windll.kernel32.Module32Next(snapshot, byref(entry)):
                        break
            windll.kernel32.CloseHandle(snapshot)
        except Exception as e:
            log(f'[!] Error: {e}')
        return 0

    def read(self, address, size):
        if not self.process_handle:
            return b'\x00' * size
        buffer    = (BYTE * size)()
        bytes_read = c_size_t(0)
        if windll.kernel32.ReadProcessMemory(self.process_handle, c_void_p(address), buffer, size, byref(bytes_read)):
            return bytes(buffer)
        return b'\x00' * size

    def write(self, address, data):
        if not self.process_handle:
            return False
        buffer        = (BYTE * len(data)).from_buffer_copy(data)
        bytes_written = c_size_t(0)
        return windll.kernel32.WriteProcessMemory(self.process_handle, c_void_p(address), buffer, len(data), byref(bytes_written))

    def read_int8(self, address):
        data = self.read(address, 8)
        return unpack("<Q", data)[0] if len(data) == 8 else 0

    def read_int4(self, address):
        data = self.read(address, 4)
        return unpack("<I", data)[0] if len(data) == 4 else 0

    def read_float(self, address):
        data = self.read(address, 4)
        return unpack("<f", data)[0] if len(data) == 4 else 0.0

    def close(self):
        if self.process_handle:
            windll.kernel32.CloseHandle(self.process_handle)

# ====================================
# GLOBALS
# ====================================
mem             = Memory()
lpAddr          = 0
plrsAddr        = 0
matrixAddr      = 0
features_enabled = False
offsets         = {}

def log(msg):
    if DEBUG_MODE:
        print(msg)

# ====================================
# VERSION CHECK
# ====================================
def get_roblox_version(pid):
    try:
        exe_path = Process(pid).exe()         
        folder   = os.path.basename(os.path.dirname(exe_path))  
        if folder.startswith("version-"):
            return folder
    except Exception as e:
        log(f'[!] Could not read Roblox exe path: {e}')
    return None

def check_version(pid):
    local_version = get_roblox_version(pid)
    if not local_version:
        print('[!] Version check skipped — could not determine Roblox version.')
        return True  
    try:
        resp           = get('https://offsets.ntgetwritewatch.workers.dev/version', timeout=10)
        remote_version = resp.text.strip()
    except Exception as e:
        print(f'[!] Version check skipped — network error: {e}')
        return True 

    print('----------------------------------------------')
    print(f'  Roblox version   : {local_version}')
    print(f'  Offsets version  : {remote_version}')
    if local_version == remote_version:
        print('  Status           : OK — versions match!')
    else:
        print('  Status           : MISMATCH — offsets may be outdated!')
        print('  The ESP might not work correctly until offsets are updated.')
    print('----------------------------------------------')

    return local_version == remote_version

# ====================================
# ROBLOX HELPER FUNCTIONS
# ====================================
def read_roblox_string(address):
    try:
        string_count = mem.read_int4(address + 0x10)
        if string_count > 15:
            ptr  = mem.read_int8(address)
            data = mem.read(ptr, min(string_count, 256))
        else:
            data = mem.read(address, min(string_count, 256))
        return data.split(b"\x00", 1)[0].decode("utf-8", errors="ignore")
    except:
        return ""

def get_class_name(instance):
    try:
        ptr = mem.read_int8(instance + 0x18)
        ptr = mem.read_int8(ptr + 0x8)
        fl  = mem.read_int8(ptr + 0x18)
        if fl == 0x1F:
            ptr = mem.read_int8(ptr)
        return read_roblox_string(ptr)
    except:
        return ""

def get_name(instance, name_offset):
    try:
        ptr = mem.read_int8(instance + name_offset)
        return read_roblox_string(ptr)
    except:
        return ""

def get_children(instance, children_offset):
    try:
        children_start = mem.read_int8(instance + children_offset)
        if not children_start:
            return []
        children_end = mem.read_int8(children_start + 8)
        current      = mem.read_int8(children_start)
        children     = []
        for _ in range(9000):
            if current == children_end:
                break
            children.append(mem.read_int8(current))
            current += 0x10
        return children
    except:
        return []

def find_first_child(instance, child_name, name_offset, children_offset):
    try:
        for child in get_children(instance, children_offset):
            if get_name(child, name_offset) == child_name:
                return child
    except:
        pass
    return 0

def find_first_child_of_class(instance, class_name, children_offset):
    try:
        for child in get_children(instance, children_offset):
            if get_class_name(child) == class_name:
                return child
    except:
        pass
    return 0

# ====================================
# MATH HELPERS
# ====================================
_IDENTITY_4X4 = array([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, 1],
], dtype=float32)

def world_to_screen(pos, view_proj_matrix, width, height):
    try:
        vec  = array([pos[0], pos[1], pos[2], 1.0], dtype=float32)
        clip = dot(view_proj_matrix, vec)
        if clip[3] <= 0:
            return None
        ndc = clip[:3] / clip[3]
        if not (-1 <= ndc[0] <= 1 and -1 <= ndc[1] <= 1 and 0 <= ndc[2] <= 1):
            return None
        x = int((ndc[0] + 1) * 0.5 * width)
        y = int((1 - ndc[1]) * 0.5 * height)
        return (x, y)
    except:
        return None

def find_window_by_title(title):
    return windll.user32.FindWindowW(None, title)

def get_client_rect_on_screen(hwnd):
    rect     = RECT()
    top_left = POINT(0, 0)
    bot_right = POINT(0, 0)
    if windll.user32.GetClientRect(hwnd, byref(rect)) == 0:
        return 0, 0, 0, 0
    top_left  = POINT(rect.left,  rect.top)
    bot_right = POINT(rect.right, rect.bottom)
    windll.user32.ClientToScreen(hwnd, byref(top_left))
    windll.user32.ClientToScreen(hwnd, byref(bot_right))
    return top_left.x, top_left.y, bot_right.x, bot_right.y

# ====================================
# INIT INJECTION
# ====================================
def init_injection():
    global lpAddr, plrsAddr, matrixAddr, offsets

    while True:
        log('[*] Waiting for Roblox...')

        while True:
            pid = mem.get_pid_by_name("RobloxPlayerBeta.exe")
            if pid and mem.open_process(pid):
                break
            sleep(1)

        try:
            check_version(pid)

            log('[*] Downloading offsets...')
            try:
                response = get('https://offsets.ntgetwritewatch.workers.dev/offsets.json', timeout=10)
                offsets  = response.json()
                log('[+] Offsets downloaded successfully!')
            except Exception as e:
                log(f'[!] Error downloading offsets: {e}')
                sleep(5)
                continue

            for key, val in offsets.items():
                try:
                    offsets[key] = int(val, 16)
                except ValueError:
                    pass

            baseAddr = mem.get_module_base()
            if not baseAddr:
                log('[!] Failed to get base address!')
                sleep(5)
                continue

            fakeDatamodel = mem.read_int8(baseAddr + offsets['FakeDataModelPointer'])
            if not fakeDatamodel:
                sleep(5)
                continue

            dataModel = mem.read_int8(fakeDatamodel + offsets['FakeDataModelToDataModel'])
            if not dataModel:
                sleep(5)
                continue

            wsAddr = mem.read_int8(dataModel + offsets['Workspace'])
            if not wsAddr:
                sleep(5)
                continue

            visualEngine = mem.read_int8(baseAddr + offsets['VisualEnginePointer'])
            if visualEngine:
                matrixAddr = visualEngine + offsets['viewmatrix']
                log(f'[+] ViewMatrix: {hex(matrixAddr)}')

            # Wait for Players service
            for _ in range(30):
                plrsAddr = find_first_child_of_class(dataModel, 'Players', offsets['Children'])
                if plrsAddr:
                    break
                sleep(1)

            if not plrsAddr:
                sleep(5)
                continue

            # Wait for LocalPlayer
            for _ in range(30):
                lpAddr = mem.read_int8(plrsAddr + offsets['LocalPlayer'])
                if lpAddr:
                    break
                sleep(1)

            if not lpAddr:
                sleep(5)
                continue

            log('[+] Injection completed successfully!')
            log(f'[!] ESP: {"ENABLED" if ENABLE_ESP else "DISABLED"}')
            log('[!] Press P to toggle | INSERT to quit')
            return True

        except Exception as e:
            log(f'[!] Injection error: {e}')
            log(traceback.format_exc())
            sleep(5)

# ====================================
# ESP OVERLAY
# ====================================
class ESPOverlay(QOpenGLWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.resize(10, 10)

        self.esp_data         = []
        self.prev_geometry    = (0, 0, 0, 0)
        self.last_geom_check  = 0.0
        self.startLineX       = 0
        self.startLineY       = 0
        self.matrix_cache     = None
        self.matrix_cache_time = 0.0

        hwnd     = self.winId().__int__()
        ex_style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style | WS_EX_LAYERED | WS_EX_TRANSPARENT)
        sleep(0.1)
        self.show()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_players)
        self.timer.start(8)  # ~125 FPS

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glLineWidth(ESP_BOX_THICKNESS)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, w, h, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)
        if not ENABLE_ESP or not features_enabled:
            return

        glLoadIdentity()

        for entry in self.esp_data:
            box        = entry.get('box')
            name       = entry.get('name', '')
            health     = entry.get('health', 100)
            distance   = entry.get('distance', 0)
            screen_pos = entry.get('screen_pos')

            if not box or not screen_pos:
                continue

            x, y, w, h = box

            # --- Box ---
            if ESP_SHOW_BOX:
                r, g, b, a = ESP_BOX_COLOR
                glColor4f(r/255, g/255, b/255, a/255)
                if ESP_CORNER_BOX:
                    cl = min(w, h) * 0.25
                    glBegin(GL_LINES)
                    # Topo-esquerda
                    glVertex2f(x, y + cl);        glVertex2f(x, y)
                    glVertex2f(x, y);              glVertex2f(x + cl, y)
                    # Topo-direita
                    glVertex2f(x + w - cl, y);    glVertex2f(x + w, y)
                    glVertex2f(x + w, y);          glVertex2f(x + w, y + cl)
                    # Base-direita
                    glVertex2f(x + w, y + h - cl); glVertex2f(x + w, y + h)
                    glVertex2f(x + w, y + h);      glVertex2f(x + w - cl, y + h)
                    # Base-esquerda
                    glVertex2f(x + cl, y + h);    glVertex2f(x, y + h)
                    glVertex2f(x, y + h);          glVertex2f(x, y + h - cl)
                    glEnd()
                else:
                    glBegin(GL_LINE_LOOP)
                    glVertex2f(x, y);         glVertex2f(x + w, y)
                    glVertex2f(x + w, y + h); glVertex2f(x, y + h)
                    glEnd()

            # --- Tracer ---
            if ESP_SHOW_TRACER:
                r, g, b, a = ESP_TRACER_COLOR
                glColor4f(r/255, g/255, b/255, a/255)
                glBegin(GL_LINES)
                glVertex2f(self.startLineX, self.startLineY)
                glVertex2f(screen_pos[0], screen_pos[1])
                glEnd()

            # --- Barra de vida ---
            if ESP_SHOW_HEALTH:
                bar_w = 2
                bar_x = x - bar_w - 2
                bar_y = y

                # Fundo
                glColor4f(0.1, 0.1, 0.1, 0.8)
                glBegin(GL_QUADS)
                glVertex2f(bar_x, bar_y);         glVertex2f(bar_x + bar_w, bar_y)
                glVertex2f(bar_x + bar_w, bar_y + h); glVertex2f(bar_x, bar_y + h)
                glEnd()

                # Preenchimento
                filled = (health / 100.0) * h
                if ESP_DYNAMIC_HEALTH_COLOR:
                    green = health / 100.0
                    glColor4f(1.0 - green, green, 0.0, 1.0)
                else:
                    r, g, b, a = ESP_HEALTH_COLOR
                    glColor4f(r/255, g/255, b/255, a/255)

                glBegin(GL_QUADS)
                glVertex2f(bar_x, bar_y + h - filled);         glVertex2f(bar_x + bar_w, bar_y + h - filled)
                glVertex2f(bar_x + bar_w, bar_y + h);          glVertex2f(bar_x, bar_y + h)
                glEnd()

            # --- Nome ---
            if ESP_SHOW_NAME and name:
                self._render_text(x + w / 2, y - 5, name, ESP_NAME_COLOR)

            # --- Distância ---
            if ESP_SHOW_DISTANCE:
                self._render_text(x + w / 2, y + h + 15, f"{distance}m", ESP_DISTANCE_COLOR)

    def _render_text(self, x, y, text, color):
        painter = QPainter(self)
        painter.setPen(QPen(QColor(color[0], color[1], color[2], color[3])))
        painter.setFont(QFont("Arial", ESP_TEXT_SIZE))
        painter.drawText(int(x), int(y), text)
        painter.end()

    def update_players(self):
        if not ENABLE_ESP or not features_enabled or lpAddr == 0 or plrsAddr == 0 or matrixAddr == 0:
            return

        self.esp_data.clear()
        now = time()

        # Atualizar geometria a cada 5 s
        if now - self.last_geom_check > 5.0:
            hwnd_roblox = find_window_by_title("Roblox")
            if hwnd_roblox:
                x, y, r, b = get_client_rect_on_screen(hwnd_roblox)
                new_geom = (x, y, r - x, b - y)
                if new_geom != self.prev_geometry and new_geom[2] > 0 and new_geom[3] > 0:
                    self.setGeometry(*new_geom)
                    self.prev_geometry = new_geom
                    self.startLineX    = self.width()  / 2
                    self.startLineY    = self.height() - self.height() / 20
            self.last_geom_check = now

        try:
            # Cache da view matrix (~60 Hz)
            if now - self.matrix_cache_time > 0.016:
                raw = mem.read(matrixAddr, 64)
                self.matrix_cache      = array(unpack("<16f", raw), dtype=float32).reshape(4, 4)
                self.matrix_cache_time = now

            view_proj = self.matrix_cache if self.matrix_cache is not None else _IDENTITY_4X4.copy()

            lpTeam = mem.read_int8(lpAddr + offsets['Team'])
            lpChar = mem.read_int8(lpAddr + offsets['ModelInstance'])
            lpHead = find_first_child(lpChar, 'Head', offsets['Name'], offsets['Children']) if lpChar else 0

            if lpHead:
                lpPrim     = mem.read_int8(lpHead + offsets['Primitive'])
                lpHeadPos  = array(unpack("<fff", mem.read(lpPrim + offsets['Position'], 12)), dtype=float32) if lpPrim else array([0, 0, 0], dtype=float32)
            else:
                lpHeadPos  = array([0, 0, 0], dtype=float32)

            for child in get_children(plrsAddr, offsets['Children']):
                try:
                    if child == lpAddr:
                        continue

                    if IGNORE_TEAM:
                        team = mem.read_int8(child + offsets['Team'])
                        if team == lpTeam and team > 0:
                            continue

                    char = mem.read_int8(child + offsets['ModelInstance'])
                    if not char:
                        continue

                    hum = find_first_child_of_class(char, 'Humanoid', offsets['Children'])
                    if not hum:
                        continue

                    health = mem.read_float(hum + offsets['Health'])
                    if IGNORE_DEAD and health <= 0:
                        continue
                    health = max(0.0, min(100.0, health))

                    head = find_first_child(char, 'Head', offsets['Name'], offsets['Children'])
                    if not head:
                        continue

                    head_prim = mem.read_int8(head + offsets['Primitive'])
                    if not head_prim:
                        continue

                    head_pos = array(unpack("<fff", mem.read(head_prim + offsets['Position'], 12)), dtype=float32)
                    distance = int(sqrt(sum((head_pos - lpHeadPos) ** 2)))

                    if HIDE_DISTANCE and distance > MAX_DISTANCE:
                        continue

                    screen_head = world_to_screen(head_pos, view_proj, self.width(), self.height())
                    if not screen_head:
                        continue

                    # Bounding box usando Head + HumanoidRootPart
                    parts = [screen_head]
                    hrp = find_first_child(char, 'HumanoidRootPart', offsets['Name'], offsets['Children'])
                    if hrp:
                        hrp_prim = mem.read_int8(hrp + offsets['Primitive'])
                        if hrp_prim:
                            hrp_pos = array(unpack("<fff", mem.read(hrp_prim + offsets['Position'], 12)), dtype=float32)
                            hrp_screen = world_to_screen(hrp_pos, view_proj, self.width(), self.height())
                            if hrp_screen:
                                parts.append(hrp_screen)

                    if len(parts) < 2:
                        continue

                    pad   = 5
                    min_x = min(p[0] for p in parts) - pad
                    min_y = min(p[1] for p in parts) - pad
                    max_x = max(p[0] for p in parts) + pad
                    max_y = max(p[1] for p in parts) + pad

                    self.esp_data.append({
                        'box':        [int(min_x), int(min_y), int(max_x - min_x), int(max_y - min_y)],
                        'name':       get_name(child, offsets['Name']),
                        'health':     health,
                        'distance':   distance,
                        'screen_pos': screen_head,
                    })
                except:
                    continue
        except:
            pass

        self.update()

# ====================================
# HOTKEY HANDLER
# ====================================
def hotkey_listener():
    global features_enabled
    P_KEY      = 0x50
    INSERT_KEY = 0x2D
    last_p     = False
    last_ins   = False
    check_cnt  = 0

    while mem.process_id == 0:
        sleep(0.1)

    roblox_pid = mem.process_id
    log(f'[+] Hotkey listener started (PID: {roblox_pid})')
    log('[*] P = toggle | INSERT = quit')

    while True:
        try:
            check_cnt += 1
            if check_cnt >= 20:  # a cada ~1 s
                check_cnt = 0
                try:
                    proc = Process(roblox_pid)
                    if not proc.is_running():
                        raise NoSuchProcess(roblox_pid)
                except (NoSuchProcess, Exception):
                    log('[!] Roblox was closed - exiting...')
                    sleep(1)
                    sys.exit(0)

            cur_p   = windll.user32.GetAsyncKeyState(P_KEY)      & 0x8000 != 0
            cur_ins = windll.user32.GetAsyncKeyState(INSERT_KEY) & 0x8000 != 0

            if cur_p and not last_p:
                features_enabled = not features_enabled
                log(f'[*] Features {"ENABLED" if features_enabled else "DISABLED"}')

            if cur_ins and not last_ins:
                log('[*] INSERT pressed - closing...')
                sys.exit(0)

            last_p   = cur_p
            last_ins = cur_ins
        except SystemExit:
            raise
        except:
            pass

        sleep(0.05)

# ====================================
# MAIN
# ====================================
if __name__ == "__main__":
    try:
        Process(os.getpid()).nice(HIGH_PRIORITY_CLASS)
    except:
        pass

    log('================')
    log('     OMEGA')
    log('================')
    log(f'ESP: {"✓" if ENABLE_ESP else "✗"}')
    log('================')

    init_injection()

    Thread(target=hotkey_listener, daemon=True).start()

    fmt = QSurfaceFormat()
    fmt.setSamples(8)
    QSurfaceFormat.setDefaultFormat(fmt)

    app = QApplication([])

    esp_overlay = None
    if ENABLE_ESP:
        esp_overlay = ESPOverlay()
        log('[+] ESP')

    log('[*] Press P to toggle | INSERT to quit')

    sys.exit(app.exec_())