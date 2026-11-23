"""Turn uploads into page images a local vision model can read.

Local models take images only, so PDFs are rendered page by page. Large
phone photos are scaled down: it makes local inference much faster and
loses no readable detail on an A4 letter.
"""

from __future__ import annotations

import io

from PIL import Image, ImageOps

from app.extraction.errors import ExtractionError

IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
PDF_TYPE = "application/pdf"
MAX_SIDE = 1600
MAX_PAGES = 6
PDF_DPI = 150


def _to_jpeg(img: Image.Image) -> bytes:
    img = ImageOps.exif_transpose(img)  # phone photos are often stored rotated
    img = img.convert("RGB")
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return buf.getvalue()


def _pdf_pages(data: bytes) -> list[bytes]:
    import pypdfium2 as pdfium

    try:
        pdf = pdfium.PdfDocument(data)
    except pdfium.PdfiumError as e:
        raise ExtractionError("This PDF could not be opened. Is it password-protected?") from e
    pages = []
    try:
        for i in range(min(len(pdf), MAX_PAGES)):
            bitmap = pdf[i].render(scale=PDF_DPI / 72)
            pages.append(_to_jpeg(bitmap.to_pil()))
    finally:
        pdf.close()
    return pages


def to_page_images(files: list[tuple[bytes, str]]) -> list[bytes]:
    """Return JPEG bytes for every page, in upload order."""
    pages: list[bytes] = []
    for data, media_type in files:
        if media_type == PDF_TYPE:
            pages.extend(_pdf_pages(data))
        elif media_type in IMAGE_TYPES:
            try:
                pages.append(_to_jpeg(Image.open(io.BytesIO(data))))
            except OSError as e:
                raise ExtractionError("One of the images could not be opened.") from e
        else:
            raise ExtractionError(f"Unsupported file type: {media_type}. Upload a JPG, PNG, WEBP or PDF.")
    if not pages:
        raise ExtractionError("No pages found in the upload.")
    if len(pages) > MAX_PAGES:
        raise ExtractionError(f"Please upload at most {MAX_PAGES} pages at a time.")
    return pages
