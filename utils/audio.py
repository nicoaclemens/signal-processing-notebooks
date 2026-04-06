# used by:
import numpy as np
from IPython.display import Audio, display

# not used


class AudioManager:

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate

    def generate_signal(self, signal_func, duration: float = 2.0) -> np.ndarray:
        t = np.linspace(0, duration, int(self.sample_rate * duration), endpoint=False)
        signal = signal_func(t)

        # Normalize to prevent clipping
        max_val = np.max(np.abs(signal))
        if max_val > 0:
            signal = signal / max_val * 0.9

        return signal

    def play_signal(self, signal_func, duration: float = 2.0, autoplay: bool = True):
        """
        Generate and play an audio signal.
        """
        signal = self.generate_signal(signal_func, duration)
        display(Audio(signal, rate=self.sample_rate, autoplay=autoplay))

    def play_array(self, signal, autoplay: bool = True):
        """
        Play an audio signal from a numpy array.
        """
        # Normalize to prevent clipping
        max_val = np.max(np.abs(signal))
        if max_val > 0:
            signal = signal / max_val * 0.9

        display(Audio(signal, rate=self.sample_rate, autoplay=autoplay))
