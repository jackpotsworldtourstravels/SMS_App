import io

import qrcode
from flask import Response, render_template, url_for
from PIL import Image

from app.blueprints.download import download_bp

# Matches the Android app's build.gradle.kts versionName. There is no
# link between this Flask app and the separate Android Gradle project at
# runtime, so this has to be updated by hand whenever a new APK is
# published to static/downloads/app-latest.apk.
APK_VERSION = "1.1"

# A stable filename — replacing this file in place is enough to publish a
# new build without touching the QR code, the download button, or any
# cached links, since the URL never changes.
APK_FILENAME = "app-latest.apk"

_MIN_QR_PIXELS = 512


def _apk_url() -> str:
    return url_for("static", filename=f"downloads/{APK_FILENAME}", _external=True)


@download_bp.route("/")
def index():
    return render_template(
        "download/index.html",
        apk_url=_apk_url(),
        apk_version=APK_VERSION,
    )


@download_bp.route("/qr.png")
def qr_code():
    img = qrcode.make(
        _apk_url(),
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    ).convert("RGB")

    if img.width < _MIN_QR_PIXELS or img.height < _MIN_QR_PIXELS:
        # NEAREST keeps the QR modules crisp (no blurring) when upscaling.
        img = img.resize((_MIN_QR_PIXELS, _MIN_QR_PIXELS), resample=Image.NEAREST)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return Response(
        buffer.getvalue(),
        mimetype="image/png",
        headers={"Cache-Control": "no-cache"},
    )
