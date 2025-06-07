import sounddevice as sd
import vlc
import time
import requests
from scipy.io.wavfile import write
import uuid
from pathlib import Path
import threading

class VoiceAgent:
    def __init__(self,  sample_rate=16000):
        self.sample_rate = sample_rate
        self.tmp_dir = Path("tmp")
        self.tmp_dir.mkdir(exist_ok=True)
        self.media_path = Path("../media")  # Assuming media files are stored in a 'media' directory

    def _genera_nome_file(self):
        return self.tmp_dir / f"{uuid.uuid4().hex}.wav"

    def _record_audio(self, durata_sec=5):
        output_file = self._genera_nome_file()
        print(f"[INFO] Inizio registrazione per {durata_sec} secondi...")
        audio = sd.rec(int(durata_sec * self.sample_rate), samplerate=self.sample_rate, channels=1, dtype='int16')
        sd.wait()
        write(str(output_file), self.sample_rate, audio)
        print(f"[INFO] Audio salvato in '{output_file}'")
        return output_file

    def _send_audio(self, file_path, extra_params=None):
        if not file_path.is_file():
            raise FileNotFoundError(f"Il file '{file_path}' non esiste.")

        print(f"[INFO] Invio del file '{file_path.name}' al server whisper.cpp...")
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    self.server_url,
                    files=files, 
                    data=extra_params)

            if response.status_code == 200:
                result = response.json()
                testo = result.get("text", "")
                print("[INFO] Trascrizione completata:")
                print(testo or "(nessun testo)")
                return testo
            else:
                print(f"[ERRORE] Risposta HTTP {response.status_code}")
                print(response.text)
                return None
        finally:
            # Pulizia file temporaneo
            try:
                file_path.unlink()
                print(f"[INFO] File temporaneo '{file_path.name}' eliminato.")
            except Exception as e:
                print(f"[WARN] Impossibile eliminare il file temporaneo: {e}")
    
    def _reproduce_question(self, question):           
        def play_audio():
            if question == 1:
                player = vlc.MediaPlayer(str(self.media_path / "How-are-you.mp3"))
                player.play()
            time.sleep(2)  # Attendi che l'audio inizi a riprodursi

        audio_thread = threading.Thread(target=play_audio)
        audio_thread.start()
        audio_thread.join()  # Attende che il thread termini prima di proseguire
    
    def _process_text(self, text):
        text = text.lower().strip()
        if any(word in text for word in ["sì", "si", "yes", "yep", "yeah"]):
            print("[INFO] L'utente ha risposto: SÌ")
            return 1
        elif any(word in text for word in ["no", "nope", "nah"]):
            print("[INFO] L'utente ha risposto: NO")
            return 0
        else:
            print("[INFO] Risposta non riconosciuta come sì o no.")
            return -1

    def start_protocol(self, server_url, duration=5):
        self.server_url = server_url
        print("[INFO] Avvio del protocollo di registrazione e trascrizione...")
        print("[INFO] Asking the user to speak...")
        self._reproduce_question(1)
        print("[INFO] Start recording and transcription...")
        file = self._record_audio(duration)
        try:
            testo = self._send_audio(file)
        except Exception as e:
            print(f"[ERRORE] Si è verificato un errore durante l'invio del file: {e}")
            return -2
        if testo:
            print(f"[INFO] Risultato della trascrizione: {testo}")
        else:
            print("[ERRORE] Trascrizione fallita.")
            return -3
        print("[INFO] Start processing...")
        result = self._process_text(testo)
        print("[INFO] Protocollo completato.")
        return result