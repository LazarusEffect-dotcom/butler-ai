# ============================================================
# JARVIS SYSTEM CONTROLLER
# Hardware Diagnostics, Audio/Volume Control, Windows Automation
# ============================================================

import ctypes
import datetime
import os
import socket
import subprocess
import time

import psutil
import pyautogui

try:
    from pycaw.pycaw import AudioUtilities
    HAS_PYCAW = True
except ImportError:
    HAS_PYCAW = False

try:
    import pyperclip
    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


# ============================================================
# HARDWARE & SYSTEM STATUS
# ============================================================

def get_system_status():
    """
    Gather comprehensive hardware and OS diagnostics.
    """
    # CPU
    cpu_usage = psutil.cpu_percent(interval=0.2)
    cpu_count = psutil.cpu_count(logical=True)
    cpu_freq = psutil.cpu_freq()
    freq_mhz = round(cpu_freq.current) if cpu_freq else "N/A"

    # Memory
    mem = psutil.virtual_memory()
    ram_total_gb = round(mem.total / (1024 ** 3), 1)
    ram_used_gb = round(mem.used / (1024 ** 3), 1)
    ram_percent = mem.percent

    # Battery
    battery = psutil.sensors_battery()
    if battery is not None:
        battery_pct = round(battery.percent)
        battery_plugged = battery.power_plugged
        battery_status = f"{battery_pct}% {'(Charging)' if battery_plugged else '(On Battery)'}"
    else:
        battery_status = "Desktop (AC Power Connected)"

    # Disks
    disks = []
    for partition in psutil.disk_partitions(all=False):
        if "fixed" in partition.opts or partition.fstype:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    "drive": partition.device,
                    "total_gb": round(usage.total / (1024 ** 3), 1),
                    "free_gb": round(usage.free / (1024 ** 3), 1),
                    "percent": usage.percent,
                })
            except (PermissionError, OSError):
                continue

    # Network / IP
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
    except Exception:
        hostname = "Unknown"
        local_ip = "127.0.0.1"

    # Internet connectivity check (fast socket probe)
    internet_connected = False
    try:
        socket.setdefaulttimeout(1.5)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        internet_connected = True
    except Exception:
        internet_connected = False

    # Uptime
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.datetime.now() - boot_time
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)
    uptime_str = f"{hours}h {minutes}m"

    return {
        "cpu_usage": cpu_usage,
        "cpu_count": cpu_count,
        "cpu_freq_mhz": freq_mhz,
        "ram_percent": ram_percent,
        "ram_used_gb": ram_used_gb,
        "ram_total_gb": ram_total_gb,
        "battery_status": battery_status,
        "disks": disks,
        "hostname": hostname,
        "local_ip": local_ip,
        "internet_connected": internet_connected,
        "uptime": uptime_str,
    }


