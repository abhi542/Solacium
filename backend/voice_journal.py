import sys
import os
import json
import wave

try:
    import audioop
except ImportError:
    try:
        import audioop_lts as audioop
        sys.modules["audioop"] = audioop
    except ImportError:
        pass

from vosk import Model, KaldiRecognizer
from dotenv import load_dotenv

load_dotenv()

class VoiceJournal:
    def __init__(self, model_path: str = None):
        self.model_path = model_path or os.getenv("VOSK_MODEL_PATH")
        if not self.model_path or not os.path.exists(self.model_path):
            print(f"Warning: Vosk model not found at {self.model_path}. STT will be unavailable.")
            self.model = None
        else:
            self.model = Model(self.model_path)

    def transcribe_audio(self, audio_file_path: str) -> str:
        """Transcribes an audio file (WAV format) using Vosk and SoundFile."""
        if not self.model:
            return "STT Error: Model not loaded."

        try:
            import soundfile as sf
            import numpy as np
            
            # Read with soundfile (handles WAV format properly)
            data, samplerate = sf.read(audio_file_path)
            
            # Convert float data to 16-bit PCM (int16) which Vosk requires
            audio_int16 = (data * 32767).astype(np.int16)
            
            rec = KaldiRecognizer(self.model, samplerate)
            rec.SetWords(True)

            # Accept the entire waveform
            if rec.AcceptWaveform(audio_int16.tobytes()):
                result_json = json.loads(rec.Result())
                text = result_json.get("text", "")
            else:
                result_json = json.loads(rec.PartialResult())
                text = result_json.get("text", "")
                
            final_result = json.loads(rec.FinalResult()).get("text", "")
            return f"{text} {final_result}".strip()
        except Exception as e:
            return f"STT Error: {str(e)}"

    # Note: TTS implementation often works better on the frontend via Web Speech API.
    # For a backend implementation, we'd need sound libraries which vary by OS.
    # We'll focus on the STT transcription here.
