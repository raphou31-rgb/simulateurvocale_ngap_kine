import argparse
import errno
import json
import os
import re
from datetime import datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import error as urllib_error
from urllib import request as urllib_request
from uuid import uuid4

from assistant_ngap import decrire_reponse_finale, proposer_choix, traiter_transcription_texte
from ngap_catalog import search_catalog


BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
MAX_AUDIO_UPLOAD_BYTES = 10 * 1024 * 1024


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


class NGAPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_POST(self):
        if self.path == "/api/analyze":
            self._handle_analyze()
            return

        if self.path == "/api/transcribe":
            self._handle_transcribe()
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")

    def _handle_analyze(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0 or content_length > 32_000:
            self._send_json({"error": "Taille de requête invalide."}, status=HTTPStatus.BAD_REQUEST)
            return

        try:
            raw_body = self.rfile.read(content_length)
            payload = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json({"error": "JSON invalide."}, status=HTTPStatus.BAD_REQUEST)
            return

        message = str(payload.get("message", "")).strip()
        contexte = str(payload.get("context", "")).strip()
        attente = str(payload.get("attente", "")).strip()

        if not message:
            self._send_json({"error": "Le message est obligatoire."}, status=HTTPStatus.BAD_REQUEST)
            return

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

        self._send_json(
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

    def _handle_transcribe(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0 or content_length > MAX_AUDIO_UPLOAD_BYTES:
            log_transcription_event(
                "transcribe_request_validation_failed",
                reason="invalid_content_length",
                content_length=content_length,
                max_audio_upload_bytes=MAX_AUDIO_UPLOAD_BYTES,
                user_agent=self.headers.get("User-Agent", ""),
            )
            self._send_json(
                {"error": "Taille audio invalide.", "error_code": "invalid_content_length"},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        request_content_type = self.headers.get("Content-Type", "application/octet-stream").strip()
        raw_body = self.rfile.read(content_length)
        if not raw_body:
            log_transcription_event(
                "transcribe_request_validation_failed",
                reason="empty_request_body",
                content_type=request_content_type,
                user_agent=self.headers.get("User-Agent", ""),
            )
            self._send_json(
                {"error": "Aucune donnée audio reçue.", "error_code": "empty_request_body"},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        language = "fr-FR"
        selected_mime_type = ""
        tested_mime_types = []
        recording_duration_ms = 0
        audio_filename = "dictation.bin"

        if request_content_type.lower().startswith("multipart/form-data"):
            try:
                fields, file_part = parse_multipart_formdata(request_content_type, raw_body)
            except TranscriptionError as exc:
                log_transcription_event(
                    "transcribe_request_validation_failed",
                    reason=exc.code,
                    content_type=request_content_type,
                    user_agent=self.headers.get("User-Agent", ""),
                    exception_type=type(exc).__name__,
                    exception_message=exc.message,
                    status_code=int(exc.status),
                )
                self._send_json({"error": exc.message, "error_code": exc.code}, status=exc.status)
                return
            audio_bytes = file_part["data"]
            content_type = file_part["content_type"].split(";", 1)[0].strip().lower()
            audio_filename = file_part["filename"]
            language = str(fields.get("language", "fr-FR")).strip() or "fr-FR"
            selected_mime_type = str(fields.get("selected_mime_type", "")).strip()
            try:
                recording_duration_ms = int(str(fields.get("recording_duration_ms", "0")).strip() or "0")
            except ValueError:
                recording_duration_ms = 0
            try:
                tested_mime_types = json.loads(fields.get("tested_mime_types", "[]"))
            except json.JSONDecodeError:
                tested_mime_types = []
        else:
            content_type = request_content_type.split(";", 1)[0].strip().lower()
            audio_bytes = raw_body
            language = self.headers.get("X-Audio-Language", "fr-FR").strip() or "fr-FR"

        if not content_type.startswith("audio/") and content_type != "application/octet-stream":
            log_transcription_event(
                "transcribe_request_validation_failed",
                reason="unsupported_content_type",
                filename=audio_filename,
                content_type=content_type,
                file_size=len(audio_bytes),
                selected_mime_type=selected_mime_type,
                recording_duration_ms=recording_duration_ms,
                user_agent=self.headers.get("User-Agent", ""),
            )
            self._send_json(
                {"error": "Format audio non reconnu.", "error_code": "unsupported_content_type"},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        if not audio_bytes:
            log_transcription_event(
                "transcribe_request_validation_failed",
                reason="empty_audio_file",
                filename=audio_filename,
                content_type=content_type,
                file_size=0,
                selected_mime_type=selected_mime_type,
                recording_duration_ms=recording_duration_ms,
                user_agent=self.headers.get("User-Agent", ""),
            )
            self._send_json(
                {"error": "Fichier audio vide.", "error_code": "empty_audio_file"},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        if recording_duration_ms and recording_duration_ms < 500:
            log_transcription_event(
                "transcribe_request_validation_failed",
                reason="audio_too_short",
                filename=audio_filename,
                content_type=content_type,
                file_size=len(audio_bytes),
                selected_mime_type=selected_mime_type,
                recording_duration_ms=recording_duration_ms,
                user_agent=self.headers.get("User-Agent", ""),
            )
            self._send_json(
                {"error": "Audio trop court pour une transcription fiable.", "error_code": "audio_too_short"},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        log_transcription_event(
            "transcribe_request_received",
            content_type=content_type,
            selected_mime_type=selected_mime_type,
            tested_mime_types=tested_mime_types,
            file_size=len(audio_bytes),
            filename=audio_filename,
            recording_duration_ms=recording_duration_ms,
            language=language,
            user_agent=self.headers.get("User-Agent", ""),
            multipart_field_name="audio" if request_content_type.lower().startswith("multipart/form-data") else "",
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
                user_agent=self.headers.get("User-Agent", ""),
                exception_type=type(exc).__name__,
                exception_message=exc.message,
                status_code=int(exc.status),
                error_code=exc.code,
            )
            self._send_json(
                {"error": exc.message, "error_code": exc.code},
                status=exc.status,
            )
            return
        except Exception as exc:
            log_transcription_event(
                "transcribe_openai_call_failed",
                filename=audio_filename,
                content_type=content_type,
                file_size=len(audio_bytes),
                selected_mime_type=selected_mime_type,
                recording_duration_ms=recording_duration_ms,
                user_agent=self.headers.get("User-Agent", ""),
                exception_type=type(exc).__name__,
                exception_message=str(exc),
                status_code=int(HTTPStatus.INTERNAL_SERVER_ERROR),
                error_code="internal_transcription_error",
            )
            self._send_json(
                {"error": "Erreur interne pendant la transcription audio.", "error_code": "internal_transcription_error"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
            return

        log_transcription_event(
            "transcribe_request_succeeded",
            content_type=content_type,
            file_size=len(audio_bytes),
            transcript_length=len(transcript),
            language=language,
        )

        self._send_json(
            {
                "text": transcript,
                "language": language,
                "provider": os.environ.get("STT_PROVIDER", "openai").strip().lower() or "openai",
                "content_type": content_type,
                "selected_mime_type": selected_mime_type,
                "recording_duration_ms": recording_duration_ms,
            }
        )

    def do_GET(self):
        if self.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def log_message(self, format, *args):
        return

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def run_web_server(host: str, port: int):
    server = None
    selected_port = port

    for candidate_port in range(port, port + 10):
        try:
            server = ThreadingHTTPServer((host, candidate_port), NGAPRequestHandler)
            selected_port = candidate_port
            break
        except OSError as exc:
            if exc.errno != errno.EADDRINUSE:
                raise

    if server is None:
        raise OSError(errno.EADDRINUSE, f"Aucun port libre trouvé entre {port} et {port + 9}")

    print(f"Assistant NGAP web disponible sur http://{host}:{selected_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServeur arrêté.")
    finally:
        server.server_close()


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

    run_web_server(args.host, args.port)


if __name__ == "__main__":
    main()
