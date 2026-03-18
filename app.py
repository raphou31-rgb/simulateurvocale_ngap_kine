import argparse
import json
import os
import re
from datetime import datetime
from http import HTTPStatus
from pathlib import Path
from urllib import error as urllib_error
from urllib import request as urllib_request
from uuid import uuid4

from flask import Flask, jsonify, request, send_from_directory

from assistant_ngap import decrire_reponse_finale, proposer_choix, traiter_transcription_texte
from ngap_catalog import search_catalog


BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
MAX_AUDIO_UPLOAD_BYTES = 10 * 1024 * 1024
app = Flask(__name__, static_folder=str(STATIC_DIR / "static"), static_url_path="/static")


class TranscriptionError(Exception):
    def __init__(self, message: str, status: HTTPStatus = HTTPStatus.BAD_GATEWAY, code: str = "transcription_error"):
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code


def log_transcription_event(event: str, **payload):
    entry = {
        "event": event,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        **payload,
    }
    print(f"[transcription] {json.dumps(entry, ensure_ascii=False)}")


def guess_audio_filename(content_type: str) -> str:
    normalized = content_type.split(";", 1)[0].strip().lower()
    mapping = {
        "audio/mp4": "dictation.m4a",
        "audio/mpeg": "dictation.mp3",
        "audio/webm": "dictation.webm",
        "audio/ogg": "dictation.ogg",
        "audio/wav": "dictation.wav",
        "audio/x-wav": "dictation.wav",
    }
    return mapping.get(normalized, "dictation.webm")


def encode_multipart_formdata(fields: dict[str, str], file_field: str, filename: str, content_type: str, payload: bytes):
    boundary = f"----ngap-{uuid4().hex}"
    body = bytearray()

    for key, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"))
        body.extend(str(value).encode("utf-8"))
        body.extend(b"\r\n")

    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(
        f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'.encode("utf-8")
    )
    body.extend(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
    body.extend(payload)
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))

    return boundary, bytes(body)


def parse_multipart_formdata(content_type_header: str, raw_body: bytes):
    match = re.search(r'boundary="?([^";]+)"?', content_type_header, re.IGNORECASE)
    if not match:
        raise TranscriptionError("Boundary multipart manquant.", status=HTTPStatus.BAD_REQUEST, code="multipart_boundary_missing")

    boundary = match.group(1).encode("utf-8")
    delimiter = b"--" + boundary
    parts = raw_body.split(delimiter)
    fields: dict[str, str] = {}
    file_part = None

    for part in parts:
        chunk = part.strip()
        if not chunk or chunk == b"--":
            continue
        if chunk.endswith(b"--"):
            chunk = chunk[:-2].rstrip()

        header_blob, separator, body_blob = chunk.partition(b"\r\n\r\n")
        if not separator:
            continue

        headers = {}
        for raw_line in header_blob.decode("utf-8", errors="replace").split("\r\n"):
            if ":" not in raw_line:
                continue
            key, value = raw_line.split(":", 1)
            headers[key.strip().lower()] = value.strip()

        disposition = headers.get("content-disposition", "")
        name_match = re.search(r'name="([^"]+)"', disposition)
        if not name_match:
            continue
        field_name = name_match.group(1)
        filename_match = re.search(r'filename="([^"]*)"', disposition)
        content = body_blob[:-2] if body_blob.endswith(b"\r\n") else body_blob

        if filename_match is not None:
            file_part = {
                "field_name": field_name,
                "filename": filename_match.group(1) or "dictation.bin",
                "content_type": headers.get("content-type", "application/octet-stream"),
                "data": content,
            }
            continue

        fields[field_name] = content.decode("utf-8", errors="replace")

    if not file_part:
        raise TranscriptionError("Fichier audio multipart manquant.", status=HTTPStatus.BAD_REQUEST, code="audio_file_missing")

    return fields, file_part


