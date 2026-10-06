# ============================================================
# JARVIS AI INTERPRETER
# Hybrid Architecture:
# 1. Zero-latency Fast Matcher (<10ms for instant system commands)
# 2. Ollama Llama 3.2 Tool Calling
# 3. Conversational Butler Persona Fallback
# ============================================================

import json
import re
import urllib.parse

try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False

from config import (
    APPLICATION_ALIASES,
    BUTLER_NAME,
    OLLAMA_FAST_MODEL,
    OLLAMA_MODEL,
    USER_TITLE,
)


# ============================================================
# TIER 1: ZERO-LATENCY FAST-PATH PATTERN MATCHER
# ============================================================

def fast_match_command(command: str):
    """
    Instantly match common operational commands without LLM latency.
    Returns dict if matched, or None to fall back to LLM.
    """
    cmd = command.strip().lower()

    # Exit / Shutdown
    if cmd in ["exit", "quit", "shutdown", "bye", "goodbye", "close"]:
        return {"action": "exit"}

    # Voice toggle
    if cmd in ["voice off", "mute voice", "mute speech", "silence voice", "disable voice"]:
        return {"action": "set_voice", "enabled": False}
    if cmd in ["voice on", "unmute voice", "enable voice", "start voice"]:
        return {"action": "set_voice", "enabled": True}
    if cmd in ["toggle voice"]:
        return {"action": "toggle_voice"}

    # Daily Briefing
    if any(cmd == x for x in ["briefing", "daily briefing", "morning briefing", "status report", "sitrep", "good morning"]):
        return {"action": "daily_briefing"}

    # Hardware & System status
    if any(k in cmd for k in ["system status", "hardware status", "system stats", "diagnostics", "system health", "specs", "cpu usage", "ram usage", "battery level", "battery status", "system diagnostic"]):
        return {"action": "system_status"}

    if any(k in cmd for k in ["top processes", "active tasks", "running processes", "running tasks", "task list", "what is running"]):
        return {"action": "top_processes"}

    # Audio & Volume Controls
    if cmd in ["mute", "mute audio", "silence audio", "mute sound"]:
        return {"action": "mute"}
    if cmd in ["unmute", "unmute audio", "sound on"]:
        return {"action": "unmute"}
    if cmd in ["volume up", "increase volume", "louder"]:
        return {"action": "volume_up", "step": 10}
    if cmd in ["volume down", "decrease volume", "quieter", "lower volume"]:
        return {"action": "volume_down", "step": 10}
    if cmd in ["get volume", "current volume", "what is the volume", "volume level"]:
        return {"action": "get_volume"}

    # "set volume to 60%", "volume 40", "volume to 75"
    vol_match = re.search(r"(?:set\s+)?volume\s+(?:to\s+)?(\d+)(?:%)?", cmd)
    if vol_match:
        try:
            level = int(vol_match.group(1))
            return {"action": "set_volume", "level": level}
        except ValueError:
            pass

    # Media controls
    if any(cmd == x for x in ["play", "pause", "play pause", "pause music", "resume music", "play music"]):
        return {"action": "media_play_pause"}
    if any(cmd == x for x in ["next track", "next song", "skip track", "skip song"]):
        return {"action": "media_next"}
    if any(cmd == x for x in ["previous track", "previous song", "prev track", "prev song"]):
        return {"action": "media_prev"}
    if cmd in ["stop music", "stop media"]:
        return {"action": "media_stop"}

    # OS Controls
    if any(k in cmd for k in ["lock pc", "lock computer", "lock screen", "lock workstation"]):
        return {"action": "lock_pc"}
    if any(k in cmd for k in ["show desktop", "minimize all", "minimize windows"]):
        return {"action": "show_desktop"}
    if any(k in cmd for k in ["task manager", "open task manager", "launch task manager"]):
        return {"action": "open_task_manager"}
    if any(k in cmd for k in ["open settings", "windows settings"]):
        return {"action": "open_settings"}
    if any(k in cmd for k in ["take screenshot", "capture screen", "screenshot"]):
        return {"action": "take_screenshot"}
    if any(k in cmd for k in ["take photo", "take selfie", "capture photo", "webcam photo"]):
        return {"action": "capture_photo"}

    # Clipboard
    if cmd in ["get clipboard", "read clipboard", "show clipboard", "paste clipboard"]:
        return {"action": "get_clipboard"}

    # Weather
    if cmd in ["weather", "what's the weather", "what is the weather", "current weather", "weather report", "how is the weather"]:
        return {"action": "weather", "city": "auto"}
    weather_city = re.search(r"weather\s+(?:in|for|at)\s+([a-zA-Z\s]+)", cmd)
    if weather_city:
        return {"action": "weather", "city": weather_city.group(1).strip()}

    # News
    if cmd in ["news", "latest news", "top news", "headlines", "today's news", "show news"]:
        return {"action": "news", "category": "technology"}
    news_cat = re.search(r"(technology|tech|business|science|world)\s+news", cmd)
    if news_cat:
        return {"action": "news", "category": news_cat.group(1).strip()}

    # YouTube playback: "play <query> on youtube", "play <query>"
    yt_match = re.search(r"play\s+(.+?)(?:\s+on\s+youtube)?$", cmd)
    if yt_match and not any(k in cmd for k in ["pause", "resume", "next", "prev", "stop", "music"]):
        song = yt_match.group(1).strip()
        if song:
            return {"action": "play_youtube", "query": song}

    # Notes
    if cmd in ["show notes", "show my notes", "get notes", "list notes", "my notes"]:
        return {"action": "list_notes"}
    if cmd in ["clear notes", "delete all notes"]:
        return {"action": "clear_notes"}
    note_match = re.search(r"(?:take\s+a?\s*note|add\s+note|remember|note down)[:\s]+(.+)", cmd)
    if note_match:
        return {"action": "add_note", "text": note_match.group(1).strip()}

    # Timer: "set a timer for 5 minutes", "timer 30 seconds"
    timer_match = re.search(r"(?:set\s+a?\s*)?timer\s+(?:for\s+)?(\d+)\s*(seconds?|secs?|minutes?|mins?|hours?|hrs?)?", cmd)
    if timer_match:
        val = int(timer_match.group(1))
        unit = (timer_match.group(2) or "seconds").lower()
        if "min" in unit:
            secs = val * 60
        elif "hour" in unit or "hr" in unit:
            secs = val * 3600
        else:
            secs = val
        return {"action": "set_timer", "seconds": secs, "label": f"{val} {unit}"}

    # Open Applications / Websites
    if cmd.startswith("open "):
        target = cmd[5:].strip()

        # Known web shortcuts
        web_map = {
            "youtube": "https://youtube.com",
            "google": "https://google.com",
            "github": "https://github.com",
            "reddit": "https://reddit.com",
            "instagram": "https://instagram.com",
            "facebook": "https://facebook.com",
            "gmail": "https://mail.google.com",
            "chatgpt": "https://chatgpt.com",
            "chat gpt": "https://chatgpt.com",
            "stackoverflow": "https://stackoverflow.com",
            "stack overflow": "https://stackoverflow.com",
            "twitter": "https://x.com",
            "x": "https://x.com",
            "netflix": "https://netflix.com",
        }
        if target in web_map:
            return {"action": "open_website", "target": web_map[target]}

        if target in APPLICATION_ALIASES:
            return {"action": "open_app", "target": APPLICATION_ALIASES[target]}

        if target.startswith(("http://", "https://", "www.")) or ("." in target and " " not in target):
            url = target if target.startswith("http") else f"https://{target}"
            return {"action": "open_website", "target": url}

        return {"action": "open_app", "target": target}

    # File browsing
    if cmd in ["show my files", "list files", "show files"]:
        return {"action": "list_files"}
    if cmd.startswith("find file ") or cmd.startswith("find "):
        q = cmd.split(" ", 2)[-1].strip()
        return {"action": "search_files", "query": q}
    if cmd.startswith("read file ") or cmd.startswith("read "):
        p = cmd.split(" ", 2)[-1].strip()
        return {"action": "read_file", "path": p}

    # Search web
    if cmd.startswith("search ") or cmd.startswith("google "):
        q = cmd.split(" ", 1)[1].strip()
        return {"action": "search", "query": q}

    # Factual instant search
    if any(cmd.startswith(prefix) for prefix in ["who is ", "what is ", "where is ", "tell me about ", "define "]):
        # Let quick factual questions be checked by instant answer
        return {"action": "instant_answer", "query": command.strip()}

    return None


