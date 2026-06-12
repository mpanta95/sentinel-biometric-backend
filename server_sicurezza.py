import cv2
import face_recognition
import os
import time
import threading
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # Permette la comunicazione con il frontend Lovable

KNOWN_FACES_DIR = "known_faces"
ALLOWED_EXT = {"jpg", "jpeg", "png", "mp4", "webm", "mov"}

if not os.path.exists(KNOWN_FACES_DIR):
    os.makedirs(KNOWN_FACES_DIR)

# Cache in memoria dei volti noti (ricaricata a caldo)
_known_encodings = []
_known_names = []
_cache_lock = threading.Lock()


def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def _encode_image_file(path: str):
    image = face_recognition.load_image_file(path)
    encodings = face_recognition.face_encodings(image)
    return encodings[0] if encodings else None


def _encode_video_file(path: str, max_frames: int = 30):
    """Estrae il primo volto riconoscibile da un breve video."""
    cap = cv2.VideoCapture(path)
    encoding = None
    frames_checked = 0
    while cap.isOpened() and frames_checked < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        frames_checked += 1
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        encs = face_recognition.face_encodings(rgb)
        if encs:
            encoding = encs[0]
            break
    cap.release()
    return encoding


def reload_known_faces():
    """Ricarica in memoria tutti i volti dalla cartella known_faces. Hot-reload."""
    encodings = []
    names = []
    for file in sorted(os.listdir(KNOWN_FACES_DIR)):
        path = os.path.join(KNOWN_FACES_DIR, file)
        if not os.path.isfile(path):
            continue
        ext = file.rsplit(".", 1)[-1].lower() if "." in file else ""
        try:
            if ext in {"jpg", "jpeg", "png"}:
                enc = _encode_image_file(path)
            elif ext in {"mp4", "webm", "mov"}:
                enc = _encode_video_file(path)
            else:
                continue
            if enc is not None:
                encodings.append(enc)
                names.append(os.path.splitext(file)[0].split("_")[0])
        except Exception as e:
            print(f"[WARN] Impossibile processare {file}: {e}")
    with _cache_lock:
        global _known_encodings, _known_names
        _known_encodings = encodings
        _known_names = names
    print(f"[INFO] Database biometrico ricaricato: {len(names)} identità")
    return names


# Bootstrap iniziale
reload_known_faces()


@app.route("/add_resident", methods=["POST"])
def add_resident():
    """Riceve nome + file (immagine o video) dal frontend, salva su disco
    e ricarica IN TEMPO REALE la cache dei volti noti senza riavvio."""
    if "file" not in request.files or "name" not in request.form:
        return jsonify({"success": False, "error": "Dati mancanti (file + name richiesti)"}), 400

    file = request.files["file"]
    name = request.form["name"].strip()

    if not name:
        return jsonify({"success": False, "error": "Nome non valido"}), 400
    if file.filename == "" or not _allowed(file.filename):
        return jsonify({"success": False, "error": "File non supportato"}), 400

    ext = file.filename.rsplit(".", 1)[1].lower()
    safe_name = secure_filename(name.lower().replace(" ", "_"))
    filename = f"{safe_name}_{int(time.time())}.{ext}"
    save_path = os.path.join(KNOWN_FACES_DIR, filename)
    file.save(save_path)

    # Hot-reload: aggiorna la cache senza riavviare il server
    loaded = reload_known_faces()

    return jsonify({
        "success": True,
        "message": f"Residente '{name}' registrato nel database biometrico",
        "filename": filename,
        "total_identities": len(loaded),
    })


@app.route("/residents", methods=["GET"])
def residents():
    with _cache_lock:
        return jsonify({"success": True, "residents": list(set(_known_names))})


@app.route("/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "Nessun frame ricevuto"}), 400

    file = request.files["file"]
    np_img = np.frombuffer(file.read(), np.uint8)
    frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    if not face_locations:
        return jsonify({"success": True, "face_detected": False, "status": "IDLE"})

    with _cache_lock:
        known_encodings = list(_known_encodings)
        known_names = list(_known_names)

    for face_encoding in face_encodings:
        if not known_encodings:
            return jsonify({"success": True, "face_detected": True, "status": "UNKNOWN_THREAT", "person_name": ""})

        matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
        face_distances = face_recognition.face_distance(known_encodings, face_encoding)
        best_match_index = int(np.argmin(face_distances)) if len(face_distances) > 0 else None

        if best_match_index is not None and matches[best_match_index]:
            name = known_names[best_match_index]
            confidence = float(1 - face_distances[best_match_index])
            return jsonify({"success": True, "face_detected": True, "status": "AUTHORIZED", "person_name": name, "confidence": confidence})

    return jsonify({"success": True, "face_detected": True, "status": "UNKNOWN_THREAT", "person_name": ""})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