class OpenAITranscriptionClient:
    def __init__(self, api_key: str, base_url: str, model: str, prompt: str):
        self.api_key = api_key
        self.endpoint = f"{base_url.rstrip('/')}/audio/transcriptions"
        self.model = model
        self.prompt = prompt

    def transcribe(self, audio_bytes: bytes, content_type: str, language: str) -> str:
        filename = guess_audio_filename(content_type)
        log_transcription_event(
            "transcribe_openai_call_started",
            filename=filename,
            content_type=content_type,
            file_size=len(audio_bytes),
            language=language,
            model=self.model,
            endpoint=self.endpoint,
        )
        fields = {
            "model": self.model,
            "language": language,
            "response_format": "json",
        }
        if self.prompt:
            fields["prompt"] = self.prompt

        boundary, body = encode_multipart_formdata(fields, "file", filename, content_type, audio_bytes)
        request = urllib_request.Request(
            self.endpoint,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Accept": "application/json",
            },
        )

        try:
            with urllib_request.urlopen(request, timeout=60) as response:
                raw_response = response.read().decode("utf-8")
        except urllib_error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(details)
                message = payload.get("error", {}).get("message") or payload.get("message") or details
            except json.JSONDecodeError:
                message = details or "Erreur STT distante."
            log_transcription_event(
                "transcribe_openai_call_failed",
                exception_type=type(exc).__name__,
                exception_message=message,
                status_code=getattr(exc, "status", None) or getattr(exc, "code", None),
                model=self.model,
                endpoint=self.endpoint,
            )
            raise TranscriptionError(
                f"Transcription distante refusée: {message}",
                status=HTTPStatus.BAD_GATEWAY,
                code="openai_http_error",
            ) from exc
        except urllib_error.URLError as exc:
            log_transcription_event(
                "transcribe_openai_call_failed",
                exception_type=type(exc).__name__,
                exception_message=str(exc.reason),
                status_code=None,
                model=self.model,
                endpoint=self.endpoint,
            )
            raise TranscriptionError(
                "Service de transcription distant inaccessible.",
                status=HTTPStatus.BAD_GATEWAY,
                code="openai_network_error",
            ) from exc

        try:
            payload = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            log_transcription_event(
                "transcribe_openai_call_failed",
                exception_type=type(exc).__name__,
                exception_message="Réponse JSON invalide du serveur distant.",
                status_code=None,
                model=self.model,
                endpoint=self.endpoint,
            )
            raise TranscriptionError(
                "Réponse STT invalide du serveur distant.",
                status=HTTPStatus.BAD_GATEWAY,
                code="openai_invalid_json",
            ) from exc

        text = str(payload.get("text") or payload.get("transcript") or "").strip()
        if not text:
            log_transcription_event(
                "transcribe_openai_call_failed",
                exception_type="EmptyTranscript",
                exception_message="La transcription serveur est vide.",
                status_code=None,
                model=self.model,
                endpoint=self.endpoint,
            )
            raise TranscriptionError(
                "La transcription serveur est vide.",
                status=HTTPStatus.BAD_GATEWAY,
                code="openai_empty_transcript",
            )
        return text


def build_transcription_client():
    provider = os.environ.get("STT_PROVIDER", "openai").strip().lower()
    if provider != "openai":
        raise TranscriptionError(
            f"Fournisseur STT non pris en charge: {provider}.",
            status=HTTPStatus.SERVICE_UNAVAILABLE,
            code="unsupported_stt_provider",
        )

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise TranscriptionError(
            "Transcription serveur non configurée: OPENAI_API_KEY manquant.",
            status=HTTPStatus.SERVICE_UNAVAILABLE,
            code="missing_openai_api_key",
        )

    return OpenAITranscriptionClient(
        api_key=api_key,
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").strip() or "https://api.openai.com/v1",
        model=os.environ.get("OPENAI_STT_MODEL", "gpt-4o-mini-transcribe").strip() or "gpt-4o-mini-transcribe",
        prompt=os.environ.get("OPENAI_STT_PROMPT", "Transcription médicale en français pour cabinet de kinésithérapie.").strip(),
    )


def run_mode_standard():
    print("Assistant NGAP kiné 2026")
    print("Tapez 'quit' pour arrêter.\n")

    contexte = ""
    attente = ""

    while True:
        message = input("Vous : ")

        if message.lower().strip() == "quit":
            print("Fin de la session.")
            break

        resultat = traiter_transcription_texte(message, contexte, attente)

        print("\nAssistant :")
        print(resultat["texte"])
        print()

        contexte = resultat["nouveau_contexte"]
        attente = resultat["attente"]


def run_mode_recette(log_path: Path):
    print("Mode recette cabinet - NGAP 2026")
    print("Commandes : 'quit' pour quitter, 'reset' pour remettre contexte/attente à vide.\n")
    print(f"Journal recette : {log_path}\n")

    contexte = ""
    attente = ""
    numero_cas = 1

    log_path.parent.mkdir(parents=True, exist_ok=True)

    while True:
        message = input(f"[cas {numero_cas}] Message : ").strip()

        if message.lower() == "quit":
            print("Fin de la recette.")
            break

        if message.lower() == "reset":
            contexte = ""
            attente = ""
            print("Contexte et attente réinitialisés.\n")
            continue

        resultat = traiter_transcription_texte(message, contexte, attente)

        print("\n=== Résultat recette ===")
        print(f"Message saisi : {message}")
        print("Réponse moteur :")
        print(resultat["texte"])
        print(f"Attente : {resultat['attente'] or '(aucune)'}")
        print(f"Contexte : {resultat['nouveau_contexte'] or '(vide)'}")
        print("========================\n")

        entree_log = {
            "horodatage": datetime.now().isoformat(timespec="seconds"),
            "message": message,
            "reponse": resultat["texte"],
            "attente": resultat["attente"],
            "contexte": resultat["nouveau_contexte"],
        }
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entree_log, ensure_ascii=False) + "\n")
        print(f"Cas enregistré dans : {log_path}\n")

        contexte = resultat["nouveau_contexte"]
        attente = resultat["attente"]
        numero_cas += 1


