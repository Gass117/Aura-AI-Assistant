import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class ApiManager:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def check_api_key(self):
        return self.client is not None

    def send_message(self, window_titles, user_prompt, images=None, model_name='gemini-2.5-flash'):
        """
        window_titles: list of strings
        images: list of PIL.Image
        model_name: string (e.g. 'gemini-2.5-flash')
        """
        if not self.client:
            return "Errore: API Key mancante. Controlla il file .env e riavvia l'app."
            
        if not images:
            images = []
            
        if len(window_titles) == 1:
            system_instruction = f"Sei Aura AI Assistant. L'utente si trova in ambiente '{window_titles[0]}'. Usa lo screenshot fornito per rispondere da esperto nel contesto di questo software."
        else:
            system_instruction = f"Sei Aura AI Assistant. L'utente sta lavorando in modalità 'Doppia Finestra'. La Finestra 1 è '{window_titles[0]}' e la Finestra 2 è '{window_titles[1]}'. L'utente ha fornito gli screenshot di entrambe in ordine. Usa questo doppio contesto per fornire risposte integrate o fare confronti."
            
        try:
            contents = []
            # Aggiunge prima le immagini come contesto
            for img in images:
                contents.append(img)
            # Poi il prompt di testo
            contents.append(user_prompt)
                
            response = self.client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                )
            )
            return response.text
        except Exception as e:
            return f"Errore nell'API: {str(e)}"
