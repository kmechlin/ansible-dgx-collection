#!/usr/bin/env python3
"""Generate a minimal 128-byte EDID 1.3 blob with a single preferred timing.

Uses VESA CVT Reduced Blanking v1 timing formulas. The output validates as
a structurally correct EDID 1.3 (header + checksum + preferred DTD), but is
not bit-accurate to any real panel. If the NVIDIA driver rejects it on your
hardware, ship a known-good EDID binary from a real monitor instead.

Usage:
    gen_edid.py --width 3840 --height 2160 --refresh 60 --out /etc/X11/edid.bin
"""
import argparse


def cvt_rb(width: int, height: int, refresh: int) -> dict:
    """VESA CVT Reduced Blanking v1 timing computation."""
    H_BLANK = 160
    V_FRONT_PORCH = 3
    V_BACK_PORCH = 6
    V_SYNC = 4
    MIN_V_BLANK_US = 460
    CLK_GRANULARITY = 0.25  # MHz

    h_active = width
    v_active = height

    h_period_est_us = ((1.0 / refresh) - (MIN_V_BLANK_US / 1_000_000.0)) / v_active * 1_000_000
    if h_period_est_us <= 0:
        raise ValueError("invalid timing: refresh too high for this resolution")

    v_blank_lines = max(
        V_SYNC + V_BACK_PORCH + V_FRONT_PORCH,
        int(MIN_V_BLANK_US / h_period_est_us) + 1,
    )
    v_total = v_active + v_blank_lines
    h_total = h_active + H_BLANK

    pixel_clock_mhz = (h_total * v_total * refresh) / 1_000_000.0
    pixel_clock_mhz = int(pixel_clock_mhz / CLK_GRANULARITY) * CLK_GRANULARITY

    h_sync = 32
    h_front = 48
    v_front = V_FRONT_PORCH
    v_sync = V_SYNC

    return {
        "pixel_clock_khz": int(pixel_clock_mhz * 1000),
        "h_active": h_active,
        "h_blanking": h_total - h_active,
        "h_sync_offset": h_front,
        "h_sync_width": h_sync,
        "v_active": v_active,
        "v_blanking": v_total - v_active,
        "v_sync_offset": v_front,
        "v_sync_width": v_sync,
    }


def build_dtd(t: dict, h_mm: int, v_mm: int) -> bytes:
    """Build an 18-byte EDID Detailed Timing Descriptor."""
    pc = t["pixel_clock_khz"] // 10  # 10 kHz units
    dtd = bytearray(18)
    dtd[0] = pc & 0xFF
    dtd[1] = (pc >> 8) & 0xFF
    dtd[2] = t["h_active"] & 0xFF
    dtd[3] = t["h_blanking"] & 0xFF
    dtd[4] = ((t["h_active"] >> 4) & 0xF0) | ((t["h_blanking"] >> 8) & 0x0F)
    dtd[5] = t["v_active"] & 0xFF
    dtd[6] = t["v_blanking"] & 0xFF
    dtd[7] = ((t["v_active"] >> 4) & 0xF0) | ((t["v_blanking"] >> 8) & 0x0F)
    dtd[8] = t["h_sync_offset"] & 0xFF
    dtd[9] = t["h_sync_width"] & 0xFF
    dtd[10] = ((t["v_sync_offset"] & 0x0F) << 4) | (t["v_sync_width"] & 0x0F)
    dtd[11] = (
        (((t["h_sync_offset"] >> 8) & 0x03) << 6)
        | (((t["h_sync_width"] >> 8) & 0x03) << 4)
        | (((t["v_sync_offset"] >> 4) & 0x03) << 2)
        | ((t["v_sync_width"] >> 4) & 0x03)
    )
    dtd[12] = h_mm & 0xFF
    dtd[13] = v_mm & 0xFF
    dtd[14] = ((h_mm >> 4) & 0xF0) | ((v_mm >> 8) & 0x0F)
    dtd[15] = 0  # h border
    dtd[16] = 0  # v border
    dtd[17] = 0x1E  # digital separate sync, +H, +V, non-interlaced
    return bytes(dtd)


def build_edid(width: int, height: int, refresh: int) -> bytes:
    t = cvt_rb(width, height, refresh)
    edid = bytearray(128)

    # Header
    edid[0:8] = bytes([0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00])

    # Manufacturer ID "VRT" (virtual)
    mid = ((ord("V") - 64) << 10) | ((ord("R") - 64) << 5) | (ord("T") - 64)
    edid[8] = (mid >> 8) & 0xFF
    edid[9] = mid & 0xFF

    # Product code + serial + week/year
    edid[10:12] = bytes([0x01, 0x00])
    edid[12:16] = bytes([0x01, 0x00, 0x00, 0x00])
    edid[16] = 1            # week
    edid[17] = 34           # year (1990 + 34 = 2024)

    # EDID version 1.3
    edid[18] = 1
    edid[19] = 3

    # Digital input
    edid[20] = 0x80

    # Approximate display size in cm (assume 16:9 ~24")
    edid[21] = 62
    edid[22] = 35

    # Gamma 2.2
    edid[23] = 120

    # Feature support: RGB, preferred timing, sRGB
    edid[24] = 0x0A

    # Chromaticity (sRGB approximation, copied from a typical EDID)
    edid[25:35] = bytes([0xEE, 0x91, 0xA3, 0x54, 0x4C, 0x99, 0x26, 0x0F, 0x50, 0x54])

    # Established timings: none
    edid[35:38] = bytes([0, 0, 0])

    # Standard timings: none (fill with 0x01 0x01)
    for i in range(8):
        edid[38 + i * 2] = 0x01
        edid[39 + i * 2] = 0x01

    # DTD #1 - preferred timing
    edid[54:72] = build_dtd(t, h_mm=620, v_mm=350)

    # DTD #2 - monitor name "Virtual"
    edid[72:90] = b"\x00\x00\x00\xfc\x00Virtual\x0a     "

    # DTD #3 - range limits (vmin=50, vmax=120, hmin=30, hmax=160, pixmax=550MHz)
    edid[90:108] = b"\x00\x00\x00\xfd\x00\x32\x78\x1e\xa0\x37\x00\x0a\x20\x20\x20\x20\x20\x20"

    # DTD #4 - dummy
    edid[108:126] = b"\x00\x00\x00\x10\x00" + b"\x00" * 13

    # Extension flag
    edid[126] = 0

    # Checksum
    edid[127] = (256 - (sum(edid[0:127]) % 256)) % 256

    return bytes(edid)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--width", type=int, required=True)
    ap.add_argument("--height", type=int, required=True)
    ap.add_argument("--refresh", type=int, default=60)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    edid = build_edid(args.width, args.height, args.refresh)
    with open(args.out, "wb") as f:
        f.write(edid)
    print(f"wrote {len(edid)} bytes to {args.out}")


if __name__ == "__main__":
    main()
