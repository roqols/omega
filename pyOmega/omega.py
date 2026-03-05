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
import random
from ctypes import *
from ctypes.wintypes import DWORD, LONG, BYTE, HMODULE
from struct import unpack, pack
from numpy import array, float32, dot
from math import sqrt
from time import time, sleep
from threading import Thread
from requests import get
from psutil import Process, HIGH_PRIORITY_CLASS, process_iter, NoSuchProcess
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QRect, QPoint
from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QBrush, QFontMetrics

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
# [STEALTH] Privilégio mínimo: apenas leitura de memória
PROCESS_VM_READ     = 0x0010
PROCESS_QUERY_INFO  = 0x0400
TH32CS_SNAPPROCESS  = 0x00000002
TH32CS_SNAPMODULE   = 0x00000008 | 0x00000010
GWL_EXSTYLE         = -20
WS_EX_LAYERED       = 0x80000
WS_EX_TRANSPARENT   = 0x20
HWND_TOPMOST        = -1
SWP_NOMOVE          = 0x0002
SWP_NOSIZE          = 0x0001

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

    def _is_valid_ptr(self, address):
        """[STEALTH] Verifica se o ponteiro é plausível antes de tentar lê-lo."""
        return isinstance(address, int) and 0x10000 < address < 0x7FFFFFFFFFFF

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
            # [STEALTH] Usa privilégios mínimos — VM_READ + QUERY_INFO apenas
            self.process_handle = windll.kernel32.OpenProcess(
                PROCESS_VM_READ | PROCESS_QUERY_INFO, False, pid
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
        # [STEALTH] Valida ponteiro antes de tentar leitura
        if not self.process_handle or not self._is_valid_ptr(address):
            return b'\x00' * size
        try:
            buffer    = (BYTE * size)()
            bytes_read = c_size_t(0)
            if windll.kernel32.ReadProcessMemory(self.process_handle, c_void_p(address), buffer, size, byref(bytes_read)):
                return bytes(buffer)
        except Exception:
            pass
        return b'\x00' * size

    def write(self, address, data):
        if not self.process_handle or not self._is_valid_ptr(address):
            return False
        buffer        = (BYTE * len(data)).from_buffer_copy(data)
        bytes_written = c_size_t(0)
        return windll.kernel32.WriteProcessMemory(self.process_handle, c_void_p(address), buffer, len(data), byref(bytes_written))

    def read_int8(self, address):
        if not self._is_valid_ptr(address):
            return 0
        data = self.read(address, 8)
        return unpack("<Q", data)[0] if len(data) == 8 else 0

    def read_int4(self, address):
        if not self._is_valid_ptr(address):
            return 0
        data = self.read(address, 4)
        return unpack("<I", data)[0] if len(data) == 4 else 0

    def read_float(self, address):
        if not self._is_valid_ptr(address):
            return 0.0
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
offsets_ready   = False  # [PERF] Lazy loading flag

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
    """[BUGFIX] Limita leitura para evitar MemoryError em strings corrompidas."""
    try:
        raw_count = mem.read_int4(address + 0x10)
        # Clamp para prevenir leituras absurdamente grandes
        string_count = min(max(0, raw_count), 128)
        if string_count == 0:
            return ""
        if raw_count > 15:
            ptr  = mem.read_int8(address)
            if not mem._is_valid_ptr(ptr):
                return ""
            data = mem.read(ptr, string_count)
        else:
            data = mem.read(address, string_count)
        return data.split(b"\x00", 1)[0].decode("utf-8", errors="ignore")
    except Exception:
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

def get_window_rect(hwnd):
    rect = RECT()
    windll.user32.GetWindowRect(hwnd, byref(rect))
    return rect.left, rect.top, rect.right, rect.bottom

# ====================================
# ASYNC OFFSET LOADER
# ====================================
def _load_offsets_async(pid, callback):
    """[PERF] Baixa offsets em background sem travar a inicialização."""
    try:
        check_version(pid)
        log('[*] Downloading offsets (async)...')
        response = get('https://offsets.ntgetwritewatch.workers.dev/offsets.json', timeout=10)
        raw = response.json()
        parsed = {}
        for key, val in raw.items():
            try:
                parsed[key] = int(val, 16)
            except (ValueError, TypeError):
                parsed[key] = val
        log('[+] Offsets downloaded successfully!')
        callback(parsed)
    except Exception as e:
        log(f'[!] Error downloading offsets: {e}')
        callback(None)

# ====================================
# INIT INJECTION
# ====================================
def init_injection():
    global lpAddr, plrsAddr, matrixAddr, offsets, offsets_ready

    while True:
        log('[*] Waiting for Roblox...')

        while True:
            pid = mem.get_pid_by_name("RobloxPlayerBeta.exe")
            if pid and mem.open_process(pid):
                break
            sleep(1)

        # [PERF] Carrega offsets de forma assíncrona
        offsets_ready = False
        def _on_offsets(result):
            global offsets, offsets_ready
            if result:
                offsets = result
                offsets_ready = True
            else:
                offsets_ready = False

        Thread(target=_load_offsets_async, args=(pid, _on_offsets), daemon=True).start()

        # Aguarda offsets ficarem prontos (timeout 15s)
        for _ in range(150):
            if offsets_ready:
                break
            sleep(0.1)

        if not offsets_ready:
            log('[!] Offsets not loaded, retrying...')
            sleep(5)
            continue

        try:
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

            for _ in range(30):
                plrsAddr = find_first_child_of_class(dataModel, 'Players', offsets['Children'])
                if plrsAddr:
                    break
                sleep(1)

            if not plrsAddr:
                sleep(5)
                continue

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
class ESPOverlay(QWidget):
    """
    Overlay 100% QPainter — sem OpenGL.

    QOpenGLWidget com WA_TranslucentBackground quebra em fullscreen borderless
    no Windows porque o FBO interno do Qt perde o canal alpha quando o DWM
    (Desktop Window Manager) é contornado pelo jogo. QPainter usa o pipeline
    do compositor nativo e funciona corretamente em qualquer modo de tela.
    """

    def __init__(self):
        super().__init__()
        # Flags essenciais para overlay transparente
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.resize(10, 10)

        self.esp_data          = []
        self.prev_geometry     = (0, 0, 0, 0)
        self.last_geom_check   = 0.0
        self.startLineX        = 0
        self.startLineY        = 0
        self.matrix_cache      = None
        self.matrix_cache_time = 0.0

        # [PERF] Cache de entidades: {player_addr: {char, hum, head, hrp, expires}}
        self._entity_cache     = {}
        self._entity_cache_ttl = 2.0

        # Font pré-criada — evita realocar a cada frame
        self._font = QFont("Arial", ESP_TEXT_SIZE)
        self._font.setBold(False)

        self._apply_window_style()
        sleep(0.1)
        self.show()

        # [STEALTH] Timer com jitter aleatório
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(8)

    def _apply_window_style(self):
        """
        Não manipula GWL_EXSTYLE manualmente.
        WA_TranslucentBackground faz o Qt controlar WS_EX_LAYERED internamente
        via UpdateLayeredWindow. Qualquer SetWindowLongW externo quebra esse
        estado e gera 'UpdateLayeredWindowIndirect failed'.
        Transparência e passthrough de mouse são garantidos pelas flags Qt:
          - WindowTransparentForInput  →  WS_EX_TRANSPARENT (Qt gerencia)
          - WindowStaysOnTopHint       →  HWND_TOPMOST      (Qt gerencia)
        """
        pass

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_window_style()

    def changeEvent(self, event):
        super().changeEvent(event)
        self._apply_window_style()

    def paintEvent(self, event):
        """Renderiza todo o ESP com QPainter — funciona em qualquer modo de tela."""
        painter = QPainter(self)
        # Limpa com transparência total
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.fillRect(self.rect(), Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        if not ENABLE_ESP or not features_enabled:
            painter.end()
            return

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(self._font)

        pen = QPen()
        pen.setWidth(ESP_BOX_THICKNESS)

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
                pen.setColor(QColor(r, g, b, a))
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                if ESP_CORNER_BOX:
                    cl = int(min(w, h) * 0.25)
                    corners = [
                        # topo-esquerda
                        (x, y+cl, x, y), (x, y, x+cl, y),
                        # topo-direita
                        (x+w-cl, y, x+w, y), (x+w, y, x+w, y+cl),
                        # base-direita
                        (x+w, y+h-cl, x+w, y+h), (x+w, y+h, x+w-cl, y+h),
                        # base-esquerda
                        (x+cl, y+h, x, y+h), (x, y+h, x, y+h-cl),
                    ]
                    for x1, y1, x2, y2 in corners:
                        painter.drawLine(x1, y1, x2, y2)
                else:
                    painter.drawRect(x, y, w, h)

            # --- Tracer ---
            if ESP_SHOW_TRACER:
                r, g, b, a = ESP_TRACER_COLOR
                pen.setWidth(1)
                pen.setColor(QColor(r, g, b, a))
                painter.setPen(pen)
                painter.drawLine(
                    int(self.startLineX), int(self.startLineY),
                    int(screen_pos[0]),   int(screen_pos[1])
                )
                pen.setWidth(ESP_BOX_THICKNESS)

            # --- Health bar ---
            if ESP_SHOW_HEALTH:
                bar_w  = 4
                bar_x  = x - bar_w - 2
                bar_y  = y
                filled = int((health / 100.0) * h)

                # Fundo
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(20, 20, 20, 200)))
                painter.drawRect(bar_x, bar_y, bar_w, h)

                # Preenchimento
                if ESP_DYNAMIC_HEALTH_COLOR:
                    green = int(health * 2.55)
                    red   = 255 - green
                    fill_color = QColor(red, green, 0, 255)
                else:
                    r, g, b, a = ESP_HEALTH_COLOR
                    fill_color = QColor(r, g, b, a)
                painter.setBrush(QBrush(fill_color))
                painter.drawRect(bar_x, bar_y + h - filled, bar_w, filled)

                painter.setBrush(Qt.NoBrush)

            # --- Nome ---
            if ESP_SHOW_NAME and name:
                r, g, b, a = ESP_NAME_COLOR
                pen.setWidth(1)
                pen.setColor(QColor(r, g, b, a))
                painter.setPen(pen)
                painter.drawText(int(x + w / 2), int(y - 5), name)

            # --- Distância ---
            if ESP_SHOW_DISTANCE:
                r, g, b, a = ESP_DISTANCE_COLOR
                pen.setColor(QColor(r, g, b, a))
                painter.setPen(pen)
                painter.drawText(int(x + w / 2), int(y + h + 15), f"{distance}m")

        painter.end()

    def _tick(self):
        """[STEALTH] Timer com jitter aleatório."""
        self.update_players()
        jitter = random.randint(-2, 2)
        self.timer.setInterval(max(4, 8 + jitter))

    def _update_geometry(self):
        """Detecta fullscreen/windowed e atualiza o overlay sem piscar."""
        hwnd_roblox = find_window_by_title("Roblox")
        if not hwnd_roblox:
            return

        x, y, r, b = get_client_rect_on_screen(hwnd_roblox)
        w, h = r - x, b - y

        if w <= 0 or h <= 0:
            x, y, r, b = get_window_rect(hwnd_roblox)
            w, h = r - x, b - y

        if w <= 0 or h <= 0:
            return

        new_geom = (x, y, w, h)
        if new_geom != self.prev_geometry:
            self.setGeometry(*new_geom)
            self.prev_geometry = new_geom
            self.startLineX    = w / 2
            self.startLineY    = h - h / 20
            self._apply_window_style()

    def _get_cached_entity(self, player_addr, now):
        """[PERF] Retorna dados cacheados do player ou None se expirado."""
        cached = self._entity_cache.get(player_addr)
        if cached and now < cached['expires']:
            return cached
        return None

    def _set_cached_entity(self, player_addr, data, now):
        """[PERF] Salva dados do player no cache com TTL de 2s."""
        data['expires'] = now + self._entity_cache_ttl
        self._entity_cache[player_addr] = data

    def update_players(self):
        if not ENABLE_ESP or not features_enabled or lpAddr == 0 or plrsAddr == 0 or matrixAddr == 0:
            return

        self.esp_data.clear()
        now = time()

        # Atualiza geometria a cada 2s (mais frequente que antes para pegar resize rápido)
        if now - self.last_geom_check > 2.0:
            self._update_geometry()
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
                lpPrim    = mem.read_int8(lpHead + offsets['Primitive'])
                lpHeadPos = array(unpack("<fff", mem.read(lpPrim + offsets['Position'], 12)), dtype=float32) if lpPrim else array([0,0,0], dtype=float32)
            else:
                lpHeadPos = array([0, 0, 0], dtype=float32)

            # [PERF] Limpa entradas de cache expiradas periodicamente
            if now % 10 < 0.1:
                self._entity_cache = {k: v for k, v in self._entity_cache.items() if now < v['expires']}

            for child in get_children(plrsAddr, offsets['Children']):
                try:
                    if child == lpAddr:
                        continue

                    if IGNORE_TEAM:
                        team = mem.read_int8(child + offsets['Team'])
                        if team == lpTeam and team > 0:
                            continue

                    # [PERF] Usa cache de entidade (char, hum, head, hrp)
                    cached = self._get_cached_entity(child, now)
                    if cached:
                        char = cached['char']
                        hum  = cached['hum']
                        head = cached['head']
                        hrp  = cached['hrp']
                    else:
                        char = mem.read_int8(child + offsets['ModelInstance'])
                        if not char:
                            continue
                        hum  = find_first_child_of_class(char, 'Humanoid', offsets['Children'])
                        head = find_first_child(char, 'Head', offsets['Name'], offsets['Children'])
                        hrp  = find_first_child(char, 'HumanoidRootPart', offsets['Name'], offsets['Children'])
                        self._set_cached_entity(child, {
                            'char': char, 'hum': hum, 'head': head, 'hrp': hrp
                        }, now)

                    if not char or not hum:
                        continue

                    health = mem.read_float(hum + offsets['Health'])
                    if IGNORE_DEAD and health <= 0:
                        continue
                    health = max(0.0, min(100.0, health))

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

                    parts = [screen_head]
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
            if check_cnt >= 20:
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

    app = QApplication([])

    esp_overlay = None
    if ENABLE_ESP:
        esp_overlay = ESPOverlay()
        log('[+] ESP')

    log('[*] Press P to toggle | INSERT to quit')

    sys.exit(app.exec_())