def _json_response(payload: dict, status: HTTPStatus = HTTPStatus.OK):
    response = jsonify(payload)
    response.status_code = int(status)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.get("/manifest.webmanifest")
def manifest():
    return send_from_directory(STATIC_DIR, "manifest.webmanifest")


@app.get("/service-worker.js")
def service_worker():
    return send_from_directory(STATIC_DIR, "service-worker.js")


@app.get("/favicon.ico")
def favicon():
    return send_from_directory(STATIC_DIR, "favicon.ico")


@app.post("/api/analyze")
def analyze_api():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _json_response({"error": "JSON invalide."}, status=HTTPStatus.BAD_REQUEST)

    message = str(payload.get("message", "")).strip()
    contexte = str(payload.get("context", "")).strip()
    attente = str(payload.get("attente", "")).strip()

    if not message:
        return _json_response({"error": "Le message est obligatoire."}, status=HTTPStatus.BAD_REQUEST)

    if len(message.encode("utf-8")) > 32_000:
        return _json_response({"error": "Taille de requête invalide."}, status=HTTPStatus.BAD_REQUEST)

    resultat = traiter_transcription_texte(message, contexte, attente)
    choices = proposer_choix(message, contexte, resultat["attente"])
    catalog_matches = [
        {
            "id": item["ID"],
            "libelle": item["libelle"].strip(),
            "theme": item.get("theme", "").strip(),
            "cotation": item["cotation"],
        }
        for item in search_catalog(message)
    ]
    result_meta = None
    if resultat["termine"]:
        result_meta = decrire_reponse_finale(resultat["texte"], message, contexte)

    return _json_response(
        {
            "answer": resultat["texte"],
            "context": resultat["nouveau_contexte"],
            "attente": resultat["attente"],
            "done": resultat["termine"],
            "choices": choices,
            "catalog_matches": catalog_matches,
            "result_meta": result_meta,
        }
    )


