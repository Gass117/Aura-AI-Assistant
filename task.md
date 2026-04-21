# Fase 5: Finestra Dinamica e UI

- [/] Modificare `history_manager.py` per includere il raggruppamento per Data
- [ ] Modifiche `interfaccia.py`:
  - [ ] Implementare `get_resource_path` per risolvere i bug dell'icona
  - [ ] Aggiungere gestione `nativeEvent` (WM_NCHITTEST) per il resizing frameless da tutti i lati
  - [ ] Rendere le anteprime (Thumbnail) "responsive" (`setMinimumHeight` e `QSizePolicy`)
  - [ ] Riorganizzare i bottoni principali: Impostazioni - Aggiorna finestre - Cronologia (Orizzontali, parole intere, icone Apple-like)
  - [ ] Adattare `reload_history_tree` per visualizzare Date -> Finestre -> Messaggi
- [ ] Ricompilare l'eseguibile con `PyInstaller --add-data "icon.ico;."`
- [ ] Verifiche finali e Walkthrough
