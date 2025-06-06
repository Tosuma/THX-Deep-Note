import random
from envelope import Envelope
from voice import SynthVoice
from voicemgr import VoiceManager
from voicesegment import VoiceSegment

num_voices = 30
sample_rate = 44100
glide_duration = 5.0
total_duration = 25.0  # total duration of the piece

voice_list = []
pitches = [
    1480,
    1174.7,
    880,
    487.33,
    440,
    293.67,
    220,
    146.83,
    110,
    73.416,
    36.708,
]
detunes = [0, -10, 10]
osc_shape = 1

for target_pitch in pitches:
    hold1_duration = random.uniform(8.0, 9.0)
    hold2_start = hold1_duration + glide_duration
    hold2_duration = total_duration - hold2_start
    pan = random.uniform(-1.0, 1.0)
    
    for detune in detunes:
        init_pitch = random.uniform(200, 400)
        lfo_settings={
            'waveform': 'triangle',
            'freq': 0.25,
            'depth_cents': 50
        }
        # initial noise
        seg1 = VoiceSegment(
            start_time=0.0,
            duration=hold1_duration,
            freq=init_pitch,
            lfo=lfo_settings,
            envelope=Envelope.attack(hold1_duration, attack_time=6.0),
            pan_from=pan,
            pan_to=pan,
            detune_cents=detune,
            osc_shape_param=osc_shape
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
            detune_cents=detune,
            osc_shape_param=osc_shape
        )

        # final sustain
        seg3 = VoiceSegment(
            start_time=hold2_start,
            duration=hold2_duration,
            freq=target_pitch,
            # lfo=lfo_settings,
            envelope=Envelope.release(hold2_duration, release_time=3.0),
            pan_from=pan,
            pan_to=pan,
            detune_cents=detune,
            osc_shape_param=osc_shape
        )

        voice = SynthVoice('saw',  [seg1, seg2, seg3], sample_rate=sample_rate)
        voice_list.append(voice)


vm = VoiceManager(sample_rate=sample_rate)
for v in voice_list:
    vm.add_voice(v)

vm.save_wave("thx.wav")