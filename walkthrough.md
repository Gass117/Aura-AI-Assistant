# Aggiornamento: Autenticazione Sicura e Ridimensionamento 🚀

Aura AI Assistant è ora equipaggiato con un login nativo tramite Google Cloud, abbandonando del tutto l'uso di chiavi API fisse, e il ridimensionamento della finestra è finalmente perfetto!

## 🔒 Autenticazione OAuth2 (Google Login)
- **Login Diretto nel Browser**: Alla prima apertura, l'assistente ti chiederà di effettuare il login aprendo automaticamente il browser. Potrai selezionare il tuo account Google e autorizzare in totale sicurezza l'uso di Gemini.
- **Sicurezza Avanzata con Keyring**: Una volta completato il login, le credenziali vengono salvate in maniera crittografata e protetta dal sistema operativo di Windows (nel Gestore Credenziali). L'app le ricorderà in automatico, ma potrai gestirle facilmente.
- **Tasto "Logout Google"**: Abbiamo inserito un bottone dedicato in rosso (nelle **Impostazioni ⚙**) che ti permette di disconnettere immediatamente l'account attualmente collegato e passare ad un altro alla successiva apertura.

## 🧠 Downgrade Intelligente al Modello Flash
- Se provi ad utilizzare il motore **Gemini 1.5 Pro** o **2.5 Pro** con un account che non ne possiede i permessi, l'applicazione intercetterà in automatico l'errore (evitando che l'app si blocchi) e ti informerà direttamente in Chat che è stato effettuato un **downgrade protettivo** per permetterti di continuare a lavorare con la versione Flash senza interruzioni!

## 📐 Ridimensionamento "Invisible Grips"
- Abbiamo implementato 8 `Widget` trasparenti, disposti in maniera millimetrica sui 4 bordi laterali e sui **4 angoli** dell'interfaccia. Adesso puoi posizionarti su uno qualsiasi degli angoli, e potrai ingrandire o restringere la finestra sia in larghezza che in altezza simultaneamente!

*(Il file è stato ricompilato e testato. Assicurati di aprire la versione appena aggiornata nella cartella `dist`!)*
