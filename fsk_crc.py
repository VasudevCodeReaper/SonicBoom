import numpy as np
import sounddevice as sd
import zlib

sample_rate = 44_100
symbol_duration = 0.05

zero_freq = 1_500
one_freq = 3_000

noise_strength = 4
repetition_count = 3

preamble_bits = "1010101010101010"


def make_packet(message):
    payload = message.encode("utf-8")

    length_bytes = len(payload).to_bytes(
        2,
        byteorder="big"
    )

    crc_bytes = zlib.crc32(payload).to_bytes(
        4,
        byteorder="big"
    )

    return length_bytes + payload + crc_bytes


def read_packet(packet):
    if len(packet) < 6:
        return None

    payload_length = int.from_bytes(
        packet[0:2],
        byteorder="big"
    )

    payload_end = 2 + payload_length

    if len(packet) != payload_end + 4:
        return None

    payload = packet[2:payload_end]

    received_crc = int.from_bytes(
        packet[payload_end:payload_end + 4],
        byteorder="big"
    )

    if zlib.crc32(payload) != received_crc:
        return None

    return payload.decode("utf-8", errors="replace")


def bytes_to_bits(data):
    return "".join(
        f"{byte:08b}"
        for byte in data
    )


def bits_to_bytes(bits):
    return bytes(
        int(bits[index:index + 8], 2)
        for index in range(0, len(bits), 8)
    )


def repeat_header_bits(bits, repeats):
    return "".join(
        bit * repeats
        for bit in bits
    )


def decode_header_bits(bits, repeats):
    decoded_bits = ""

    for start in range(0, len(bits), repeats):
        group = bits[start:start + repeats]

        if group.count("1") > group.count("0"):
            decoded_bits += "1"
        else:
            decoded_bits += "0"

    return decoded_bits


def repeat_bits(bits, repeats):
    return "".join(
        bits
        for _ in range(repeats)
    )


def decode_repeated_bits(bits, repeats):
    original_bit_count = len(bits) // repeats
    decoded_bits = ""

    for bit_index in range(original_bit_count):
        copies = ""

        for copy_index in range(repeats):
            index = (
                copy_index * original_bit_count
                + bit_index
            )

            copies += bits[index]

        if copies.count("1") > copies.count("0"):
            decoded_bits += "1"
        else:
            decoded_bits += "0"

    return decoded_bits


def make_tone(freq):
    sample_count = int(sample_rate * symbol_duration)
    time = np.arange(sample_count) / sample_rate

    return np.sin(
        2 * np.pi * freq * time
    )


def bits_to_signal(bits):
    tones = []

    for bit in bits:
        if bit == "0":
            tones.append(make_tone(zero_freq))
        else:
            tones.append(make_tone(one_freq))

    return np.concatenate(tones)


def add_noise(signal, strength):
    noise = np.random.normal(
        loc=0,
        scale=strength,
        size=len(signal)
    )

    return signal + noise


def detect_bit(samples):
    spectrum = np.fft.rfft(samples)

    frequencies = np.fft.rfftfreq(
        len(samples),
        d=1 / sample_rate
    )

    peak_index = np.argmax(np.abs(spectrum))
    peak_frequency = frequencies[peak_index]

    if abs(peak_frequency - zero_freq) < abs(peak_frequency - one_freq):
        return "0"

    return "1"


def signal_to_bits(signal):
    samples_per_symbol = int(
        sample_rate * symbol_duration
    )

    received_bits = ""

    for start in range(
        0,
        len(signal),
        samples_per_symbol
    ):
        symbol = signal[
            start:start + samples_per_symbol
        ]

        received_bits += detect_bit(symbol)

    return received_bits


message_to_send = "HELLO WORLD"

packet_to_send = make_packet(message_to_send)
packet_bits = bytes_to_bits(packet_to_send)

header_bits = packet_bits[:16]
body_bits = packet_bits[16:]

encoded_header_bits = repeat_header_bits(
    header_bits,
    repetition_count
)

encoded_body_bits = repeat_bits(
    body_bits,
    repetition_count
)

encoded_packet_bits = (
    encoded_header_bits
    + encoded_body_bits
)

bits_to_send = preamble_bits + encoded_packet_bits

transmitted_signal = bits_to_signal(bits_to_send)

audio_to_play = 0.15 * transmitted_signal

print("Playing FSK packet through the speaker...")

sd.play(
    audio_to_play.astype(np.float32),
    sample_rate
)

sd.wait()

print("Playback finished.")

received_signal = add_noise(
    transmitted_signal,
    noise_strength
)

received_bits = signal_to_bits(received_signal)

received_preamble = received_bits[
    :len(preamble_bits)
]

received_packet_encoded_bits = received_bits[
    len(preamble_bits):
]

header_encoded_length = (
    16 * repetition_count
)

received_header_encoded_bits = (
    received_packet_encoded_bits[
        :header_encoded_length
    ]
)

received_body_encoded_bits = (
    received_packet_encoded_bits[
        header_encoded_length:
    ]
)

received_header_bits = decode_header_bits(
    received_header_encoded_bits,
    repetition_count
)

received_body_bits = decode_repeated_bits(
    received_body_encoded_bits,
    repetition_count
)

received_packet_bits = (
    received_header_bits
    + received_body_bits
)

received_packet = bits_to_bytes(
    received_packet_bits
)

received_message = read_packet(received_packet)

print("TX message:", message_to_send)
print("Packet bytes:", len(packet_to_send))

print(
    "Preamble detected:",
    received_preamble == preamble_bits
)

if received_message is None:
    print("RX result: Packet rejected — CRC failed")
else:
    print("RX result: Packet accepted")
    print("RX message:", received_message)