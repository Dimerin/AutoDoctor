from VoiceAgent import VoiceAgent

def transcription_test():
    # Crea un'istanza di VoiceRecognition
    voice_recognition = VoiceAgent(time_window=3)

    while True:
        scelta = input("Inserisci 1 per avviare il riconoscimento, 2 per fermarlo: ")
        if scelta == "1":
            voice_recognition.start()
        elif scelta == "2":
            voice_recognition.stop()
            break
        else:
            print("Scelta non valida. Riprova.")

def recgnition_test():
    # Crea un'istanza di VoiceRecognition
    voice_recognition = VoiceAgent(time_window=3)

    # Avvia il riconoscimento vocale
    voice_recognition.start()

    # Attendi una risposta
    response = voice_recognition.wait_for_response()
    if response:
        print("Riconosciuto: Sì")
        voice_recognition.stop()
    else:
        print("Riconosciuto: No")
        voice_recognition.stop()

def play_test():
        # Crea un'istanza di VoiceRecognition
    voice_recognition = VoiceAgent(time_window=3)

    # Avvia il riconoscimento vocale
    voice_recognition.say_question(1)

if __name__ == "__main__":
    play_test()
