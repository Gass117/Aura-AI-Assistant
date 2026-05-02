import os
import sys
import keyring
from google import genai
from google.genai import types

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

SERVICE_ID = "AuraAIAssistant"
TOKEN_KEY = "GeminiAPIKey"

class ApiManager:
    def __init__(self):
        self.client = None
        self.api_key = None
        self.authenticate()

    def authenticate(self, new_key=None):
        if new_key:
            self.api_key = new_key
            keyring.set_password(SERVICE_ID, TOKEN_KEY, new_key)
        else:
            self.api_key = keyring.get_password(SERVICE_ID, TOKEN_KEY)
            
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"Errore inizializzazione client: {e}")
                self.client = None
        else:
            self.client = None
            
    def logout(self):
        try:
            keyring.delete_password(SERVICE_ID, TOKEN_KEY)
        except keyring.errors.PasswordDeleteError:
            pass
        self.api_key = None
        self.client = None

    def check_api_key(self):
        return self.client is not None

    def send_message(self, window_titles, user_prompt, images=None, model_name='gemini-2.5-flash'):
        if not self.client:
            return "Errore: Autenticazione Google fallita o annullata. Accedi tramite impostazioni per continuare."
            
        if not images:
            images = []
            
        if len(window_titles) == 1:
            system_instruction = f"Sei Aura AI Assistant. L'utente si trova in ambiente '{window_titles[0]}'. Usa lo screenshot fornito per rispondere da esperto nel contesto di questo software."
        else:
            system_instruction = f"Sei Aura AI Assistant. L'utente sta lavorando in modalità 'Doppia Finestra'. La Finestra 1 è '{window_titles[0]}' e la Finestra 2 è '{window_titles[1]}'. L'utente ha fornito gli screenshot di entrambe in ordine. Usa questo doppio contesto per fornire risposte integrate o fare confronti."
            
        try:
            contents = []
            for img in images:
                contents.append(img)
            contents.append(user_prompt)
                
            response_stream = self.client.models.generate_content_stream(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                )
            )
            return response_stream
        except Exception as e:
            error_str = str(e)
            if "403" in error_str and "pro" in model_name.lower():
                return f"**Avviso Aura:** L'account Google collegato non ha accesso al modello Pro ({model_name}). Il software scalerà automaticamente a Flash alla prossima richiesta se selezioni un modello accessibile. \n\n*Dettaglio errore:* {error_str}"
            return f"Errore nell'API: {error_str}"
