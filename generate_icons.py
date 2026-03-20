"""Genere les icones PWA pour l'app NGAP kine."""

import struct
import zlib
from pathlib import Path


def create_png_icon(size, output_path):
    """Cree une icone PNG simple : fond bleu medical #2b7ca8."""
    bg_r, bg_g, bg_b = 0x2B, 0x7C, 0xA8
    raw_rows = []

    for y in range(size):
        row = bytearray()
        row.append(0)
        for x in range(size):
            cx, cy = x - size // 2, y - size // 2
            radius = size // 2 - 2
            corner_radius = size // 5

            in_rect = abs(cx) <= radius and abs(cy) <= radius
            in_corner = True
            if abs(cx) > radius - corner_radius and abs(cy) > radius - corner_radius:
                dx = abs(cx) - (radius - corner_radius)
                dy = abs(cy) - (radius - corner_radius)
                in_corner = (dx * dx + dy * dy) <= corner_radius * corner_radius

            if in_rect and in_corner:
                row.extend([bg_r, bg_g, bg_b, 255])
            else:
                row.extend([0, 0, 0, 0])
        raw_rows.append(bytes(row))

    raw_data = b"".join(raw_rows)

    def make_chunk(chunk_type, data):
        chunk = chunk_type + data
        crc = zlib.crc32(chunk) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + chunk + struct.pack(">I", crc)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as file_obj:
        file_obj.write(b"\x89PNG\r\n\x1a\n")
        ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
        file_obj.write(make_chunk(b"IHDR", ihdr))
        compressed = zlib.compress(raw_data)
        file_obj.write(make_chunk(b"IDAT", compressed))
        file_obj.write(make_chunk(b"IEND", b""))

    print(f"Icone {size}x{size} generee : {output_path}")


if __name__ == "__main__":
    create_png_icon(192, "static/icon-192.png")
    create_png_icon(512, "static/icon-512.png")
