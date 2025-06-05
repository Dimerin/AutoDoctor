import subprocess
import threading
import vlc
import time
class VoiceAgent:
    def __init__(self, time_window=3):
        # initialize parameters
        self.time_window = time_window # in seconds
        self.binary_path = "../../bin/"
        self.media_path = "../../media/"
        self.command = [self.binary_path + "whisper_stream_win/stream", "-m", self.binary_path + "whisper_stream_win/ggml-model-whisper-base.en.bin", "--length", "3", "--language", "it"]
        # Output list to store transcriptions
        self.transcriptions = []
        # Whisper process
        self._transcription_process = None
        self._stdout_thread = None        # Wait for the thread to finish
        self._lastchecked = 0 # Last checked index for transcriptions
        pass
    
    def _read_stream_output(self, process):
        exclude_keywords = ["audio_sdl_init", "whisper_model_load", "SDL_main"]
        while True:
            line = process.stdout.readline()
            if not line:
                break
            decoded_line = line.decode("utf-8").strip()
            if decoded_line:
                if any(keyword in decoded_line for keyword in exclude_keywords):
                    continue  # Ignora righe di log tecnico
                self.transcriptions.append(decoded_line)
         
    def start(self):
        # Avvia il processo
        if self._transcription_process is not None:
            print("Il processo di riconoscimento vocale è già in esecuzione.")
            return
        self._transcription_process  = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1
        )

        # Thread per leggere l'output in tempo reale
        self._stdout_thread = threading.Thread(target=self._read_stream_output, args=(self._transcription_process,))
        self._stdout_thread.start()
    
    def wait_for_response(self):
        self._lastchecked = 0
        while True:
            # Check only new transcriptions
            new_transcriptions = self.transcriptions[self._lastchecked:]
            for t in new_transcriptions:
                if "yes" in t.lower():
                    return True
                if "no" in t.lower():
                    return False
            self._lastchecked += len(new_transcriptions)
            if self._transcription_process.poll() is not None:
                break
    
    def say_question(self, question):
        
        def play_audio():
            if question == 1:
                player = vlc.MediaPlayer(self.media_path + "How-are-you.mp3")
                player.play()
            time.sleep(5)

        audio_thread = threading.Thread(target=play_audio)
        audio_thread.start()
        audio_thread.join()  # Attende che il thread termini prima di proseguire


    def stop(self):
        # Termina il processo e attende la fine del thread
        if self._transcription_process is None:
            print("Il processo di riconoscimento vocale non è in esecuzione.")
            return
        self._transcription_process.terminate()
