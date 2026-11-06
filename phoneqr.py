"""Phone-access helpers: detect the LAN address and render a scannable QR."""

import io
import socket


DEFAULT_PORT = 8501


def local_ip() -> str | None:
    """The computer's LAN IPv4 address, so a phone on the same Wi-Fi can connect.

    A UDP socket is opened only to learn which interface owns the default route;
    no data is actually sent, and failures simply mean the address is unknown.
    """
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("8.8.8.8", 80))
        return probe.getsockname()[0]
    except OSError:
        return None
    finally:
        probe.close()


def phone_url(port: int = DEFAULT_PORT) -> str | None:
    """A ``http://<lan-ip>:<port>`` address for phones on the same network."""
    ip = local_ip()
    if not ip:
        return None
    return f"http://{ip}:{port}"


def qr_png(text: str) -> bytes | None:
    """Return PNG bytes that encode ``text`` as a QR code.

    ``qrcode`` is an optional dependency: when it is not installed the page
    simply shows the URL as text instead of failing.
    """
    try:
        import qrcode
    except ImportError:
        return None
    image = qrcode.make(text)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def qr_ascii(text: str, invert: bool = True) -> str | None:
    """Return a QR that can be printed in a terminal (``None`` without qrcode).

    ``invert`` suits the usual dark terminal: light blocks on a dark background,
    which phone cameras read the same as a normal QR.
    """
    try:
        import qrcode
    except ImportError:
        return None
    code = qrcode.QRCode(border=1)
    code.add_data(text)
    code.make(fit=True)
    stream = io.StringIO()
    code.print_ascii(out=stream, invert=invert)
    return stream.getvalue()

