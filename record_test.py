import numpy as np
import matplotlib.pyplot as plt
import sounddevice as sd

sample_rate = 44_100
recording_seconds = 12

print("Recording... start the FSK transmitter now.")

recording = sd.rec(
    int(sample_rate * recording_seconds),
    samplerate=sample_rate,
    channels=1,
    dtype="float32"
)

sd.wait()

samples = recording[:, 0]

spectrum = np.fft.rfft(samples)
frequencies = np.fft.rfftfreq(
    len(samples),
    d=1 / sample_rate
)

magnitudes = np.abs(spectrum)

plt.plot(frequencies, magnitudes)
plt.title("Microphone recording: FSK frequency spectrum")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude")
plt.xlim(500, 4_000)
plt.grid()
plt.show()