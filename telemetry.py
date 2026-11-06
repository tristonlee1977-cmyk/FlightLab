"""Run the ground station, or use --video to export the same experiment."""
import argparse
import json
import math
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def fly(i):
    angle = i * math.tau / 80
    return dict(lat=round(49.32 + .001 * math.sin(angle), 6),
                lon=round(-123.04 + .0015 * math.cos(angle), 6),
                altitude_m=round(42 + 2 * math.sin(angle), 1),
                speed_ms=8, battery_pct=round(100 - (i % 800) / 10, 1))

def encode(row):
    row = dict(row, lon=f"{row['lon']:.6f}")
    return json.dumps(row, separators=(',', ':')).encode()

class GroundStation:
    def __init__(self, key):
        self.cipher = AESGCM(key)
        self.latest = -1

    def receive(self, seq, payload):
        nonce = seq.to_bytes(12, 'big')
        raw = self.cipher.decrypt(nonce, payload, b'flight-lab-v1')
        if seq <= self.latest:
            raise ValueError('Replay')
        self.latest = seq
        return json.loads(raw)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--video', action='store_true')
    export = parser.parse_args().video
    key = AESGCM.generate_key(bit_length=128)
    drone, station = AESGCM(key), GroundStation(key)
    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    fig.subplots_adjust(bottom=.20, top=.78, wspace=.25)
    fig.suptitle('Ground station  /  GPS integrity experiment', fontsize=20)
    lines = []
    tracks = [[], []]
    for ax, title, color in zip(axes, ['Plain JSON', 'AES-GCM'], ['#cb5638','#137e70']):
        ax.set(title=title, xlabel='East of origin (m)', xlim=(-150,280), ylim=(-140,140))
        ax.set_aspect('equal')
        ax.grid(alpha=.2)
        lines.append(ax.plot([], [], color=color, marker='.', markersize=3)[0])
    axes[0].set_ylabel('North of origin (m)')
    note = fig.text(.06,.07,'',fontsize=10)
    rejected = 0
    def update(i):
        nonlocal rejected
        row = fly(i)
        raw = encode(row)
        packet = drone.encrypt(i.to_bytes(12,'big'), raw, b'flight-lab-v1')
        attack = 26 <= i % 80 < 40
        if attack:
            # Replace one longitude digit in the known plaintext. Apply the
            # identical byte difference at that offset in the ciphertext.
            # Format GPS to six decimal places on the wire (see encode).
            pos = raw.index(b'-123.') + 7
            changed = bytearray(raw)
            # Favor an eastward displacement while preserving one ASCII digit.
            changed[pos] = ord('0') + max(0, raw[pos] - ord('0') - 2)
            if changed[pos] == raw[pos]:
                changed[pos] = ord('1')
            altered = bytearray(packet)
            altered[pos] ^= raw[pos] ^ changed[pos]
            packet, raw = bytes(altered), bytes(changed)
        plain = json.loads(raw)
        readings = [plain]
        try:
            readings.append(station.receive(i,packet))
        except InvalidTag:
            rejected += 1
            readings.append(None)
        for track,line,item in zip(tracks,lines,readings):
            if item is None:
                track.append((float('nan'),float('nan')))
            else:
                track.append(((float(item['lon'])+123.04)*72500,(item['lat']-49.32)*111200))
            del track[:-80]
            line.set_data(*zip(*track))
        note.set_text(f'Frame {i:03}   |   ' + ('GPS edit accepted on left / rejected on right' if attack else 'Authentic reading') +
                      f'   |   Rejected: {rejected}\nAltitude {row["altitude_m"]} m    Speed {row["speed_ms"]} m/s    Battery {row["battery_pct"]}%')
    animation = FuncAnimation(fig,update,frames=range(80) if export else None,
                              init_func=lambda: (), interval=125,repeat=False,cache_frame_data=False)
    if export:
        animation.save('comparison.mp4',writer='ffmpeg',fps=8,dpi=90)
    else:
        plt.show()

if __name__ == '__main__':
    main()