# ============================================================
# TIER 2 & 3: LLM PARSER & CONVERSATIONAL BRAIN
# ============================================================

SYSTEM_PROMPT = f"""You are {BUTLER_NAME}, Tony Stark's sophisticated, witty, and polite AI assistant running locally on Windows.
The user is your creator and master, addressed as '{USER_TITLE}'.

Your tasks:
1. If the user gives a command, return a JSON object with the appropriate action.
2. If the user asks a conversational question, greeting, or request for advice, return an action of "chat" with a charming, refined, butler-like response in "reply".

NEVER output raw markdown code blocks. Output ONLY valid JSON.

AVAILABLE ACTION SCHEMAS:
- System Status: {{"action": "system_status"}}
- Top Processes: {{"action": "top_processes"}}
- Volume: {{"action": "set_volume", "level": 50}} or {{"action": "volume_up"}} or {{"action": "volume_down"}} or {{"action": "mute"}} or {{"action": "unmute"}}
- Media: {{"action": "media_play_pause"}} or {{"action": "media_next"}} or {{"action": "media_prev"}}
- Lock PC: {{"action": "lock_pc"}}
- Daily Briefing: {{"action": "daily_briefing"}}
- Weather: {{"action": "weather", "city": "auto"}}
- News: {{"action": "news", "category": "technology"}}
- Play on YouTube: {{"action": "play_youtube", "query": "song or video name"}}
- Notes: {{"action": "add_note", "text": "content"}} or {{"action": "list_notes"}} or {{"action": "clear_notes"}}
- Timers: {{"action": "set_timer", "seconds": 300, "label": "tea"}}
- Open Application: {{"action": "open_app", "target": "Application Name"}}
- Open Website: {{"action": "open_website", "target": "https://..."}}
- Search Web: {{"action": "search", "query": "search query"}}
- File Search: {{"action": "search_files", "query": "filename"}}
- Read File: {{"action": "read_file", "path": "filename.py"}}
- Screenshot: {{"action": "take_screenshot"}}
- Exit: {{"action": "exit"}}
- Chat/Conversation/Q&A:
  {{"action": "chat", "reply": "A witty, polite, and helpful answer in character as Jarvis, calling the user {USER_TITLE}."}}

Examples:
- "Hello Jarvis" -> {{"action": "chat", "reply": "Good day, {USER_TITLE}. All systems are online and functioning at peak efficiency. How may I assist you?"}}
- "Who are you?" -> {{"action": "chat", "reply": "I am {BUTLER_NAME}, your personal AI butler and system manager, {USER_TITLE}."}}
- "What can you do?" -> {{"action": "chat", "reply": "I can control system audio, monitor hardware diagnostics, play media on YouTube, fetch real-time weather and news, manage files and notes, and oversee your workstation, {USER_TITLE}."}}
- "Turn down the sound a bit" -> {{"action": "volume_down", "step": 15}}
- "I need some music to focus" -> {{"action": "play_youtube", "query": "focus ambient music"}}
"""


