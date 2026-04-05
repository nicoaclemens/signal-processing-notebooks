import numpy as np
from IPython.display import Audio, display


class AudioManager:
    """
    Manager for generating and playing audio signals.

    Usage:
        audio = AudioManager(sample_rate=44100)
        audio.play_signal(lambda t: np.sin(2*np.pi*440*t), duration=2.0)
    """

    def __init__(self, sample_rate: int = 44100):
        """
        Initialize the AudioManager.

        Args:
            sample_rate: Sample rate in Hz (default: 44100, standard CD quality)
        """
        self.sample_rate = sample_rate

    def generate_signal(self, signal_func, duration: float = 2.0):
        """
        Generate audio signal from a function.

        Args:
            signal_func: Function that takes time array and returns signal
            duration: Duration in seconds

        Returns:
            numpy array of audio samples
        """
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

        Args:
            signal_func: Function that takes time array and returns signal
            duration: Duration in seconds
            autoplay: Whether to autoplay the audio
        """
        signal = self.generate_signal(signal_func, duration)
        display(Audio(signal, rate=self.sample_rate, autoplay=autoplay))

    def play_array(self, signal, autoplay: bool = True):
        """
        Play an audio signal from a numpy array.

        Args:
            signal: numpy array of audio samples
            autoplay: Whether to autoplay the audio
        """
        # Normalize to prevent clipping
        max_val = np.max(np.abs(signal))
        if max_val > 0:
            signal = signal / max_val * 0.9

        display(Audio(signal, rate=self.sample_rate, autoplay=autoplay))
