"""
Generates a valid multi-resolution Windows .ICO file without requiring PIL.
Creates 16x16, 32x32, and 48x48 icon formats with a high-contrast cyan bolt.
"""

import struct

def generate_ico(filename="autoclicker.ico"):
    sizes = [16, 32, 48]
    images_data = []

    for size in sizes:
        # BMP BITMAPINFOHEADER (40 bytes)
        # For ICO, biHeight is 2 * height (for XOR + AND masks)
        bi_size = 40
        bi_width = size
        bi_height = size * 2
        bi_planes = 1
        bi_bit_count = 32
        bi_compression = 0
        bi_size_image = size * size * 4
        bi_x_pels = 0
        bi_y_pels = 0
        bi_clr_used = 0
        bi_clr_important = 0

        header = struct.pack(
            "<IIIHHIIIIII",
            bi_size, bi_width, bi_height, bi_planes, bi_bit_count,
            bi_compression, bi_size_image, bi_x_pels, bi_y_pels,
            bi_clr_used, bi_clr_important
        )

        # Pixel data (BGRA 32-bit, bottom-to-top)
        pixels = bytearray()
        cx, cy = size / 2.0, size / 2.0
        r_outer = size * 0.46
        r_inner = size * 0.38

        for y in range(size):
            # bottom-up in BMP
            real_y = (size - 1) - y
            for x in range(size):
                dx = x - cx
                dy = real_y - cy
                dist = (dx * dx + dy * dy) ** 0.5

                # Drawing a dark slate circle with glowing cyan/emerald ring and center bolt
                if dist <= r_outer:
                    if dist >= r_inner:
                        # Cyan neon border: #06b6d4 -> (212, 182, 6, 255) in BGRA
                        pixels.extend([212, 182, 6, 255])
                    elif abs(dx) < size * 0.15 and abs(dy) < size * 0.28:
                        # Center Bolt: #22c55e (Green/Cyan)
                        pixels.extend([94, 197, 34, 255])
                    else:
                        # Dark Core: #090d16
                        pixels.extend([22, 13, 9, 240])
                else:
                    # Transparent
                    pixels.extend([0, 0, 0, 0])

        # AND mask (1 bit per pixel, row padded to 32 bits)
        # All 0 for 32-bit ARGB
        row_bytes = (size + 31) // 32 * 4
        and_mask = bytes(row_bytes * size)

        img_bytes = header + bytes(pixels) + and_mask
        images_data.append((size, img_bytes))

    # ICONDIR header (6 bytes)
    # idReserved=0, idType=1 (icon), idCount=len(sizes)
    icondir = struct.pack("<HHH", 0, 1, len(images_data))

    # ICONDIRENTRY (16 bytes each)
    offset = 6 + 16 * len(images_data)
    entries = []
    for size, img_bytes in images_data:
        b_width = size if size < 256 else 0
        b_height = size if size < 256 else 0
        b_color_count = 0
        b_reserved = 0
        w_planes = 1
        w_bit_count = 32
        dw_bytes_in_res = len(img_bytes)
        dw_image_offset = offset

        entry = struct.pack(
            "<BBBBHHII",
            b_width, b_height, b_color_count, b_reserved,
            w_planes, w_bit_count, dw_bytes_in_res, dw_image_offset
        )
        entries.append(entry)
        offset += dw_bytes_in_res

    with open(filename, "wb") as f:
        f.write(icondir)
        for e in entries:
            f.write(e)
        for _, img_bytes in images_data:
            f.write(img_bytes)

    print(f"[✓] Generated native high-resolution icon: {filename}")

if __name__ == "__main__":
    generate_ico("autoclicker.ico")
