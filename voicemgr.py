import wave
import numpy as np

class VoiceManager:
    def __init__(self, sample_rate=44100):
        self.voices = []
        self.sample_rate = sample_rate

    def add_voice(self, voice):
        self.voices.append(voice)

    def _mix_voices(self):
        # Find max length of all voices
        lengths = [voice.generate_wave().shape[0] for voice in self.voices]
        max_len = max(lengths)

        mixed = np.zeros((max_len, 2))  # stereo: [L, R]

        for voice in self.voices:
            wave = voice.generate_wave()  # shape: (N, 2)
            mixed[:wave.shape[0], :] += wave  # mix both channels

        # Optional: normalize
        mixed /= max(len(self.voices), 1)

        return mixed

    def save_wave(self, filename, sample_rate=44100):
        stereo_samples = self._mix_voices()
        stereo_samples = np.clip(stereo_samples, -1.0, 1.0)
        int_samples = (stereo_samples * 32767).astype(np.int16)

        with wave.open(filename, 'w') as wf:
            wf.setnchannels(2)  # stereo
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(int_samples.tobytes())