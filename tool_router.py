# ============================================================
# JARVIS TOOL ROUTER
# Routes parsed actions to the appropriate system/intelligence module
# ============================================================

import os
import urllib.parse

from config import USER_TITLE

# Existing tools
from tools import (
    open_website,
    open_windows_app,
    open_vscode,
    open_downloads,
    open_terminal,
    open_path,
)

# File tools
from file_manager import (
    list_files,
    search_files,
    search_file_content,
    read_file,
)

from file_index import (
    initialize_database,
    rebuild_index,
    search_index,
)

# System controller
import system_controller

# Intelligence suite
import intelligence

# Speech engine
import speech_engine


# ============================================================
# EXECUTION ROUTER
# ============================================================

def execute(command):
    """
    Execute parsed command dictionary and return structured result.
    """
    if not isinstance(command, dict):
        return {
            "success": False,
            "error": "Invalid command format."
        }

    action = command.get("action")

    # ========================================================
    # CONVERSATIONAL CHAT
    # ========================================================
    if action == "chat":
        reply = command.get("reply", "At your service, sir.")
        return {
            "success": True,
            "message": reply,
            "speak": reply,
            "chat": True
        }

    # ========================================================
    # SYSTEM HARDWARE & DIAGNOSTICS
    # ========================================================
    if action == "system_status":
        stats = system_controller.get_system_status()
        summary = (
            f"CPU: {stats['cpu_usage']}% ({stats['cpu_count']} cores) | "
            f"RAM: {stats['ram_percent']}% ({stats['ram_used_gb']}/{stats['ram_total_gb']} GB) | "
            f"Power: {stats['battery_status']} | Uptime: {stats['uptime']}"
        )
        spoken = f"All systems nominal, {USER_TITLE}. CPU is at {stats['cpu_usage']} percent, and memory utilization is {stats['ram_percent']} percent."
        return {
            "success": True,
            "stats": stats,
            "message": summary,
            "speak": spoken
        }

    if action == "top_processes":
        procs = system_controller.get_top_processes(limit=5)
        lines = [f"{p['name']} (PID: {p['pid']}) - {p['memory_mb']} MB RAM" for p in procs]
        summary = "Top Active Processes:\n" + "\n".join(lines)
        spoken = f"Retrieved top resource consuming processes, {USER_TITLE}."
        return {
            "success": True,
            "processes": procs,
            "message": summary,
            "speak": spoken
        }

    # ========================================================
    # AUDIO & VOLUME CONTROL
    # ========================================================
    if action == "get_volume":
        vol = system_controller.get_volume()
        muted = system_controller.is_muted()
        mute_str = " (Muted)" if muted else ""
        return {
            "success": True,
            "volume": vol,
            "message": f"Master volume is at {vol}%{mute_str}.",
            "speak": f"Master volume is at {vol} percent."
        }

    if action == "set_volume":
        level = command.get("level", 50)
        success, msg = system_controller.set_volume(level)
        return {
            "success": success,
            "message": msg,
            "speak": f"Volume set to {level} percent, {USER_TITLE}."
        }

    if action == "volume_up":
        step = command.get("step", 10)
        success, msg = system_controller.volume_up(step)
        return {
            "success": success,
            "message": msg,
            "speak": f"Volume increased, {USER_TITLE}."
        }

    if action == "volume_down":
        step = command.get("step", 10)
        success, msg = system_controller.volume_down(step)
        return {
            "success": success,
            "message": msg,
            "speak": f"Volume decreased, {USER_TITLE}."
        }

    if action == "mute":
        success, msg = system_controller.set_mute(True)
        return {
            "success": success,
            "message": msg,
            "speak": "" # Don't speak after muting
        }

    if action == "unmute":
        success, msg = system_controller.set_mute(False)
        return {
            "success": success,
            "message": msg,
            "speak": f"Audio unmuted, {USER_TITLE}."
        }

    if action == "toggle_mute":
        success, msg = system_controller.toggle_mute()
        return {
            "success": success,
            "message": msg,
            "speak": msg
        }

    # ========================================================
    # MEDIA PLAYBACK CONTROLS
    # ========================================================
    if action == "media_play_pause":
        success, msg = system_controller.media_play_pause()
        return {"success": success, "message": msg, "speak": msg}

    if action == "media_next":
        success, msg = system_controller.media_next()
        return {"success": success, "message": msg, "speak": "Next track."}

    if action == "media_prev":
        success, msg = system_controller.media_prev()
        return {"success": success, "message": msg, "speak": "Previous track."}

    if action == "media_stop":
        success, msg = system_controller.media_stop()
        return {"success": success, "message": msg, "speak": "Media stopped."}

    # ========================================================
    # WINDOWS & DESKTOP CONTROLS
    # ========================================================
    if action == "lock_pc":
        success, msg = system_controller.lock_pc()
        return {"success": success, "message": msg, "speak": f"Locking workstation, {USER_TITLE}."}

    if action == "sleep_pc":
        success, msg = system_controller.sleep_pc()
        return {"success": success, "message": msg, "speak": f"System entering standby, {USER_TITLE}."}

    if action == "shutdown_pc":
        confirmed = command.get("confirm", False)
        success, msg = system_controller.shutdown_pc(confirmed=confirmed)
        return {"success": success, "message": msg, "speak": msg}

    if action == "restart_pc":
        confirmed = command.get("confirm", False)
        success, msg = system_controller.restart_pc(confirmed=confirmed)
        return {"success": success, "message": msg, "speak": msg}

    if action == "cancel_shutdown":
        success, msg = system_controller.cancel_shutdown()
        return {"success": success, "message": msg, "speak": f"Shutdown sequence aborted, {USER_TITLE}."}

    if action == "show_desktop":
        success, msg = system_controller.show_desktop()
        return {"success": success, "message": msg, "speak": "Desktop displayed."}

    if action == "open_task_manager":
        success, msg = system_controller.open_task_manager()
        return {"success": success, "message": msg, "speak": "Task Manager opened."}

    if action == "open_settings":
        success, msg = system_controller.open_settings()
        return {"success": success, "message": msg, "speak": "Settings opened."}

    # ========================================================
    # SCREENSHOT & WEBCAM
    # ========================================================
    if action == "take_screenshot":
        success, msg = system_controller.take_screenshot()
        return {
            "success": success,
            "message": msg,
            "speak": f"Screenshot captured, {USER_TITLE}." if success else "Failed to capture screenshot."
        }

    if action == "capture_photo":
        success, msg = system_controller.capture_photo()
        return {
            "success": success,
            "message": msg,
            "speak": f"Photo taken, {USER_TITLE}." if success else msg
        }

    # ========================================================
    # CLIPBOARD
    # ========================================================
    if action == "get_clipboard":
        text = system_controller.get_clipboard_text()
        return {
            "success": True,
            "content": text,
            "message": f"Clipboard content:\n{text}",
            "speak": "Retrieved clipboard content, sir."
        }

    if action == "set_clipboard":
        text = command.get("text", "")
        success, msg = system_controller.set_clipboard_text(text)
        return {"success": success, "message": msg, "speak": "Copied to clipboard."}

    # ========================================================
    # WEATHER & NEWS
    # ========================================================
    if action == "weather":
        city = command.get("city")
        data = intelligence.get_weather(city)
        if data.get("success"):
            summary = data.get("summary")
            temp = data.get("temp_c")
            desc = data.get("description", "clear")
            loc = data.get("location", "")
            spoken = f"The weather in {loc} is currently {desc} at {temp} degrees Celsius." if temp != "N/A" else summary
            return {
                "success": True,
                "weather": data,
                "message": summary,
                "speak": spoken
            }
        return {"success": False, "error": data.get("error", "Weather unavailable.")}

    if action == "news":
        category = command.get("category", "technology")
        data = intelligence.get_news(category=category, limit=5)
        if data.get("success"):
            articles = data.get("articles", [])
            lines = [f"• {a['title']}" for a in articles]
            summary = f"Top {category.capitalize()} Headlines:\n" + "\n".join(lines)
            spoken = f"Here are the top {category} headlines, {USER_TITLE}."
            return {
                "success": True,
                "news": articles,
                "message": summary,
                "speak": spoken
            }
        return {"success": False, "error": data.get("error", "News unavailable.")}

    # ========================================================
    # DAILY BRIEFING
    # ========================================================
    if action == "daily_briefing":
        briefing = intelligence.get_daily_briefing()
        display_msg = (
            f"{briefing['greeting']}\n"
            f"Date & Time: {briefing['date']} | {briefing['time']}\n"
            f"Weather: {briefing['weather'].get('summary', 'Unavailable')}\n"
            f"Notes: {briefing['note_count']} active notes."
        )
        return {
            "success": True,
            "briefing": briefing,
            "message": display_msg,
            "speak": briefing["spoken_text"]
        }

    # ========================================================
    # YOUTUBE PLAYBACK
    # ========================================================
    if action == "play_youtube":
        query = command.get("query", "")
        if not query:
            return {"success": False, "error": "No song or video title specified."}
        data = intelligence.play_on_youtube(query)
        return {
            "success": True,
            "message": data["message"],
            "speak": data["message"]
        }

    # ========================================================
    # INSTANT FACTUAL ANSWER / WIKIPEDIA
    # ========================================================
    if action == "instant_answer":
        query = command.get("query", "")
        data = intelligence.get_instant_answer(query)
        if data.get("success"):
            return {
                "success": True,
                "title": data.get("title"),
                "summary": data.get("summary"),
                "message": f"[{data.get('title')}]\n{data.get('summary')}",
                "speak": data.get("summary")
            }
        # Fallback to web search
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        open_website(url)
        return {
            "success": True,
            "message": f"Searching web for '{query}'",
            "speak": f"I have initiated a web search for '{query}', {USER_TITLE}."
        }

    # ========================================================
    # NOTES & MEMORY
    # ========================================================
    if action == "add_note":
        text = command.get("text", "")
        res = intelligence.add_note(text)
        return {
            "success": res["success"],
            "message": res.get("message", res.get("error")),
            "speak": f"Note recorded, {USER_TITLE}."
        }

    if action == "list_notes":
        notes = intelligence.get_all_notes()
        if not notes:
            return {
                "success": True,
                "notes": [],
                "message": "You have no saved notes.",
                "speak": f"You have no pending notes on file, {USER_TITLE}."
            }
        lines = [f"#{n['id']} [{n['created_at']}]: {n['text']}" for n in notes]
        return {
            "success": True,
            "notes": notes,
            "message": "Saved Notes:\n" + "\n".join(lines),
            "speak": f"You have {len(notes)} saved {'note' if len(notes)==1 else 'notes'}, {USER_TITLE}."
        }

    if action == "clear_notes":
        res = intelligence.clear_all_notes()
        return {
            "success": True,
            "message": res["message"],
            "speak": f"All notes cleared, {USER_TITLE}."
        }

    # ========================================================
    # TIMERS & COUNTDOWN
    # ========================================================
    if action == "set_timer":
        seconds = command.get("seconds", 60)
        label = command.get("label", "Timer")
        res = intelligence.set_timer(seconds, label)
        return {
            "success": True,
            "message": res["message"],
            "speak": f"Timer set for {seconds} seconds, {USER_TITLE}."
        }

    # ========================================================
    # VOICE ENGINE TOGGLE
    # ========================================================
    if action == "toggle_voice":
        state = speech_engine.toggle_voice()
        state_str = "enabled" if state else "muted"
        return {
            "success": True,
            "voice_enabled": state,
            "message": f"Voice synthesis is now {state_str}.",
            "speak": f"Voice synthesis {state_str}, {USER_TITLE}." if state else ""
        }

    if action == "set_voice":
        enabled = command.get("enabled", True)
        state = speech_engine.set_voice_enabled(enabled)
        state_str = "enabled" if state else "muted"
        return {
            "success": True,
            "voice_enabled": state,
            "message": f"Voice synthesis {state_str}.",
            "speak": f"Voice synthesis {state_str}." if state else ""
        }

    # ========================================================
    # EXISTING WEBSITE / APP / FILE TOOLS
    # ========================================================
    if action == "open_website":
        url = command.get("target")
        if not url:
            return {"success": False, "error": "No website specified."}
        open_website(url)
        return {
            "success": True,
            "message": f"Opened {url}",
            "speak": f"Opening {url.split('//')[-1].split('/')[0]}, {USER_TITLE}."
        }

    if action == "open_app":
        app = command.get("target")
        if not app:
            return {"success": False, "error": "No application specified."}

        app_lower = app.lower()
        if app_lower in ["visual studio code", "vscode"]:
            success = open_vscode()
        elif app_lower in ["task manager", "taskmgr"]:
            success, _ = system_controller.open_task_manager()
        elif app_lower in ["settings"]:
            success, _ = system_controller.open_settings()
        elif app_lower in ["cmd", "terminal", "command prompt"]:
            success = open_terminal()
        elif app_lower in ["downloads", "download"]:
            success = open_downloads()
        else:
            success = open_windows_app(app)

        return {
            "success": success,
            "message": f"Started {app}",
            "speak": f"Launching {app}, {USER_TITLE}."
        }

    if action == "open_downloads":
        success = open_downloads()
        return {"success": success, "message": "Opened Downloads folder.", "speak": "Downloads folder opened."}

    if action == "open_terminal":
        success = open_terminal()
        return {"success": success, "message": "Opened Command Prompt.", "speak": "Terminal opened."}

    if action == "search":
        query = command.get("query")
        if not query:
            return {"success": False, "error": "No search query specified."}
        encoded = urllib.parse.quote(query)
        url = f"https://www.google.com/search?q={encoded}"
        open_website(url)
        return {
            "success": True,
            "message": f"Searching for '{query}'",
            "speak": f"Searching the web for '{query}', {USER_TITLE}."
        }

    if action == "list_files":
        path = command.get("path")
        return list_files(path)

    if action == "search_files":
        query = command.get("query")
        if not query:
            return {"success": False, "error": "No file search query."}
        return search_files(query)

    if action == "search_file_content":
        query = command.get("query")
        if not query:
            return {"success": False, "error": "No content search query."}
        return search_file_content(query)

    if action == "read_file":
        path = command.get("path")
        if not path:
            return {"success": False, "error": "No file path."}
        return read_file(path)

    return {
        "success": False,
        "error": f"Unknown action: {action}"
    }


# ============================================================
# INITIALIZE
# ============================================================

def initialize():
    """
    Initialize all Jarvis core subsystems.
    """
    initialize_database()
    intelligence.init_notes_db()
    speech_engine.init_speech_engine()