# Piano di Sviluppo (Fase 5: Finestra Dinamica e UI)

## 1. Ridimensionamento su tutti gli angoli (Native Resizing)
Per consentire il ridimensionamento della finestra da tutti i lati (come una normale finestra di Windows) mantenendo il design arrotondato, intercetteremo gli eventi nativi di Windows (`WM_NCHITTEST`) tramite le API di sistema in PyQt6.
- Questo eliminerà la necessità del piccolo "grip" in basso a destra e permetterà di stringere/allargare l'interfaccia da qualsiasi lato e angolo.

## 2. Anteprima "Responsive"
L'altezza fissa (`setFixedHeight(100)`) delle miniature delle finestre catturate verrà rimossa.
- Imposteremo `setMinimumHeight(100)` e utilizzeremo le policy di espansione (es. `QSizePolicy.Policy.Expanding`) affinché le immagini si ingrandiscano o rimpiccioliscano dinamicamente seguendo le dimensioni del programma.

## 3. Bug Icona Mancante
Il bug è causato dal fatto che il percorso dell'icona (`icon.ico`) non veniva risolto correttamente dal file `.exe` durante l'esecuzione autonoma (cercava l'icona sul desktop invece che dentro sé stesso). 
- Aggiungerò una funzione dedicata (`get_resource_path`) per dire all'eseguibile di caricare l'icona dal proprio "pacchetto" interno in modo che la mostri correttamente sulla Taskbar e sulla nuova barra in alto.
- Nello script di PyInstaller forzerò l'inclusione del file icona come allegato dati (`--add-data "icon.ico;."`).

## 4. Cronologia per Date
Modificherò il modulo `history_manager.py`.
- Le conversazioni verranno salvate con data e ora (es. "21/04/2026 12:30").
- La struttura dell'albero laterale diventerà:
  - 📅 Data (es. `21/04/2026`)
    - 💻 Titolo Finestra
      - 💬 "Cosa vedi in questa immagine? [12:30]"

## 5. Tasti Centrali e Testi Completi
- I tre tasti principali diventeranno: **"⚙ Impostazioni"** | **"🔄 Aggiorna"** (cambierò icona) | **"💬 Cronologia"**.
- Saranno disposti orizzontalmente in quest'ordine, con le parole scritte per intero.
- Cambierò l'icona del refresh con qualcosa di più elegante o moderno (es. un simbolo 🔃 o ✨ o un'icona testuale migliore).

### Verifica
Dopo aver applicato i codici, avvierò di nuovo la compilazione con PyInstaller passandogli le giuste dipendenze per l'icona.
