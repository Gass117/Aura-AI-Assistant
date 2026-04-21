import json
import os

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "font_family": "Segoe UI",
    "font_size": 13,
    "text_color": "#FFFFFF",
    "theme": "Dark", # Dark, Light, Green
    "opacity": 0.9,
    "ai_engine": "Gemini 2.5 Flash"
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            settings = DEFAULT_SETTINGS.copy()
            settings.update(data)
            return settings
    except:
        return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Errore salvataggio impostazioni: {e}")