def get_top_processes(limit=5):
    """
    Retrieve top running processes sorted by memory consumption.
    """
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
        try:
            mem_mb = round(p.info['memory_info'].rss / (1024 * 1024), 1)
            procs.append({
                "pid": p.info['pid'],
                "name": p.info['name'],
                "memory_mb": mem_mb,
                "cpu_percent": p.info['cpu_percent'] or 0.0,
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    procs.sort(key=lambda x: x["memory_mb"], reverse=True)
    return procs[:limit]


# ============================================================
# VOLUME & AUDIO CONTROL
# ============================================================

def _get_speaker_device():
    if not HAS_PYCAW:
        return None
    try:
        return AudioUtilities.GetSpeakers()
    except Exception:
        return None


def get_volume():
    """
    Get master audio volume (0-100).
    """
    dev = _get_speaker_device()
    if dev:
        try:
            return round(dev.volume_percent)
        except Exception:
            pass
    return 100


def set_volume(level_percent: int):
    """
    Set master volume percentage (0 - 100).
    """
    level_percent = max(0, min(100, int(level_percent)))
    dev = _get_speaker_device()
    if dev:
        try:
            dev.EndpointVolume.SetMasterVolumeLevelScalar(level_percent / 100.0, None)
            return True, f"Volume set to {level_percent}%"
        except Exception as e:
            return False, f"Could not adjust volume: {e}"
    return False, "Audio control is not available."


def volume_up(step=10):
    current = get_volume()
    new_vol = min(100, current + step)
    return set_volume(new_vol)


def volume_down(step=10):
    current = get_volume()
    new_vol = max(0, current - step)
    return set_volume(new_vol)


def is_muted():
    dev = _get_speaker_device()
    if dev:
        try:
            return bool(dev.EndpointVolume.GetMute())
        except Exception:
            pass
    return False


def set_mute(mute_state: bool):
    dev = _get_speaker_device()
    if dev:
        try:
            dev.EndpointVolume.SetMute(1 if mute_state else 0, None)
            state_str = "muted" if mute_state else "unmuted"
            return True, f"Audio is now {state_str}."
        except Exception as e:
            return False, f"Could not change mute state: {e}"
    return False, "Audio control is not available."


def toggle_mute():
    currently_muted = is_muted()
    return set_mute(not currently_muted)


# ============================================================
# MEDIA KEY CONTROLS
# ============================================================

def media_play_pause():
    try:
        pyautogui.press("playpause")
        return True, "Triggered Play/Pause."
    except Exception as e:
        return False, str(e)


def media_next():
    try:
        pyautogui.press("nexttrack")
        return True, "Skipped to next track."
    except Exception as e:
        return False, str(e)


def media_prev():
    try:
        pyautogui.press("prevtrack")
        return True, "Returned to previous track."
    except Exception as e:
        return False, str(e)


def media_stop():
    try:
        pyautogui.press("stop")
        return True, "Stopped media playback."
    except Exception as e:
        return False, str(e)


# ============================================================
# WINDOWS OS CONTROLS
# ============================================================

def lock_pc():
    """
    Instantly and securely locks Windows workstation.
    """
    try:
        ctypes.windll.user32.LockWorkStation()
        return True, "Workstation locked successfully."
    except Exception as e:
        return False, f"Failed to lock workstation: {e}"


def sleep_pc():
    try:
        subprocess.Popen("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
        return True, "System entering sleep mode."
    except Exception as e:
        return False, f"Failed to put system to sleep: {e}"


def shutdown_pc(confirmed=False):
    if not confirmed:
        return False, "Shutdown requires confirmation. Please repeat with confirmation or type 'shutdown confirm'."
    try:
        subprocess.Popen("shutdown /s /t 30 /c \"Jarvis: System shutdown initiated in 30 seconds. Type 'shutdown abort' to cancel.\"", shell=True)
        return True, "System shutdown initiated (30 second timer)."
    except Exception as e:
        return False, f"Failed to initiate shutdown: {e}"


def restart_pc(confirmed=False):
    if not confirmed:
        return False, "Restart requires confirmation. Please repeat with confirmation or type 'restart confirm'."
    try:
        subprocess.Popen("shutdown /r /t 30 /c \"Jarvis: System restart initiated in 30 seconds. Type 'shutdown abort' to cancel.\"", shell=True)
        return True, "System restart initiated (30 second timer)."
    except Exception as e:
        return False, f"Failed to initiate restart: {e}"


def cancel_shutdown():
    try:
        subprocess.Popen("shutdown /a", shell=True)
        return True, "Shutdown/restart sequence aborted."
    except Exception as e:
        return False, f"Failed to cancel shutdown: {e}"


def show_desktop():
    try:
        pyautogui.hotkey("win", "d")
        return True, "Toggled Show Desktop."
    except Exception as e:
        return False, str(e)


def open_task_manager():
    try:
        subprocess.Popen("taskmgr.exe")
        return True, "Task Manager opened."
    except Exception as e:
        return False, str(e)


def open_settings():
    try:
        subprocess.Popen("explorer.exe ms-settings:")
        return True, "Windows Settings opened."
    except Exception as e:
        return False, str(e)


# ============================================================
# CLIPBOARD
# ============================================================

def get_clipboard_text():
    if HAS_CLIPBOARD:
        try:
            return pyperclip.paste()
        except Exception:
            pass
    return ""


def set_clipboard_text(text: str):
    if HAS_CLIPBOARD:
        try:
            pyperclip.copy(text)
            return True, "Text copied to clipboard."
        except Exception as e:
            return False, str(e)
    return False, "Clipboard module unavailable."


# ============================================================
# SCREENSHOT & WEBCAM
# ============================================================

def take_screenshot():
    """
    Take a screenshot of the primary screen and save it to screenshots folder.
    """
    try:
        folder = os.path.join(os.getcwd(), "screenshots")
        os.makedirs(folder, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(folder, filename)

        img = pyautogui.screenshot()
        img.save(filepath)

        # Open image for user viewing
        try:
            os.startfile(filepath)
        except Exception:
            pass

        return True, f"Screenshot captured and saved to {filepath}"
    except Exception as e:
        return False, f"Could not capture screenshot: {e}"


def capture_photo():
    """
    Capture a photo from the primary webcam if available.
    """
    if not HAS_CV2:
        return False, "OpenCV is not installed."

    try:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap.release()
            return False, "No webcam hardware detected on this device, sir."

        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            return False, "Could not capture image from webcam."

        folder = os.path.join(os.getcwd(), "photos")
        os.makedirs(folder, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(folder, f"photo_{timestamp}.jpg")

        cv2.imwrite(filepath, frame)
        try:
            os.startfile(filepath)
        except Exception:
            pass

        return True, f"Photo captured and saved to {filepath}"
    except Exception as e:
        return False, f"Camera error: {e}"
