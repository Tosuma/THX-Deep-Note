import random
from envelope import Envelope
from voice import SynthVoice
from voicemgr import VoiceManager
from voicesegment import VoiceSegment

base_freqs: dict[str, float] = {
    "C": 16.35,
    "C#": 17.32,
    "D": 18.35,
    "D#": 19.45,
    "E": 20.60,
    "F": 21.83,
    "F#": 23.12,
    "G": 24.50,
    "G#": 25.96,
    "A": 27.50,
    "A#": 29.14,
    "B": 30.87,
}

target_chord_bass: list[tuple[str, int]] = [
    ("D", 1),
    ("D", 2),
    ("A", 2),
    ("D", 3),
    ("A", 3),
]
target_chord_treble: list[tuple[str, int]] = [
    ("D", 4),
    ("A", 4),
    ("D", 5),
    ("A", 5),
    ("D", 6),
    ("F#", 6),
]

def key_to_freq(key: str, octave: float):
    return base_freqs[key] * 2 ** octave

def generate_deep_note(
    filename: str,
    total_duration: float = 20.0,
    glide_duration: float = 5.0,
    sample_rate: int = 44100,
    num_bass_voices: int = 2,
    num_treble_voices: int = 3
    ):
    global base_freqs, target_chord_bass, target_chord_treble
    
    voice_list = []
    all_voices = [
        (num_bass_voices, target_chord_bass),
        (num_treble_voices, target_chord_treble),
    ]
    
    for num_voices, notes in all_voices:
        for key, octave in notes:
            target_pitch = key_to_freq(key, octave)
            hold1_duration = random.uniform(8.0, 9.0)
            hold2_start = hold1_duration + glide_duration
            hold2_duration = total_duration - hold2_start
            # pan = random.uniform(-1.0, 1.0) if key != "F#" else 0
            
            # settings for segments
            lfo_settings = {
                'waveform': 'triangle',
                'freq': 0.25,
                'depth_cents': 50
            }
            osc_settings = {
                'from': 'saw',
                'to': 'sine',
                'amount': 0.6,
            }
            filter_type = 'lowpass'
            filter_cutoff = 4000.0
            
            for voice in range(num_voices):
                init_pitch = random.uniform(200, 400)
                if voice == 0:
                    pan = -1 if key != "F#" else -0.25
                elif voice == 1:
                    pan = 1 if key != "F#" else 0.25
                else:
                    pan = 0

                # initial noise
                seg1 = VoiceSegment(
                    start_time=0.0,
                    duration=hold1_duration,
                    freq=init_pitch,
                    lfo=lfo_settings,
                    envelope=Envelope.attack(hold1_duration, attack_time=6.0),
                    pan_from=pan,
                    pan_to=pan,
                    detune_cents=0,
                    osc_shape_param=1,
                    # osc_blend=osc_settings,
                    filter_type=filter_type,
                    filter_cutoff=filter_cutoff,
                )

                # note glide
                seg2 = VoiceSegment(
                    start_time=hold1_duration,
                    duration=glide_duration,
                    freq=target_pitch,
                    glide_from=init_pitch,
                    glide_shape='sigmoid',
                    pan_from=pan,
                    pan_to=pan,
                    detune_cents=0,
                    osc_shape_param=1,
                    # osc_blend=osc_settings,
                    filter_type=filter_type,
                    filter_cutoff=filter_cutoff,
                    # lfo={
                    #     'waveform': 'sine',
                    #     'freq': 0.15,
                    #     'depth_cents': 5
                    # },
                )

                # final sustain
                seg3 = VoiceSegment(
                    start_time=hold2_start,
                    duration=hold2_duration,
                    freq=target_pitch,
                    # lfo={
                    #     'waveform': 'sine',
                    #     'freq': 0.15,
                    #     'depth_cents': 5
                    # },
                    envelope=Envelope.release(hold2_duration, release_time=3.0),
                    pan_from=pan,
                    pan_to=pan,
                    detune_cents=0,
                    osc_shape_param=1,
                    # osc_blend=osc_settings,
                    filter_type=filter_type,
                    filter_cutoff=filter_cutoff,
                )

                voice = SynthVoice('mixture',  [seg1, seg2, seg3], sample_rate=sample_rate)
                voice_list.append(voice)
    
    
    vm = VoiceManager(sample_rate=sample_rate)
    for v in voice_list:
        vm.add_voice(v)

    vm.save_wave(filename)


if __name__ == "__main__":
    generate_deep_note("thx.wav")