@app.post("/api/transcribe")
def transcribe_api():
    content_length = request.content_length or 0
    if content_length <= 0 or content_length > MAX_AUDIO_UPLOAD_BYTES:
        log_transcription_event(
            "transcribe_request_validation_failed",
            reason="invalid_content_length",
            content_length=content_length,
            max_audio_upload_bytes=MAX_AUDIO_UPLOAD_BYTES,
            user_agent=request.headers.get("User-Agent", ""),
        )
        return _json_response(
            {"error": "Taille audio invalide.", "error_code": "invalid_content_length"},
            status=HTTPStatus.BAD_REQUEST,
        )

    request_content_type = request.headers.get("Content-Type", "application/octet-stream").strip()
    language = "fr-FR"
    selected_mime_type = ""
    tested_mime_types = []
    recording_duration_ms = 0
    audio_filename = "dictation.bin"

    if request.files:
        uploaded_file = request.files.get("audio")
        if uploaded_file is None:
            log_transcription_event(
                "transcribe_request_validation_failed",
                reason="audio_file_missing",
                content_type=request_content_type,
                user_agent=request.headers.get("User-Agent", ""),
            )
            return _json_response(
                {"error": "Fichier audio multipart manquant.", "error_code": "audio_file_missing"},
                status=HTTPStatus.BAD_REQUEST,
            )

        audio_bytes = uploaded_file.read()
        content_type = (uploaded_file.mimetype or "application/octet-stream").split(";", 1)[0].strip().lower()
        audio_filename = uploaded_file.filename or "dictation.bin"
        language = str(request.form.get("language", "fr-FR")).strip() or "fr-FR"
        selected_mime_type = str(request.form.get("selected_mime_type", "")).strip()
        try:
            recording_duration_ms = int(str(request.form.get("recording_duration_ms", "0")).strip() or "0")
        except ValueError:
            recording_duration_ms = 0
        try:
            tested_mime_types = json.loads(request.form.get("tested_mime_types", "[]"))
        except json.JSONDecodeError:
            tested_mime_types = []
    else:
        audio_bytes = request.get_data(cache=False)
        if not audio_bytes:
            log_transcription_event(
                "transcribe_request_validation_failed",
                reason="empty_request_body",
                content_type=request_content_type,
                user_agent=request.headers.get("User-Agent", ""),
            )
            return _json_response(
                {"error": "Aucune donnée audio reçue.", "error_code": "empty_request_body"},
                status=HTTPStatus.BAD_REQUEST,
            )
        content_type = request_content_type.split(";", 1)[0].strip().lower()
        language = request.headers.get("X-Audio-Language", "fr-FR").strip() or "fr-FR"

    if not content_type.startswith("audio/") and content_type != "application/octet-stream":
        log_transcription_event(
            "transcribe_request_validation_failed",
            reason="unsupported_content_type",
            filename=audio_filename,
            content_type=content_type,
            file_size=len(audio_bytes),
            selected_mime_type=selected_mime_type,
            recording_duration_ms=recording_duration_ms,
            user_agent=request.headers.get("User-Agent", ""),
        )
        return _json_response(
            {"error": "Format audio non reconnu.", "error_code": "unsupported_content_type"},
            status=HTTPStatus.BAD_REQUEST,
        )

    if not audio_bytes:
        log_transcription_event(
            "transcribe_request_validation_failed",
            reason="empty_audio_file",
            filename=audio_filename,
            content_type=content_type,
            file_size=0,
            selected_mime_type=selected_mime_type,
            recording_duration_ms=recording_duration_ms,
            user_agent=request.headers.get("User-Agent", ""),
        )
        return _json_response(
            {"error": "Fichier audio vide.", "error_code": "empty_audio_file"},
            status=HTTPStatus.BAD_REQUEST,
        )

    if recording_duration_ms and recording_duration_ms < 500:
        log_transcription_event(
            "transcribe_request_validation_failed",
            reason="audio_too_short",
            filename=audio_filename,
            content_type=content_type,
            file_size=len(audio_bytes),
            selected_mime_type=selected_mime_type,
            recording_duration_ms=recording_duration_ms,
            user_agent=request.headers.get("User-Agent", ""),
        )
        return _json_response(
            {"error": "Audio trop court pour une transcription fiable.", "error_code": "audio_too_short"},
            status=HTTPStatus.BAD_REQUEST,
        )

    log_transcription_event(
        "transcribe_request_received",
        content_type=content_type,
        selected_mime_type=selected_mime_type,
        tested_mime_types=tested_mime_types,
        file_size=len(audio_bytes),
        filename=audio_filename,
        recording_duration_ms=recording_duration_ms,
        language=language,
        user_agent=request.headers.get("User-Agent", ""),
        multipart_field_name="audio" if request.files else "",
    )

    try:
        client = build_transcription_client()
        transcript = client.transcribe(audio_bytes, content_type, language.split("-", 1)[0].lower())
    except TranscriptionError as exc:
        log_transcription_event(
            "transcribe_openai_call_failed",
            filename=audio_filename,
            content_type=content_type,
            file_size=len(audio_bytes),
            selected_mime_type=selected_mime_type,
            recording_duration_ms=recording_duration_ms,
            user_agent=request.headers.get("User-Agent", ""),
            exception_type=type(exc).__name__,
            exception_message=exc.message,
            status_code=int(exc.status),
            error_code=exc.code,
        )
        return _json_response(
            {"error": exc.message, "error_code": exc.code},
            status=exc.status,
        )
    except Exception as exc:
        log_transcription_event(
            "transcribe_openai_call_failed",
            filename=audio_filename,
            content_type=content_type,
            file_size=len(audio_bytes),
            selected_mime_type=selected_mime_type,
            recording_duration_ms=recording_duration_ms,
            user_agent=request.headers.get("User-Agent", ""),
            exception_type=type(exc).__name__,
            exception_message=str(exc),
            status_code=int(HTTPStatus.INTERNAL_SERVER_ERROR),
            error_code="internal_transcription_error",
        )
        return _json_response(
            {"error": "Erreur interne pendant la transcription audio.", "error_code": "internal_transcription_error"},
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    log_transcription_event(
        "transcribe_request_succeeded",
        content_type=content_type,
        file_size=len(audio_bytes),
        transcript_length=len(transcript),
        language=language,
    )

    return _json_response(
        {
            "text": transcript,
            "language": language,
            "provider": os.environ.get("STT_PROVIDER", "openai").strip().lower() or "openai",
            "content_type": content_type,
            "selected_mime_type": selected_mime_type,
            "recording_duration_ms": recording_duration_ms,
        }
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["standard", "recette", "web"],
        default="web",
        help="Mode d'exécution local.",
    )
    parser.add_argument(
        "--recette-log",
        default="logs/recette_cabinet.jsonl",
        help="Fichier journal utilisé en mode recette (format jsonl).",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("HOST", "127.0.0.1"),
        help="Adresse d'écoute du serveur web.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", "8000")),
        help="Port du serveur web.",
    )
    args = parser.parse_args()

    if args.mode == "recette":
        run_mode_recette(Path(args.recette_log))
        return

    if args.mode == "standard":
        run_mode_standard()
        return

    print(f"Assistant NGAP web disponible sur http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
