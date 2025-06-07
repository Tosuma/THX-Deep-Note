import numpy as np
from scipy.signal import butter, lfilter

class SynthVoice:
    def __init__(self, waveform_type, segments, sample_rate=44100):
        self.waveform_type = waveform_type
        self.segments = segments
        self.sample_rate = sample_rate

    def generate_wave(self):
        total_duration = max(seg.start_time + seg.duration for seg in self.segments)
        total_samples = int(self.sample_rate * total_duration)
        output_left = np.zeros(total_samples)
        output_right = np.zeros(total_samples)

        prev_phase = 0.0  # track cumulative phase in radians

        for seg in self.segments:
            t = np.linspace(0, seg.duration, int(self.sample_rate * seg.duration), False)
            start_idx = int(self.sample_rate * seg.start_time)
            end_idx = start_idx + len(t)

            # Frequency path
            if seg.glide_from is not None:
                base_freq = self._interpolate_glide(seg.glide_from, seg.freq, t, seg.glide_shape)
            else:
                base_freq = np.full_like(t, seg.freq)

            # Detune base frequency (in cents)
            if seg.detune_cents != 0:
                base_freq *= 2 ** (seg.detune_cents / 1200)

            # LFO
            if seg.lfo:
                lfo_wave = self._generate_lfo_waveform(t, seg.lfo)
                cents_mod = seg.lfo['depth_cents'] * lfo_wave
                freq_mod = base_freq * (2 ** (cents_mod / 1200))
            else:
                freq_mod = base_freq

            # Maintain phase continuity
            phase = 2 * np.pi * np.cumsum(freq_mod) / self.sample_rate + prev_phase
            prev_phase = phase[-1]  # update for next segment

            mono_wave = self._oscillator(phase,
                             shape_param=seg.osc_shape_param,
                             blend=seg.osc_blend)


            # Apply envelope if present
            if seg.envelope:
                env = seg.envelope(t)
                mono_wave *= env
                
            # Apply filter
            if seg.filter_type and seg.filter_cutoff:
                mono_wave = self._apply_filter(
                    mono_wave,
                    filter_type=seg.filter_type,
                    cutoff=seg.filter_cutoff,
                    resonance=seg.filter_resonance,
                    sample_rate=self.sample_rate
                )

            # Panning
            pan = self._interpolate_pan(seg.pan_from, seg.pan_to, t, seg.pan_shape)
            left_amp = np.cos((np.pi / 4) * (1 + pan))
            right_amp = np.sin((np.pi / 4) * (1 + pan))

            output_left[start_idx:end_idx] += mono_wave * left_amp
            output_right[start_idx:end_idx] += mono_wave * right_amp

        return np.stack([output_left, output_right], axis=1)




    def _generate_lfo_waveform(self, t, lfo):
        phase = 2 * np.pi * lfo['freq'] * t
        shape = lfo['waveform']
        if shape == 'sine':
            return np.sin(phase)
        elif shape == 'triangle':
            return 2 * np.abs(2 * (t * lfo['freq'] % 1) - 1) - 1
        elif shape == 'saw':
            return 2 * (t * lfo['freq'] % 1) - 1
        else:
            raise ValueError("Unsupported LFO waveform")

    def _oscillator(self, phase, shape_param=None, blend=None):
        def gen_wave(shape):
            if shape == 'sine':
                return np.sin(phase)
            elif shape == 'square':
                duty = shape_param if shape_param is not None else 0.5
                return np.where((phase / (2 * np.pi) % 1) < duty, 1.0, -1.0)
            elif shape == 'saw':
                curve = shape_param if shape_param is not None else 1.0
                frac = (phase / (2 * np.pi)) % 1
                return 2 * (frac ** curve) - 1
            elif shape == 'triangle':
                frac = (phase / (2 * np.pi)) % 1
                return 4 * np.abs(frac - 0.5) - 1

            # --- Organ Variants ---
            elif shape == 'flute':
                base = np.sin(phase)
                third = 0.1 * np.sin(3 * phase)  # very light harmonic
                return (base + third) / 1.1

            elif shape == 'principal':
                base = np.sin(phase)
                third = 0.5 * np.sin(3 * phase)
                fifth = 0.3 * np.sin(5 * phase)
                return (base + third + fifth) / 1.8

            elif shape == 'reed':
                # Buzzy pipe, like a saw filtered slightly
                frac = (phase / (2 * np.pi)) % 1
                raw = 2 * frac - 1  # saw
                return 0.5 * raw + 0.5 * np.sin(phase)

            elif shape == 'celeste':
                # Two sine waves detuned
                beat = 0.02  # Detune ratio
                return 0.5 * np.sin(phase) + 0.5 * np.sin(phase * (1 + beat))

            elif shape == 'mixture':
                # Add many harmonics (1st to 7th), scaled down
                wave = np.zeros_like(phase)
                amps = [1.0, 0.6, 0.4, 0.25, 0.15, 0.1, 0.05]
                for i, amp in enumerate(amps):
                    wave += amp * np.sin((i + 1) * phase)
                return wave / sum(amps)

            else:
                raise ValueError(f"Unsupported waveform: {shape}")


        if blend:
            wave1 = gen_wave(blend['from'])
            wave2 = gen_wave(blend['to'])
            amount = np.clip(blend['amount'], 0.0, 1.0)
            return (1 - amount) * wave1 + amount * wave2
        else:
            return gen_wave(self.waveform_type)




    def _interpolate_glide(self, start_freq, end_freq, t, shape):
        if shape == 'linear':
            return np.linspace(start_freq, end_freq, len(t))
        elif shape == 'exponential':
            # Avoid zero/negative
            start_freq = max(start_freq, 1e-3)
            end_freq = max(end_freq, 1e-3)
            return start_freq * (end_freq / start_freq) ** (t / t[-1])
        elif shape == 'sigmoid':
            norm = (t - t[0]) / (t[-1] - t[0])
            return start_freq + (end_freq - start_freq) * (1 / (1 + np.exp(-12 * (norm - 0.5))))
        else:
            raise ValueError(f"Unsupported glide shape: {shape}")

    def _interpolate_pan(self, start_pan, end_pan, t, shape):
        if shape == 'linear':
            return np.linspace(start_pan, end_pan, len(t))
        elif shape == 'sigmoid':
            norm = (t - t[0]) / (t[-1] - t[0])
            return start_pan + (end_pan - start_pan) * (1 / (1 + np.exp(-12 * (norm - 0.5))))
        elif shape == 'exponential':
            norm = (t - t[0]) / (t[-1] - t[0])
            return start_pan + (end_pan - start_pan) * (norm ** 2)
        else:
            raise ValueError("Unsupported pan shape")
        
    def _apply_filter(self, signal, filter_type, cutoff, resonance, sample_rate):
        nyquist = 0.5 * sample_rate
        norm_cutoff = cutoff / nyquist
        b, a = butter(N=2, Wn=norm_cutoff, btype=filter_type)
        return lfilter(b, a, signal)
