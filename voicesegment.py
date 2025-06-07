class VoiceSegment:
    def __init__(self, start_time, duration, freq, lfo=None,
                 glide_from=None, glide_shape='linear',
                 pan_from=0.0, pan_to=0.0, pan_shape='linear',
                 envelope=None,
                 detune_cents=0.0,
                 osc_shape_param=None,
                 osc_blend=None,
                 filter_type=None,
                 filter_cutoff=None,
                 filter_resonance=0.707):  # Q=0.707 is butterworth
        self.start_time = start_time
        self.duration = duration
        self.freq = freq
        self.lfo = lfo
        self.glide_from = glide_from
        self.glide_shape = glide_shape
        self.pan_from = pan_from
        self.pan_to = pan_to
        self.pan_shape = pan_shape
        self.envelope = envelope
        self.detune_cents = detune_cents
        self.osc_shape_param = osc_shape_param
        self.osc_blend = osc_blend
        self.filter_type = filter_type
        self.filter_cutoff = filter_cutoff
        self.filter_resonance = filter_resonance