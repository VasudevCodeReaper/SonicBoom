# SonicBonk FSK Prototype

SonicBonk is an experimental acoustic data-transfer project.

This FSK version sends digital bits through ordinary speakers and microphones using two audible frequencies:

```text
0 → 1500 Hz
1 → 3000 Hz
```

It is designed as a learning prototype, not a production modem.

## Features

- Binary Frequency Shift Keying (FSK)
- Speaker-to-microphone text transfer
- FFT / matched-filter frequency detection
- Preamble-based synchronization
- Packet length field
- CRC-32 corruption detection
- Simple 3× repetition coding
- Image compression and packetization experiments

## Requirements

- Python 3
- Speaker and microphone
- Two terminals, or two nearby devices
- A quiet room for early tests

Install dependencies inside a virtual environment:

```powershell
python -m venv myenv
.\myenv\Scripts\Activate.ps1
python -m pip install numpy scipy sounddevice matplotlib pillow
```

## Main files

```text
fsk_crc.py          Transmitter: converts text to FSK audio and plays it.
receiver_v1.py      Receiver: records microphone audio and reconstructs text.
image_compress.py   Resizes and compresses an image for experiments.
image_packet.py     Splits image bytes into numbered CRC-protected packets.
```

## How FSK transfer works

```text
Text
 ↓
UTF-8 bytes
 ↓
Packet: length + payload + CRC
 ↓
Bits
 ↓
0 = 1500 Hz
1 = 3000 Hz
 ↓
Speaker
 ~ acoustic channel ~
Microphone
 ↓
Detect 1500 Hz or 3000 Hz
 ↓
Bits → packet → CRC check → text
```

## Important shared settings

These values must match in both `fsk_crc.py` and `receiver_v1.py`:

```python
sample_rate = 44_100
symbol_duration = 0.05

zero_freq = 1_500
one_freq = 3_000

repetition_count = 3
preamble_bits = "1010101010101010"
```

If the sender and receiver use different values, decoding fails.

## Sending text

In `fsk_crc.py`, set the message:

```python
message_to_send = "HELLO WORLD"
```

Start the receiver first:

```powershell
python receiver_v1.py
```

While it says it is recording, start the transmitter in another terminal:

```powershell
python fsk_crc.py
```

Expected successful receiver output:

```text
Preamble found at: 2.500 seconds
CRC check: passed
Received message: HELLO WORLD
```

## What the receiver checks

The receiver performs these checks:

```text
1. Find the preamble.
2. Identify each FSK tone.
3. Reconstruct the repeated bits.
4. Rebuild the packet.
5. Verify CRC-32.
6. Display text only if CRC passes.
```

A result such as this is good behavior:

```text
No valid packet found.
```

It means the receiver refused to trust corrupted data.

## Choosing recording duration

The receiver must record long enough for you to switch terminals and for the whole transmission to finish.

Recommended values:

```python
recording_seconds = 20
```

For longer messages:

```python
recording_seconds = 40
```

## Volume

Start with low volume:

```python
audio_to_play = 0.15 * transmitted_signal
```

If the microphone cannot detect the tones, increase gradually:

```python
audio_to_play = 0.25 * transmitted_signal
```

Avoid speaker or microphone clipping. Louder is not always better.

## Preparing an image

Compress an image before any transfer attempt:

```powershell
python image_compress.py
```

Enter the image path without quotation marks:

```text
C:\Users\vasud\Downloads\image.png
```

The script creates:

```text
tiny_image.jpg
```

Then test image packetization:

```powershell
python image_packet.py
```

Expected output:

```text
Image bytes: 1208
Chunk size: 32
Total packets: 38
Success: image reconstructed exactly.
```

## Image transfer status

The FSK prototype can prepare and reconstruct image packets in software.

Real acoustic image transfer is very slow because the FSK version sends only one bit per tone and uses repetition coding for reliability.

At:

```text
symbol duration = 0.05 seconds
repetition count = 3
```

the effective rate is under one byte per second.

Use FSK for:

- Learning communication-system fundamentals
- Reliable text messages
- Testing packet formats
- Testing CRC and synchronization
- Tiny image experiments

Use OFDM/QPSK for faster image transfers.

## Troubleshooting

### `No valid packet found`

Check:

- Receiver started before transmitter.
- Sender and receiver settings match exactly.
- Microphone permission is enabled.
- Speaker volume is high enough.
- Devices are nearby.
- The room is reasonably quiet.
- Recording duration is long enough.

### Preamble is found but CRC fails

This means synchronization worked, but payload bits were corrupted.

Try:

- Lowering speaker volume if audio clips.
- Moving devices closer.
- Increasing `symbol_duration`.
- Using a shorter message.
- Raising `repetition_count`.
- Reducing background noise.

### PowerShell cannot activate the virtual environment

Run this in the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate again:

```powershell
.\myenv\Scripts\Activate.ps1
```

## Project milestone

The FSK milestone is complete when this works:

```text
Laptop speaker
     ↓
Acoustic FSK tones
     ↓
Laptop microphone
     ↓
CRC-verified text appears at the receiver
```

The next-generation SonicBonk architecture uses:

```text
QPSK + OFDM + pilots + cyclic prefix + chunked file transfer
```

That architecture is intended for much faster image transfer.
