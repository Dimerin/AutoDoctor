from voice_agent import VoiceAgent


if __name__ == "__main__":
    voicea = VoiceAgent("http://localhost:8080/inference")
    voicea.start_protocol(duration=5)
