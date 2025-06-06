import numpy as np

class Envelope:
    def attack(duration, attack_time):
        def fn(t):
            env = np.ones_like(t)
            attack_samples = int(attack_time * len(t) / duration)
            env[:attack_samples] = np.linspace(0, 1, attack_samples)
            return env
        return fn

    def release (duration, release_time):
        def fn(t):
            env = np.ones_like(t)
            release_samples = int(release_time * len(t) / duration)
            env[-release_samples:] = np.linspace(1, 0, release_samples)
            return env
        return fn

    def flat(duration):
        return lambda t: np.ones_like(t)