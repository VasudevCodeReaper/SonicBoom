import numpy as np
import matplotlib.pyplot as plt

sample_rate = 44_100
symbol_duration = 0.05

zero_freq = 1_500
one_freq = 3_000

bit_count = 1_000
trials_per_noise_level = 5


def make_tone(freq):
    sample_count = int(sample_rate * symbol_duration)
    time = np.arange(sample_count) / sample_rate

    return np.sin(2 * np.pi * freq * time)


def bits_to_signal(bits):
    tones = []

    for bit in bits:
        if bit == "0":
            tones.append(make_tone(zero_freq))
        else:
            tones.append(make_tone(one_freq))

    return np.concatenate(tones)


def add_noise(signal, noise_strength):
    noise = np.random.normal(
        loc=0,
        scale=noise_strength,
        size=len(signal)
    )

    return signal + noise


def detect_bit(samples):
    spectrum = np.fft.rfft(samples)
    freqs = np.fft.rfftfreq(len(samples), d=1 / sample_rate)

    peak_index = np.argmax(np.abs(spectrum))
    detected_frequency = freqs[peak_index]

    if abs(detected_frequency - zero_freq) < abs(detected_frequency - one_freq):
        return "0"

    return "1"


def signal_to_bits(signal):
    samples_per_symbol = int(sample_rate * symbol_duration)
    received_bits = ""

    for start in range(0, len(signal), samples_per_symbol):
        symbol = signal[start:start + samples_per_symbol]
        received_bits += detect_bit(symbol)

    return received_bits


def calculate_ber(sent_bits, received_bits):
    error_count = 0

    for sent_bit, received_bit in zip(sent_bits, received_bits):
        if sent_bit != received_bit:
            error_count += 1

    return error_count / len(sent_bits)


bits_to_send = "".join(
    np.random.choice(["0", "1"], size=bit_count)
)

clean_signal = bits_to_signal(bits_to_send)

noise_levels = range(0, 13)
ber_results = []

for noise_strength in noise_levels:
    trial_bers = []

    for _ in range(trials_per_noise_level):
        noisy_signal = add_noise(clean_signal, noise_strength)
        received_bits = signal_to_bits(noisy_signal)

        ber = calculate_ber(bits_to_send, received_bits)
        trial_bers.append(ber)

    average_ber = np.mean(trial_bers)
    ber_results.append(average_ber)

    print(
        f"Noise: {noise_strength:2d} | "
        f"Average BER: {average_ber:.4f}"
    )


plt.plot(noise_levels, ber_results, marker="o")
plt.title("FSK reliability: noise strength vs BER")
plt.xlabel("Noise strength (standard deviation)")
plt.ylabel("Average Bit Error Rate")
plt.grid()
plt.show()