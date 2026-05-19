# virtual_display

Creates a fake monitor so a headless NVIDIA GPU has something to render to
(required for Sunshine/Moonlight to capture a desktop).

Generates a 128-byte EDID 1.3 blob (`/etc/X11/edid.bin`) via
`gen_edid.py` using VESA CVT Reduced Blanking timings, installs an
`xorg.conf.d` snippet that pins it to a fake `DFP-0` connector, and
enables `lightdm` so X starts at boot.

## Variables

| Variable | Default | Notes |
|---|---|---|
| `virtual_display_width` | `3840` | Pixels. |
| `virtual_display_height` | `2160` | Pixels. |
| `virtual_display_refresh` | `60` | Hz. |
| `virtual_display_busid` | `""` | Empty = autodetect. Set to `PCI:1:0:0` to pin. |
| `virtual_display_connector` | `DFP-0` | NVIDIA connector name for `ConnectedMonitor`. |

## Notes

- The EDID generator is structurally valid but not bit-accurate. If the
  NVIDIA driver rejects it, ship a known-good EDID dump from a real
  monitor instead (place at `/etc/X11/edid.bin`, skip the generation task).
- For datacenter GPUs with no display outputs (A100, H100), this won't
  work — use Xvfb/VirtualGL instead.
