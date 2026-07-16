import io

from PIL import Image


def test_download_page_renders_without_login(client):
    response = client.get("/download/")
    assert response.status_code == 200
    assert b"Download App" in response.data
    assert b"Scan to Download Transaction SMS App" in response.data
    assert b"Version 1.1" in response.data
    assert b"Download APK" in response.data


def test_download_page_renders_when_logged_in(logged_in_client):
    response = logged_in_client.get("/download/")
    assert response.status_code == 200
    assert b"Download App" in response.data


def test_qr_code_is_png_at_least_512px(client):
    response = client.get("/download/qr.png")
    assert response.status_code == 200
    assert response.mimetype == "image/png"

    img = Image.open(io.BytesIO(response.data))
    assert img.format == "PNG"
    assert img.width >= 512
    assert img.height >= 512


def test_qr_code_and_download_button_point_to_same_apk_url(client):
    page = client.get("/download/").get_data(as_text=True)
    import re

    apk_url_match = re.search(r'href="([^"]*app-latest\.apk)"', page)
    qr_src_match = re.search(r'src="([^"]*/download/qr\.png)"', page)
    assert apk_url_match is not None
    assert qr_src_match is not None
    assert apk_url_match.group(1).endswith("/static/downloads/app-latest.apk")


def test_apk_file_is_served_and_downloadable(client):
    response = client.get("/static/downloads/app-latest.apk")
    assert response.status_code == 200
    assert response.content_length is not None
    assert response.content_length > 0
