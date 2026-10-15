import zlib


def make_packet(message):
    payload = message.encode("utf-8")

    payload_length = len(payload)
    length_bytes = payload_length.to_bytes(2, byteorder="big")

    crc_value = zlib.crc32(payload)
    crc_bytes = crc_value.to_bytes(4, byteorder="big")

    return length_bytes + payload + crc_bytes


def read_packet(packet):
    payload_length = int.from_bytes(
        packet[0:2],
        byteorder="big"
    )

    payload_start = 2
    payload_end = payload_start + payload_length

    payload = packet[payload_start:payload_end]

    received_crc = int.from_bytes(
        packet[payload_end:payload_end + 4],
        byteorder="big"
    )

    calculated_crc = zlib.crc32(payload)

    if received_crc != calculated_crc:
        return None

    return payload.decode("utf-8")


message_to_send = "HELLO SONICBONK"

packet = make_packet(message_to_send)

print("Packet bytes:", packet)
print("Packet length:", len(packet))

received_message = read_packet(packet)

if received_message is None:
    print("Packet rejected: CRC failed")
else:
    print("Packet accepted:", received_message)