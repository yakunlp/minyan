"""Print the LAN address (and a scan-me QR) so a phone can open the web page.

Run this while the service is running. It does not require the page to be open on
the computer first: just scan the QR below with the phone camera.

    & '.venv\\Scripts\\python.exe' phone_address.py
"""

import argparse
import sys

import phoneqr


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Show the phone URL (and a QR) for this computer."
    )
    parser.add_argument("--port", type=int, default=phoneqr.DEFAULT_PORT)
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    url = phoneqr.phone_url(args.port)
    if not url:
        print("无法检测局域网地址：请先让电脑连上 Wi-Fi/网络，再运行本脚本。", flush=True)
        print(f"备用写法：http://<电脑的无线 IPv4>:{args.port}", flush=True)
        return 1

    print(f"📱 手机访问地址：{url}", flush=True)
    qr = phoneqr.qr_ascii(url)
    if qr:
        print(qr, flush=True)
        print("用手机相机对着上面的方块扫码即可打开（无需先在电脑上打开网页）。", flush=True)
    else:
        print("（未安装 qrcode，请在手机浏览器直接输入上面的地址。）", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
