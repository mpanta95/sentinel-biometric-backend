# Sentinel Biometric Backend

Backend Python per il sistema di sicurezza biometrica **Sentinel**.  
Riconoscimento facciale in tempo reale con hot-reload del database residenti.

---

## Deploy su Render (consigliato)

1. Vai su [render.com](https://render.com) e accedi.
2. Clicca **New → Web Service**.
3. Seleziona **Deploy an existing image from a registry** oppure crea un **Public Git Repository** e inserisci l'URL di questo repo.
4. Imposta:
   - **Runtime**: Docker
   - **Plan**: Standard (o Free se disponibile, ma il build di dlib richiede risorse)
5. Clicca **Create Web Service**.
6. Al termine del deploy, copia l'URL pubblico (es. `https://tuo-backend.onrender.com`).

---

## Endpoints

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/analyze` | POST | Riceve un frame JPEG, rileva volti e restituisce `AUTHORIZED` / `UNKNOWN_THREAT` / `IDLE` |
| `/add_resident` | POST | Registra un nuovo residente (nome + foto/video) con hot-reload della cache |
| `/residents` | GET | Restituisce la lista dei residenti registrati |

---

## Configura il frontend

Nelle **Impostazioni** dell'app Sentinel, imposta l'URL backend:

```
https://tuo-backend.onrender.com/analyze
```

---

## Dipendenze principali

- **Flask** + **Flask-CORS**: API HTTP
- **OpenCV**: decodifica frame
- **face_recognition** + **dlib**: encoding biometrici
- **NumPy**: calcolo distanze facciali
- **Gunicorn**: server WSGI per produzione

---

## Note tecniche

- Il database biometrico è in-memory (`_known_encodings`, `_known_names`) con **hot-reload**: quando aggiungi un residente, la cache si aggiorna senza riavvio.
- I file caricati vengono salvati in `./known_faces/`.  
  Su Render il filesystem è **ephemeral**: al riavvio del server i file scompaiono.  
  Per persistenza, considera un mount di **Render Disk** o un bucket S3.
- Il build del container compila `dlib` da sorgente: il primo deploy può richiedere **8-12 minuti**.
