from pathlib import Path
import math
import zlib

chunk_size = 32

input_path = Path("tiny_image.jpg")
output_path = Path("reconstructed_tiny_image.jpg")


def make_packet(sequence_number, total_packets, chunk):
    header = (
        sequence_number.to_bytes(2, byteorder="big")
        + total_packets.to_bytes(2, byteorder="big")
    )

    payload = header + chunk

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
    if len(packet) < 10:
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

    sequence_number = int.from_bytes(
        payload[0:2],
        byteorder="big"
    )

    total_packets = int.from_bytes(
        payload[2:4],
        byteorder="big"
    )

    chunk = payload[4:]

    return sequence_number, total_packets, chunk


image_bytes = input_path.read_bytes()

total_packets = math.ceil(
    len(image_bytes) / chunk_size
)

packets = []

for sequence_number in range(total_packets):
    start = sequence_number * chunk_size
    end = start + chunk_size

    chunk = image_bytes[start:end]

    packet = make_packet(
        sequence_number,
        total_packets,
        chunk
    )

    packets.append(packet)

print("Image bytes:", len(image_bytes))
print("Chunk size:", chunk_size)
print("Total packets:", total_packets)

received_chunks = {}

for packet in packets:
    result = read_packet(packet)

    if result is None:
        print("A packet failed CRC.")
        continue

    sequence_number, total, chunk = result

    received_chunks[sequence_number] = chunk

if len(received_chunks) != total_packets:
    print("Image incomplete.")
else:
    reconstructed_image = b"".join(
        received_chunks[sequence_number]
        for sequence_number in range(total_packets)
    )

    output_path.write_bytes(reconstructed_image)

    if image_bytes == reconstructed_image:
        print("Success: image reconstructed exactly.")
    else:
        print("Error: reconstructed image differs.")