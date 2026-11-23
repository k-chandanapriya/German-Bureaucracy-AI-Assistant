"""Turn uploads into pages a local model can read.

Digital PDFs (most letters sent by email, ELSTER or a portal) already
contain their text: we use it directly, which takes milliseconds instead of
a vision pass. Scanned PDFs and photos are rendered to images. Large phone
photos are scaled down: it makes local inference much faster and loses no
readable detail on an A4 letter.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image, ImageOps

from app.extraction.errors import ExtractionError

IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
PDF_TYPE = "application/pdf"
MAX_SIDE = 1600
MAX_PAGES = 6
PDF_DPI = 150
MIN_TEXT_CHARS = 80  # fewer characters on a PDF page means it's a scan


@dataclass
class Page:
    text: str | None = None  # text layer of a digital PDF page
    image: bytes | None = None  # JPEG for pages that need the vision model


def _to_jpeg(img: Image.Image) -> bytes:
    img = ImageOps.exif_transpose(img)  # phone photos are often stored rotated
    img = img.convert("RGB")
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return buf.getvalue()


def _pdf_pages(data: bytes, use_text_layer: bool) -> list[Page]:
    import pypdfium2 as pdfium

    try:
        pdf = pdfium.PdfDocument(data)
    except pdfium.PdfiumError as e:
        raise ExtractionError("This PDF could not be opened. Is it password-protected?") from e
    pages: list[Page] = []
    try:
        if len(pdf) > MAX_PAGES:
            raise ExtractionError(f"This PDF has {len(pdf)} pages. Please upload at most {MAX_PAGES} pages at a time.")
        for i in range(len(pdf)):
            page = pdf[i]
            if use_text_layer:
                text = page.get_textpage().get_text_range().strip()
                if len(text) >= MIN_TEXT_CHARS:
                    pages.append(Page(text=text))
                    continue
            pages.append(Page(image=_to_jpeg(page.render(scale=PDF_DPI / 72).to_pil())))
    finally:
        pdf.close()
    return pages


def to_pages(files: list[tuple[bytes, str]], use_text_layer: bool = True) -> list[Page]:
    """Every page in upload order: text where the PDF has it, otherwise an image."""
    pages: list[Page] = []
    for data, media_type in files:
        if media_type == PDF_TYPE:
            pages.extend(_pdf_pages(data, use_text_layer))
        elif media_type in IMAGE_TYPES:
            try:
                pages.append(Page(image=_to_jpeg(Image.open(io.BytesIO(data)))))
            except OSError as e:
                raise ExtractionError("One of the images could not be opened.") from e
        else:
            raise ExtractionError(f"Unsupported file type: {media_type}. Upload a JPG, PNG, WEBP or PDF.")
    if not pages:
        raise ExtractionError("No pages found in the upload.")
    if len(pages) > MAX_PAGES:
        raise ExtractionError(f"Please upload at most {MAX_PAGES} pages at a time.")
    return pages


def to_page_images(files: list[tuple[bytes, str]]) -> list[bytes]:
    """JPEG bytes for every page (PDFs always rendered), in upload order."""
    return [p.image for p in to_pages(files, use_text_layer=False) if p.image]
