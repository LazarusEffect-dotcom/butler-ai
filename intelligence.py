# ============================================================
# JARVIS INTELLIGENCE SUITE
# Weather, News, Daily Briefing, YouTube, Notes, and Timers
# ============================================================

import datetime
import os
import re
import sqlite3
import threading
import time
import urllib.parse
import webbrowser
import xml.etree.ElementTree as ET

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from config import (
    DEFAULT_CITY,
    NEWS_CATEGORY,
    NOTES_DB,
    USER_TITLE,
)
from speech_engine import speak

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


# ============================================================
# LIVE WEATHER
# ============================================================

def get_weather(city=None):
    """
    Fetch live weather for specified city or auto-detected location.
    """
    if not city or city.lower() == "auto":
        city = DEFAULT_CITY if DEFAULT_CITY != "auto" else ""

    target_city = city.strip()
    encoded_city = urllib.parse.quote(target_city) if target_city else ""
    url = f"https://wttr.in/{encoded_city}?format=j1"

    headers = {
        "User-Agent": "curl/7.88.1"
    }

    try:
        response = requests.get(url, headers=headers, verify=False, timeout=6)
        if response.status_code == 200:
            data = response.json()
            current = data.get("current_condition", [{}])[0]
            nearest = data.get("nearest_area", [{}])[0]

            loc_name = ""
            if nearest.get("areaName"):
                loc_name = nearest["areaName"][0].get("value", "")
            if nearest.get("country"):
                loc_name += f", {nearest['country'][0].get('value', '')}"

            temp_c = current.get("temp_C", "N/A")
            desc = current.get("weatherDesc", [{}])[0].get("value", "Clear")
            humidity = current.get("humidity", "N/A")
            wind_kmph = current.get("windspeedKmph", "N/A")

            return {
                "success": True,
                "location": loc_name or (target_city.capitalize() if target_city else "Your Area"),
                "temp_c": temp_c,
                "description": desc,
                "humidity": humidity,
                "wind_kmph": wind_kmph,
                "summary": f"{desc}, {temp_c}°C in {loc_name or target_city} (Humidity: {humidity}%, Wind: {wind_kmph} km/h)"
            }
    except Exception as e:
        pass

    # Quick plain format fallback
    try:
        url_plain = f"https://wttr.in/{encoded_city}?format=%l:+%c+%t,+%w+(%h+humidity)"
        res = requests.get(url_plain, headers=headers, verify=False, timeout=5)
        if res.status_code == 200 and res.text:
            cleaned = res.text.strip()
            return {
                "success": True,
                "location": target_city or "Current Location",
                "summary": cleaned
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unable to retrieve weather data: {e}"
        }

    return {
        "success": False,
        "error": "Weather service currently unavailable."
    }


# ============================================================
# LIVE NEWS HEADLINES
# ============================================================

def get_news(category=None, limit=5):
    """
    Fetch top headlines via Google News RSS.
    """
    cat = (category or NEWS_CATEGORY).lower()
    topic_map = {
        "technology": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB",
        "tech": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB",
        "business": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB",
        "science": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFptTXpJU0FtVnVHZ0pWVXlnQVAB",
        "world": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB",
    }

    topic_id = topic_map.get(cat)
    if topic_id:
        url = f"https://news.google.com/rss/topics/{topic_id}?hl=en-US&gl=US&ceid=US:en"
    else:
        url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"

    try:
        response = requests.get(url, verify=False, timeout=6)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            items = []
            for item in root.findall(".//item"):
                title_elem = item.find("title")
                link_elem = item.find("link")
                pub_elem = item.find("pubDate")

                if title_elem is not None and title_elem.text:
                    clean_title = title_elem.text.rsplit(" - ", 1)[0]
                    items.append({
                        "title": clean_title,
                        "link": link_elem.text if link_elem is not None else "",
                        "date": pub_elem.text if pub_elem is not None else "",
                    })
                if len(items) >= limit:
                    break

            return {
                "success": True,
                "category": cat,
                "articles": items
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to retrieve news: {e}",
            "articles": []
        }

    return {
        "success": False,
        "error": "News feed unavailable.",
        "articles": []
    }


# ============================================================
# INSTANT FACTUAL SEARCH (WIKIPEDIA / DUCKDUCKGO)
# ============================================================

def get_instant_answer(query: str):
    """
    Query Wikipedia Summary API for instant factual lookups.
    """
    clean_q = query.strip().rstrip("?").strip()
    # Strip leading question words
    for prefix in ["who is ", "what is ", "where is ", "tell me about ", "define ", "who was ", "what was "]:
        if clean_q.lower().startswith(prefix):
            clean_q = clean_q[len(prefix):].strip()
            break

    # Wikipedia REST API
    encoded = urllib.parse.quote(clean_q.replace(" ", "_"))
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"

    try:
        headers = {"User-Agent": "JarvisAssistant/2.0"}
        res = requests.get(url, headers=headers, verify=False, timeout=5)
        if res.status_code == 200:
            data = res.json()
            extract = data.get("extract")
            title = data.get("title")
            if extract:
                # Limit extract to 2-3 sentences
                sentences = extract.split(". ")
                short_summary = ". ".join(sentences[:2])
                if not short_summary.endswith("."):
                    short_summary += "."
                return {
                    "success": True,
                    "title": title,
                    "summary": short_summary,
                    "url": data.get("content_urls", {}).get("desktop", {}).get("page", "")
                }
    except Exception:
        pass

    # DuckDuckGo fallback
    try:
        ddg_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(clean_q)}&format=json&no_html=1&skip_disambig=1"
        res = requests.get(ddg_url, verify=False, timeout=4)
        if res.status_code == 200:
            data = res.json()
            abstract = data.get("AbstractText")
            if abstract:
                return {
                    "success": True,
                    "title": data.get("Heading", clean_q),
                    "summary": abstract,
                    "url": data.get("AbstractURL", "")
                }
    except Exception:
        pass

    return {
        "success": False,
        "error": "No instant answer found."
    }


