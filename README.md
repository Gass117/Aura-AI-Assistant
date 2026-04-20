# Aura AI Assistant

Aura AI Assistant è un copilota visivo universale per il tuo desktop. 
Si "attacca" alla finestra che selezioni, ne osserva lo stato catturando screenshot ogni N secondi e ti permette di chattare con Gemini, che risponderà conoscendo il contesto visivo e testuale del programma che stai usando.

## Requisiti

- Python 3.12+
- Sistema Operativo: Windows

## Installazione

1. Clona o estrai il progetto.
2. Crea un ambiente virtuale (consigliato):
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
3. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```
4. Configura la chiave API di Gemini. Crea un file `.env` nella directory radice del progetto e aggiungi la tua chiave:
   ```env
   GEMINI_API_KEY=la_tua_chiave_api_qui
   ```

## Esecuzione

Avvia l'applicazione eseguendo:
```bash
python main.py
```

## Funzionalità
- **Selezione Finestra**: Scegli dal menu a tendina quale finestra l'assistente deve osservare.
- **Opacità Regolabile**: L'interfaccia è Always-on-Top; puoi regolarne la trasparenza per non intralciare il lavoro.
- **Contesto Dinamico**: Il nome della finestra attiva diventerà automaticamente parte del "System Prompt" di Gemini.
- **Miniatura**: Visualizza l'ultimo screenshot catturato in tempo reale (richiamabile anche tramite shortcut, default `Ctrl+Shift+A`).
