# ============================================================
# JARVIS SYSTEM CONFIGURATION
# ============================================================

BUTLER_NAME = "JARVIS"
USER_TITLE = "Sir"

# Ollama local LLM models
OLLAMA_MODEL = "llama3.2:1b"
OLLAMA_FAST_MODEL = "llama3.2:1b"

# ============================================================
# VOICE & AUDIO (TEXT-TO-SPEECH & RECOGNITION)
# ============================================================

VOICE_ENABLED = True          # Can be toggled live via 'voice on' / 'voice off'
VOICE_RATE = 185              # Words per minute (crisp, confident cadence)
VOICE_VOLUME = 0.95           # 0.0 to 1.0
VOICE_PREFERRED_NAME = "David" # Preferred voice keyword (e.g., David / Zira)

# Microphone speech recognition settings
SPEECH_ENERGY_THRESHOLD = 300
SPEECH_PAUSE_THRESHOLD = 0.8
SPEECH_LISTEN_TIMEOUT = 5.0
SPEECH_PHRASE_TIME_LIMIT = 8.0

# ============================================================
# DAILY BRIEFING & INTELLIGENCE
# ============================================================

DEFAULT_CITY = "auto"         # 'auto' or specify a city like 'New York', 'London', 'Kolkata'
NEWS_CATEGORY = "technology"  # technology, general, science, business

# ============================================================
# MEMORY & NOTES DATABASE
# ============================================================

DATABASE = "astra.db"
NOTES_DB = "jarvis_memory.db"

# ============================================================
# SECURITY & SAFETY
# ============================================================

REQUIRE_CONFIRMATION_FOR_POWER = True  # Shutdown / Restart requires explicit confirmation

# Allowed folders for file searching & reading
ALLOWED_FOLDERS = [
    r"D:\FunPlus\Desktop\Butler",
    r"D:\FunPlus\Desktop\Hackathon",
]

MAX_FILE_SIZE_MB = 10

TEXT_FILE_EXTENSIONS = {
    ".txt",
    ".md",
    ".py",
    ".js",
    ".html",
    ".css",
    ".json",
    ".yaml",
    ".yml",
    ".xml",
    ".csv",
    ".sql",
    ".ini",
    ".cfg",
    ".log",
    ".toml",
}

# ============================================================
# APPLICATION ALIASES & PATHS
# ============================================================

APPLICATION_ALIASES = {
    "vscode": "Visual Studio Code",
    "vs code": "Visual Studio Code",
    "visual studio code": "Visual Studio Code",
    "code": "Visual Studio Code",

    "chrome": "Google Chrome",
    "google chrome": "Google Chrome",
    "browser": "Google Chrome",

    "edge": "Microsoft Edge",
    "ms edge": "Microsoft Edge",

    "calculator": "Calculator",
    "calc": "Calculator",

    "notepad": "Notepad",
    "editor": "Notepad",

    "paint": "Paint",
    "mspaint": "Paint",

    "explorer": "File Explorer",
    "file explorer": "File Explorer",
    "files": "File Explorer",

    "spotify": "Spotify",
    "music": "Spotify",

    "discord": "Discord",
    "steam": "Steam",
    "telegram": "Telegram",
    "whatsapp": "WhatsApp",

    "task manager": "Task Manager",
    "taskmgr": "Task Manager",

    "settings": "Settings",
    "control panel": "Control Panel",
    "cmd": "Command Prompt",
    "terminal": "Windows Terminal",
    "powershell": "PowerShell",
}