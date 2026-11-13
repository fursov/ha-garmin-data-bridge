"""Verify Home Assistant custom-integration brand assets."""

from pathlib import Path
from struct import unpack
from zlib import crc32

BRAND_DIR = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "garmin_data_bridge"
    / "brand"
)
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def test_icon_is_valid_transparent_256px_png() -> None:
    """Ensure the bundled icon is complete, square, and supports transparency."""
    data = (BRAND_DIR / "icon.png").read_bytes()
    assert data.startswith(PNG_SIGNATURE)

    offset = len(PNG_SIGNATURE)
    chunks: set[bytes] = set()
    image_color_type: int | None = None
    while offset < len(data):
        assert len(data) - offset >= 12
        length = unpack(">I", data[offset : offset + 4])[0]
        name = data[offset + 4 : offset + 8]
        chunk_end = offset + length + 12
        assert chunk_end <= len(data)
        payload = data[offset + 8 : chunk_end - 4]
        stored_crc = unpack(">I", data[chunk_end - 4 : chunk_end])[0]
        assert stored_crc == crc32(name + payload)
        chunks.add(name)
        if name == b"IHDR":
            width, height, bit_depth, image_color_type = unpack(">IIBB", payload[:10])
            assert (width, height, bit_depth) == (256, 256, 8)
        offset = chunk_end
        if name == b"IEND":
            break

    assert offset == len(data)
    assert {b"IHDR", b"IDAT", b"IEND"}.issubset(chunks)
    assert image_color_type in (3, 6)
    assert image_color_type == 6 or b"tRNS" in chunks
