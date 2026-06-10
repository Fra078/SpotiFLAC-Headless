# SpotiFLAC Headless: Funzioni Supportate e Mappatura Endpoint

Questo documento descrive la mappatura tra le funzioni originali della GUI (basata su `pywebview` in `SpotiFLAC/app.py`) e i nuovi endpoint della versione headless sviluppata con **FastAPI**.

---

## 1. Mappatura delle Funzioni e degli Endpoint API

| Metodo Python Originale (`SpotiFLAC_API`) | Funzione / Caratteristica GUI | Endpoint FastAPI | Metodo HTTP | Stato Migrazione | Note / Dettagli |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `get_version()` | Recupero della versione dell'app | `/api/status/version` | `GET` | **Mappato** | Restituisce la versione letta da `pyproject.toml` o dai metadati. |
| `get_ffmpeg_status()` | Controllo della presenza di `ffmpeg` | `/api/status/ffmpeg` | `GET` | **Mappato** | Verifica la disponibilità del binario ffmpeg nel path locale. |
| `get_network_status()` | Rilevamento IP pubblico e nazione | `/api/status/network` | `GET` | **Mappato** | Ottiene dettagli IP tramite geolocalizzazione esterna. |
| `run_health_check()` | Verifica stato dei provider di rete | `/api/status/health` | `GET` | **Mappato** | Interroga le API Zarz e singoli endpoint di streaming. |
| `check_qobuz_api()` / `check_tidal_api()` | Validazione URL endpoint custom | `/api/status/check_endpoint` | `GET` | **Mappato** | Utile per validare connessioni api a endpoint alternativi. |
| `load_settings()` | Lettura delle impostazioni globali | `/api/settings` | `GET` | **Mappato** | Carica la configurazione del file JSON in Pydantic. |
| `save_settings()` | Salvataggio delle impostazioni globali | `/api/settings` | `POST` | **Mappato** | Salva e valida la configurazione dell'utente. |
| `get_profiles()` | Elenco dei profili di download | `/api/settings/profiles` | `GET` | **Mappato** | Ritorna i profili di download disponibili. |
| `load_profile_data(name)` | Caricamento di un profilo specifico | `/api/settings/profiles/{name}` | `GET` | **Mappato** | Ritorna le impostazioni per un singolo profilo. |
| `save_profile_data(name, cfg)` | Salvataggio/Aggiornamento profilo | `/api/settings/profiles/{name}` | `POST` | **Mappato** | Crea o aggiorna un profilo con validazione DTO. |
| `delete_profile_data(name)` | Eliminazione profilo salvato | `/api/settings/profiles/{name}` | `DELETE` | **Mappato** | Cancella il file del profilo. |
| `get_history()` | Ottieni cronologia degli URL inseriti | `/api/history` | `GET` | **Mappato** | Mostra fino a 20 URL cercati o scaricati di recente. |
| `remove_history_item(url)` | Rimuove un URL dalla cronologia | `/api/history/item` | `DELETE` | **Mappato** | Cancella l'URL specificato nei parametri query. |
| `search_provider(...)` | Ricerca album/tracce su Spotify | `/api/search` | `GET` | **Mappato** | Esegue query catalogo di metadati. |
| `download_tracks(...)` | Avvio download di tracce/album/playlist | `/api/download` | `POST` | **Mappato** | Avvia il download in background asincrono per un URL. |
| `_download_stats_monitor()` | Aggiornamento statistiche e file completati | `/api/download/stats` | `GET` | **Mappato** | Rileva live progress, velocità, coda e gli ultimi 20 file scaricati. |
| `_download_stats_monitor()` | Stream push statistiche in tempo reale | `/api/download/ws` | `WS` | **Mappato** | Invia aggiornamenti in tempo reale su coda di download e file scaricati. |
| - | Reset della coda e pulizia statistiche | `/api/download/reset` | `POST` | **Mappato** | Svuota la coda corrente nel `DownloadManager`. |
| `search_code(query, path, limit)` | Ricerca all'interno del codice sorgente | - | - | **Non Mappato** | Funzione di sviluppo locale non necessaria in produzione server. |
| `download_track_lyrics(...)` | Scarica lyrics di una singola traccia | - | - | **Disponibile nel core** | Integrato implicitamente in `/api/download` se `embed_lyrics` è True. |
| `download_track_cover(...)` | Scarica copertina singola traccia | - | - | **Disponibile nel core** | Integrato implicitamente in `/api/download` o recuperabile da `/api/search`. |
| `download_all_covers(...)` | Scarica copertine di tutte le tracce | - | - | **Disponibile nel core** | Gestito nativamente dal downloader durante il processo di download. |
| `download_all_lyrics(...)` | Scarica l'archivio lyrics di tutte le tracce | - | - | **Disponibile nel core** | Gestito nativamente dal downloader durante il processo di download. |

---

## 2. Funzioni Obsolete o Non Applicabili per l'ambiente Headless

Le seguenti funzioni originarie di `SpotiFLAC_API` erano specifiche per la gestione della GUI desktop tramite `pywebview` e sono state intenzionalmente escluse dagli endpoint API in quanto prive di senso in un ambiente headless (CLI/Server):

- **Interazione Finestra Desktop (OS native)**:
  - `WindowMinimise()`: Riduce a icona la finestra.
  - `WindowToggleMaximise()`: Ingrandisce o ripristina la finestra.
  - `Quit()`: Chiude l'applicazione.
- **Selettori OS e Apertura Link Browser**:
  - `choose_folder()`: Apre il selettore cartelle di sistema (sostituito dal parametro `output_dir` configurabile via API).
  - `open_config_folder()`: Apre il file explorer sulla cartella delle impostazioni.
  - `open_url(url)`: Apre un URL nel browser predefinito locale.
- **Callback grafici**:
  - `log(message, type)`: Scrittura diretta dei log nella console JS della GUI (sostituita da logging di FastAPI/Uvicorn standard).
  - `set_progress(label)` / `set_metadata(...)`: Callback javascript di aggiornamento immediato della UI (sostituiti dal monitoraggio poll/GET su `/api/download/stats`).
