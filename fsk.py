import numpy as np
import sounddevice as sd


sample_rate = 44_100
symbol_duration = 0.05

zero_freq = 1_500
one_freq = 3_000

message_to_send = "HELLO SONICBOOM"

message_bytes = message_to_send.encode("utf-8")

bits_test = "".join(
    f"{byte:08b}"
    for byte in message_bytes
)


def make_tone(freq):
    sample_count = int(sample_rate * symbol_duration)
    time = np.arange(sample_count) / sample_rate

    return np.sin(2 * np.pi * freq * time)


def detect_bit(samples):
    spectrum = np.fft.rfft(samples)
    freqs = np.fft.rfftfreq(len(samples), d=1 / sample_rate)

    peak_index = np.argmax(np.abs(spectrum))
    detected_frequency = freqs[peak_index]

    dist0 = abs(detected_frequency - zero_freq)
    dist1 = abs(detected_frequency - one_freq)

    if dist0 < dist1:
        return "0"

    return "1"


def add_noise(signal, noise_strength):
    noise = np.random.normal(
        loc=0,
        scale=noise_strength,
        size=len(signal)
    )

    return signal + noise


transmitted_signal = np.array([])

for bit in bits_test:
    if bit == "0":
        tone = make_tone(zero_freq)
    else:
        tone = make_tone(one_freq)

    transmitted_signal = np.concatenate(
        [transmitted_signal, tone]
    )

audio_to_play = 0.2 * transmitted_signal

print("Playing FSK audio...")
sd.play(audio_to_play.astype(np.float32), sample_rate)
sd.wait()
print("Playback finished.")

received_signal = add_noise(
    transmitted_signal,
    noise_strength=4
)

samples_per_symbol = int(sample_rate * symbol_duration)
received_bits = ""

for start in range(
    0,
    len(received_signal),
    samples_per_symbol
):
    symbol = received_signal[
        start:start + samples_per_symbol
    ]

    received_bits += detect_bit(symbol)


error_count = 0

for sent_bit, received_bit in zip(bits_test, received_bits):
    if sent_bit != received_bit:
        error_count += 1

bit_error_rate = error_count / len(bits_test)

print("Total bits:", len(bits_test))
print("First 50 TX bits:", bits_test[:50])
print("First 50 RX bits:", received_bits[:50])
print("Bit errors:", error_count)
print("BER:", bit_error_rate)


received_bytes = bytes(
    int(received_bits[index:index + 8], 2)
    for index in range(0, len(received_bits), 8)
)

received_message = received_bytes.decode(
    "utf-8",
    errors="replace"
)

print("TX message:", message_to_send)
print("RX message:", received_message)