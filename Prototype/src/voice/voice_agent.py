import sounddevice as sd
import vlc
import time
import requests
from scipy.io.wavfile import write
import uuid
from pathlib import Path
import threading
import queue

class VoiceAgent:
    def __init__(self, server_url = None, sample_rate=16000):
        self.sample_rate = sample_rate
        self.tmp_dir = Path("tmp")
        self.tmp_dir.mkdir(exist_ok=True)
        self.media_path = Path("../media")  # Assuming media files are stored in a 'media' directory
        self.server_url = server_url

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
    
    def _play_audio(self, file_name, sleep_time):
        file_path = self.media_path / file_name
        if not file_path.is_file():
            raise FileNotFoundError(f"Il file '{file_path}' non esiste.")
        
        print(f"[INFO] Riproduzione dell'audio '{file_path.name}'...")
        player = vlc.MediaPlayer(str(file_path))
        player.play()
        #print(f"[INFO] Attesa di {sleep_time:.2f} secondi per la riproduzione...")
        time.sleep(sleep_time)

    def _reproduce_question(self, question):           
        def play_audio():
            if question == 1:
                self._play_audio("Can you hear me .mp3", 1.6)  
            elif question == 2:
                self._play_audio("Can you open your ey.mp3", 2.6)
            elif question == 3:
                self._play_audio("Can you move your ey.mp3", 2.6)
            else:
                print("[ERRORE] Domanda non riconosciuta.")
                return
            self._play_audio("beep.mp3", 0.1)

        audio_thread = threading.Thread(target=play_audio)
        audio_thread.start()
        audio_thread.join()  # Attende che il thread termini prima di proseguire
    
    def _process_text(self, text):
        text = text.lower().strip()
        if any(word in text for word in ["sì", "si", "yes", "yep", "yeah"]):
            print("[INFO] L'utente ha risposto: SÌ")
            return "Yes"
        elif any(word in text for word in ["no", "nope", "nah"]):
            print("[INFO] L'utente ha risposto: NO")
            return "No"
        else:
            print("[INFO] Risposta non riconosciuta come sì o no.")
            return "Unknown"

    def send_and_process(self, file, results_queue, whisper_time_queue):
        # TIME TRACKING
        starting_time = time.time()
        # END TIME TRACKING
        try:
            testo = self._send_audio(file)
        except Exception as e:
            print(f"[ERRORE] Si è verificato un errore durante l'invio del file: {e}")
            results_queue.put("-1")
            return
        if testo:
            print(f"[INFO] Risultato della trascrizione: {testo}")
        else:
            print("[ERRORE] Trascrizione fallita.")
            results_queue.put("-3")
            return
        print("[INFO] Start processing...")
        result = self._process_text(testo)
        results_queue.put(result)
        # TIME TRACKING
        whisper_time_queue.put(time.time() - starting_time)
        # END TIME TRACKING
    
    def start_protocol(self, server_url = None, duration=3):
        if server_url is not None:
            self.server_url = server_url
        elif self.server_url is None and server_url is None:
            raise ValueError("Server URL must be provided or set in the constructor.")
        user_responses = []
        threads = []
        user_times = []
        print("[INFO] Avvio del protocollo di registrazione e trascrizione...")
        print("[INFO] Asking the user to speak...")
        for i in range(1, 4):
            start_user_time = time.time()
            self._reproduce_question(i)
            file = self._record_audio(duration)
            user_times.append(time.time() - start_user_time)
            # Usa una coda thread-safe per raccogliere i risultati dalle thread
            if 'results_queue' not in locals():
                results_queue = queue.Queue()
            # TIME TRACKING
            if 'whisper_time_queue' not in locals():
                whisper_time_queue = queue.Queue()
            # END TIME TRACKING
            thread = threading.Thread(target=self.send_and_process, args=(file, results_queue, whisper_time_queue))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        # Raccogli i risultati dalla coda
        while not results_queue.empty():
            user_responses.append(results_queue.get())
        # TIME TRACKING
        time_per_question = []
        while not whisper_time_queue.empty():
            time_per_question.append(whisper_time_queue.get())
        # END TIME TRACKING
        print("[INFO] Protocollo completato.")
        print("[INFO] Risposte dell'utente:", user_responses)
        return user_responses, time_per_question, user_times