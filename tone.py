import numpy as np
import matplotlib.pyplot as plt

sample_rate = 44_100
duration_seconds = 0.01
frequency_hz = 2000


time = np.arange(int(sample_rate*duration_seconds)) / sample_rate
signal = np.sin(2*np.pi * frequency_hz * time)

spectrum = np.fft.rfft(signal)
frequencies = np.fft.rfftfreq(len(signal),d = 1/sample_rate)

magnitudes = np.abs(spectrum)
peak_index = np.argmax(magnitudes)
detected_frequency = frequencies[peak_index]

print(f"detected frequnecy: {detected_frequency:.0f} Hz")

plt.plot(frequencies, magnitudes)
plt.title("Frequency spectrum of the signal")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude")
plt.xlim(0, 5_000)
plt.grid()
plt.show()