import numpy as np
import sounddevice as sd
import zlib

sample_rate = 44_100
symbol_duration = 0.05

zero_freq = 1_500
one_freq = 3_000

recording_seconds = 35
repetition_count = 3

preamble_bits = "1010101010101010"

samples_per_symbol = int(
    sample_rate * symbol_duration
)


def bits_to_bytes(bits):
    return bytes(
        int(bits[index:index + 8], 2)
        for index in range(0, len(bits), 8)
    )


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


def detect_bit(samples):
    samples = samples - np.mean(samples)

    time = np.arange(len(samples)) / sample_rate

    zero_reference = np.exp(
        -2j * np.pi * zero_freq * time
    )

    one_reference = np.exp(
        -2j * np.pi * one_freq * time
    )

    zero_energy = abs(
        np.sum(samples * zero_reference)
    )

    one_energy = abs(
        np.sum(samples * one_reference)
    )

    if zero_energy > one_energy:
        return "0"

    return "1"


def decode_bits_at(
    recording,
    start_sample,
    bit_count
):
    end_sample = start_sample + (
        bit_count * samples_per_symbol
    )

    if end_sample > len(recording):
        return None

    decoded_bits = ""

    for bit_index in range(bit_count):
        symbol_start = start_sample + (
            bit_index * samples_per_symbol
        )

        symbol_end = symbol_start + samples_per_symbol

        symbol = recording[
            symbol_start:symbol_end
        ]

        decoded_bits += detect_bit(symbol)

    return decoded_bits


def decode_header_bits_at(
    recording,
    start_sample,
    original_bit_count
):
    repeated_bit_count = (
        original_bit_count * repetition_count
    )

    repeated_bits = decode_bits_at(
        recording,
        start_sample,
        repeated_bit_count
    )

    if repeated_bits is None:
        return None

    decoded_bits = ""

    for start in range(
        0,
        len(repeated_bits),
        repetition_count
    ):
        group = repeated_bits[
            start:start + repetition_count
        ]

        if group.count("1") > group.count("0"):
            decoded_bits += "1"
        else:
            decoded_bits += "0"

    return decoded_bits


def decode_repeated_bits_at(
    recording,
    start_sample,
    original_bit_count
):
    repeated_bit_count = (
        original_bit_count * repetition_count
    )

    repeated_bits = decode_bits_at(
        recording,
        start_sample,
        repeated_bit_count
    )

    if repeated_bits is None:
        return None

    decoded_bits = ""

    for bit_index in range(original_bit_count):
        copies = ""

        for copy_index in range(repetition_count):
            index = (
                copy_index * original_bit_count
                + bit_index
            )

            copies += repeated_bits[index]

        if copies.count("1") > copies.count("0"):
            decoded_bits += "1"
        else:
            decoded_bits += "0"

    return decoded_bits


def find_message(recording):
    preamble_length = len(preamble_bits)

    search_step = int(sample_rate * 0.005)
    fine_search_step = 20

    minimum_needed = (
        preamble_length + 16
    ) * samples_per_symbol

    last_start = len(recording) - minimum_needed

    best_match_count = -1
    best_start_sample = None

    for start_sample in range(
        0,
        last_start,
        search_step
    ):
        possible_preamble = decode_bits_at(
            recording,
            start_sample,
            preamble_length
        )

        match_count = sum(
            expected_bit == received_bit
            for expected_bit, received_bit in zip(
                preamble_bits,
                possible_preamble
            )
        )

        if match_count > best_match_count:
            best_match_count = match_count
            best_start_sample = start_sample

        if match_count < 14:
            continue

        fine_start_min = max(
            0,
            start_sample - search_step
        )

        fine_start_max = min(
            last_start,
            start_sample + search_step
        )

        for fine_start in range(
            fine_start_min,
            fine_start_max,
            fine_search_step
        ):
            fine_preamble = decode_bits_at(
                recording,
                fine_start,
                preamble_length
            )

            fine_match_count = sum(
                expected_bit == received_bit
                for expected_bit, received_bit in zip(
                    preamble_bits,
                    fine_preamble
                )
            )

            if fine_match_count < 14:
                continue

            packet_start = fine_start + (
                preamble_length * samples_per_symbol
            )

            length_bits = decode_header_bits_at(
                recording,
                packet_start,
                16
            )

            if length_bits is None:
                continue

            payload_length = int.from_bytes(
                bits_to_bytes(length_bits),
                byteorder="big"
            )

            if payload_length > 500:
                continue

            packet_byte_count = 2 + payload_length + 4
            packet_bit_count = packet_byte_count * 8

            body_start = packet_start + (
                16
                * repetition_count
                * samples_per_symbol
            )

            body_bit_count = packet_bit_count - 16

            body_bits = decode_repeated_bits_at(
                recording,
                body_start,
                body_bit_count
            )

            if body_bits is None:
                continue

            packet_bits = length_bits + body_bits

            packet = bits_to_bytes(packet_bits)
            message = read_packet(packet)

            if message is not None:
                return (
                    message,
                    fine_start,
                    best_match_count,
                    best_start_sample
                )

    return (
        None,
        None,
        best_match_count,
        best_start_sample
    )


print("Receiver is recording.")
print("Run fsk_crc.py on the transmitting device now.")

recording = sd.rec(
    int(sample_rate * recording_seconds),
    samplerate=sample_rate,
    channels=1,
    dtype="float32"
)

sd.wait()

samples = recording[:, 0]

print("Recording finished. Searching for preamble...")

(
    received_message,
    start_sample,
    best_match_count,
    best_start_sample
) = find_message(samples)

best_time = best_start_sample / sample_rate

print(
    "Best preamble match:",
    f"{best_match_count}/{len(preamble_bits)} bits",
    f"at {best_time:.3f} seconds"
)

if received_message is None:
    print("No valid packet found.")
else:
    start_time = start_sample / sample_rate

    print(
        f"Preamble found at: {start_time:.3f} seconds"
    )

    print("CRC check: passed")
    print("Received message:", received_message)