# ============================================================
# YOUTUBE PLAYBACK
# ============================================================

def play_on_youtube(query: str):
    """
    Open and auto-play YouTube video/song matching query.
    """
    clean_q = query.strip()
    encoded = urllib.parse.quote_plus(clean_q)
    url = f"https://www.youtube.com/results?search_query={encoded}"

    # Try to find direct video link
    try:
        search_url = f"https://www.youtube.com/results?search_query={encoded}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(search_url, headers=headers, verify=False, timeout=5)
        if resp.status_code == 200:
            video_ids = re.findall(r"watch\?v=([a-zA-Z0-9_-]{11})", resp.text)
            if video_ids:
                url = f"https://www.youtube.com/watch?v={video_ids[0]}"
    except Exception:
        pass

    webbrowser.open(url)
    return {
        "success": True,
        "query": clean_q,
        "url": url,
        "message": f"Playing '{clean_q}' on YouTube, {USER_TITLE}."
    }


# ============================================================
# DAILY BRIEFING
# ============================================================

def get_daily_briefing():
    """
    Generate an Iron Man-style daily briefing.
    """
    now = datetime.datetime.now()
    hour = now.hour

    if hour < 12:
        greeting = f"Good morning, {USER_TITLE}."
    elif hour < 17:
        greeting = f"Good afternoon, {USER_TITLE}."
    else:
        greeting = f"Good evening, {USER_TITLE}."

    date_str = now.strftime("%A, %B %d, %Y")
    time_str = now.strftime("%I:%M %p")

    # Fetch weather
    weather = get_weather()
    weather_desc = weather.get("summary", "Weather data is currently unavailable.")

    # Notes count
    notes = get_all_notes()
    note_count = len(notes)
    notes_summary = f"You have {note_count} active {'note' if note_count == 1 else 'notes'} on file." if note_count else "You have no pending notes."

    spoken_briefing = (
        f"{greeting} The time is {time_str} on {date_str}. "
        f"Weather report: {weather.get('temp_c', '')} degrees and {weather.get('description', 'clear')}. "
        f"{notes_summary} All core systems are functioning normally."
    )

    return {
        "success": True,
        "greeting": greeting,
        "date": date_str,
        "time": time_str,
        "weather": weather,
        "note_count": note_count,
        "spoken_text": spoken_briefing
    }


# ============================================================
# MEMORY & NOTES (SQLITE)
# ============================================================

def init_notes_db():
    conn = sqlite3.connect(NOTES_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def add_note(text: str):
    init_notes_db()
    clean_text = text.strip()
    if not clean_text:
        return {"success": False, "error": "Note cannot be empty."}

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    conn = sqlite3.connect(NOTES_DB)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notes (text, created_at) VALUES (?, ?)", (clean_text, timestamp))
    conn.commit()
    note_id = cursor.lastrowid
    conn.close()

    return {
        "success": True,
        "id": note_id,
        "message": f"Note saved, {USER_TITLE}."
    }


def get_all_notes():
    init_notes_db()
    conn = sqlite3.connect(NOTES_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id, text, created_at FROM notes ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "text": r[1], "created_at": r[2]} for r in rows]


def delete_note(note_id: int):
    init_notes_db()
    conn = sqlite3.connect(NOTES_DB)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    if deleted:
        return {"success": True, "message": f"Note #{note_id} deleted."}
    return {"success": False, "error": f"Note #{note_id} not found."}


def clear_all_notes():
    init_notes_db()
    conn = sqlite3.connect(NOTES_DB)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes")
    conn.commit()
    conn.close()
    return {"success": True, "message": "All notes have been cleared."}


# ============================================================
# TIMERS & COUNTDOWN
# ============================================================

def set_timer(seconds: int, label: str = "Timer"):
    """
    Set a non-blocking background countdown timer with alert.
    """
    seconds = max(1, int(seconds))

    def _timer_thread():
        time.sleep(seconds)
        if HAS_WINSOUND:
            try:
                for _ in range(3):
                    winsound.Beep(1000, 250)
                    time.sleep(0.1)
            except Exception:
                pass
        alert_msg = f"Alert: Your timer for {label} ({seconds} seconds) has elapsed, {USER_TITLE}."
        print(f"\n\n[JARVIS ALERT: {alert_msg}]\nYou > ", end="", flush=True)
        speak(alert_msg)

    thread = threading.Thread(target=_timer_thread, daemon=True)
    thread.start()

    return {
        "success": True,
        "seconds": seconds,
        "message": f"Timer set for {seconds} seconds ({label})."
    }