def _clean_json_str(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


def interpret(command: str) -> dict:
    """
    Main interpreter entry point.
    Executes fast-matcher first. If unmatched, uses Ollama Llama 3.2.
    """
    if not command or not command.strip():
        return {"action": "chat", "reply": f"Yes, {USER_TITLE}?"}

    # 1. Tier 1: Zero-latency Fast Match
    fast_result = fast_match_command(command)
    if fast_result is not None:
        return fast_result

# ============================================================
# TIER 2 & 3: SELF-HEALING NEURAL CORE CLIENT
# ============================================================

import requests
import subprocess
import time

_active_model = OLLAMA_MODEL
_neural_core_checked = False


def ensure_neural_core():
    """
    Check if Ollama service is reachable. If not, attempt to start it.
    Auto-detect the best installed Llama model.
    """
    global _active_model, _neural_core_checked

    ollama_url = "http://127.0.0.1:11434/api/tags"

    # Step 1: Probe HTTP endpoint
    try:
        res = requests.get(ollama_url, timeout=1.5)
        if res.status_code == 200:
            data = res.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            for candidate in [OLLAMA_MODEL, f"{OLLAMA_MODEL}:latest", OLLAMA_FAST_MODEL, "llama3.2:latest", "llama3.2:1b"]:
                if candidate in models:
                    _active_model = candidate
                    break
            _neural_core_checked = True
            return True, _active_model
    except Exception:
        pass

    # Step 2: Try starting Ollama service automatically
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        # Wait up to 3 seconds for boot
        for _ in range(6):
            time.sleep(0.5)
            try:
                res = requests.get(ollama_url, timeout=1.0)
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    for candidate in [OLLAMA_MODEL, f"{OLLAMA_MODEL}:latest", OLLAMA_FAST_MODEL, "llama3.2:latest", "llama3.2:1b"]:
                        if candidate in models:
                            _active_model = candidate
                            break
                    _neural_core_checked = True
                    return True, _active_model
            except Exception:
                continue
    except Exception:
        pass

    return False, "Ollama service unavailable"


def _query_neural_core(command: str) -> dict:
    """
    Query Llama 3.2 via direct HTTP with fallback to the ollama Python client.
    """
    global _active_model

    ensure_neural_core()

    # Approach A: Direct REST HTTP (Fastest, zero package dependencies)
    try:
        payload = {
            "model": _active_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": command}
            ],
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 100
            }
        }
        res = requests.post("http://127.0.0.1:11434/api/chat", json=payload, timeout=60)
        if res.status_code == 200:
            content = res.json().get("message", {}).get("content", "")
            cleaned = _clean_json_str(content)
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict) and "action" in parsed:
                return parsed
            return {"action": "chat", "reply": str(parsed.get("reply", parsed))}
    except Exception:
        pass

    # Approach B: Python ollama library fallback
    if HAS_OLLAMA:
        try:
            response = ollama.chat(
                model=_active_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": command}
                ],
                format="json",
                options={
                    "temperature": 0.3,
                    "num_predict": 100
                }
            )
            raw_content = response["message"]["content"]
            cleaned = _clean_json_str(raw_content)
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict) and "action" in parsed:
                return parsed
            return {"action": "chat", "reply": str(parsed.get("reply", parsed))}
        except Exception:
            pass

    return {
        "action": "chat",
        "reply": f"Right away, {USER_TITLE}. All auxiliary systems remain operational, though the neural core is cycling. How else may I assist you?"
    }


def interpret(command: str) -> dict:
    """
    Main interpreter entry point.
    Executes fast-matcher first (<10ms). If unmatched, queries the neural core.
    """
    if not command or not command.strip():
        return {"action": "chat", "reply": f"Yes, {USER_TITLE}?"}

    # 1. Tier 1: Zero-latency Fast Match
    fast_result = fast_match_command(command)
    if fast_result is not None:
        return fast_result

    # 2. Tier 2 & 3: Neural Core Query
    return _query_neural_core(command)