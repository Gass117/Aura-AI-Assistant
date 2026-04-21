import json
import os
import datetime

HISTORY_FILE = "history.json"

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {"Dates": {}, "LastSession": {}}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Backward compatibility check
            if "Windows" in data and "Dates" not in data:
                # Migrate old format to new format under today's date
                today = datetime.datetime.now().strftime("%d/%m/%Y")
                data["Dates"] = {today: data["Windows"]}
                del data["Windows"]
            if "Dates" not in data:
                data["Dates"] = {}
            return data
    except:
        return {"Dates": {}, "LastSession": {}}

def save_history(history_data):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history_data, f, indent=4)
    except Exception as e:
        print(f"Errore salvataggio cronologia: {e}")

def add_to_history(window_title, prompt, html_response):
    data = load_history()
    
    now = datetime.datetime.now()
    date_str = now.strftime("%d/%m/%Y")
    time_str = now.strftime("%H:%M")
    
    if "Dates" not in data:
        data["Dates"] = {}
        
    if date_str not in data["Dates"]:
        data["Dates"][date_str] = {}
        
    if window_title not in data["Dates"][date_str]:
        data["Dates"][date_str][window_title] = []
        
    conversation = {"prompt": prompt, "response": html_response, "time": time_str}
    data["Dates"][date_str][window_title].append(conversation)
    
    # Update Last Session
    data["LastSession"] = {
        "window": window_title,
        "chat_html": f"<b>Tu:</b> {prompt}<br><br><b style='color: #4CAF50;'>Aura:</b><br>{html_response}"
    }
    
    save_history(data)
    return data
