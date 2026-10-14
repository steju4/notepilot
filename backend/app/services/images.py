import warnings
from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
import pypdfium2 as pdfium
from PIL import Image, ImageOps, UnidentifiedImageError

from ..core import MAX_PAGES, MAX_PIXELS

Image.MAX_IMAGE_PIXELS = MAX_PIXELS


def decode_pages(data: bytes, suffix: str):
    if suffix == ".pdf":
        if not data.lstrip().startswith(b"%PDF-"):
            raise ValueError("Die Datei ist kein gültiges PDF.")
        try:
            pdf = pdfium.PdfDocument(data)
            if not 1 <= len(pdf) <= MAX_PAGES:
                raise ValueError(f"PDFs dürfen maximal {MAX_PAGES} Seiten enthalten.")
            result = []
            for i in range(len(pdf)):
                page = pdf[i]
                width, height = page.get_size()
                scale = min(2.5, 3000 / max(width, height))
                if width * height * scale * scale > MAX_PIXELS:
                    raise ValueError("Eine PDF-Seite ist zu groß.")
                bitmap = page.render(scale=scale)
                result.append(bitmap.to_pil().convert("RGB").copy())
                bitmap.close()
                page.close()
            pdf.close()
            return result
        except Exception as error:
            raise ValueError(
                "PDF konnte nicht gelesen werden; prüfe die Datei und die Seitenzahl."
            ) from error
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            image = Image.open(BytesIO(data))
            if image.format not in ("JPEG", "PNG", "WEBP"):
                raise ValueError("Bitte JPG, PNG oder WebP verwenden.")
            if image.width * image.height > MAX_PIXELS:
                raise ValueError("Das Bild ist zu groß.")
            image.load()
            return [ImageOps.exif_transpose(image).convert("RGB")]
    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as error:
        raise ValueError("Das Bild ist beschädigt oder zu groß.") from error


def quality(image: Image.Image):
    image = image.copy()
    image.thumbnail((1600, 1600))
    gray = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2GRAY)
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(gray.mean())
    hints = []
    if min(image.size) < 600:
        hints.append("Niedrige Auflösung: bitte die Noten näher und möglichst scharf aufnehmen.")
    if blur < 65:
        hints.append("Das Foto könnte unscharf sein. Bitte vor dem Fotografieren fokussieren.")
    if brightness < 130:
        hints.append("Das Foto ist dunkel. Gleichmäßige Beleuchtung verbessert die Erkennung.")
    tiles = [float(t.mean()) for t in np.array_split(gray, 4)]
    if max(tiles) - min(tiles) > 55:
        hints.append("Die Beleuchtung ist ungleichmäßig; Schatten möglichst vermeiden.")
    edges = cv2.Canny(gray, 60, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 80, minLineLength=image.width * 0.25, maxLineGap=15)
    angle = 0.0
    if lines is not None:
        angles = [np.degrees(np.arctan2(y2 - y1, x2 - x1)) for [[x1, y1, x2, y2]] in lines]
        angles = [a for a in angles if abs(a) < 15]
        if angles:
            angle = float(np.median(angles))
            if abs(angle) > 1.5:
                hints.append(f"Die Notenzeilen sind etwa {angle:.1f}° geneigt. Ausrichten kann helfen.")
    return dict(
        width=image.width,
        height=image.height,
        sharpness=round(blur, 1),
        brightness=round(brightness, 1),
        skew_degrees=round(angle, 2),
        hints=hints,
    )


def process_image(source: Path, destination: Path, options):
    image = Image.open(source).convert("RGB")
    if options.get("crop"):
        x, y, w, h = options["crop"]
        if not all(0 <= v <= 1 for v in (x, y, w, h)) or w <= 0 or h <= 0 or x + w > 1.001 or y + h > 1.001:
            raise ValueError("Ungültiger Bildausschnitt.")
        image = image.crop(
            (
                round(x * image.width),
                round(y * image.height),
                round((x + w) * image.width),
                round((y + h) * image.height),
            )
        )
    angle = float(options.get("rotate", 0))
    if options.get("deskew"):
        angle += quality(image)["skew_degrees"]
    image = image.rotate(angle, expand=True, fillcolor="white", resample=Image.Resampling.BICUBIC)
    points = options.get("perspective")
    if points:
        if len(points) != 4 or any(len(p) != 2 or any(not 0 <= n <= 1 for n in p) for p in points):
            raise ValueError(
                "Bitte vier gültige Ecken wählen: oben links, oben rechts, unten rechts, unten links."
            )
        src = np.array([[x * image.width, y * image.height] for x, y in points], np.float32)
        if abs(cv2.contourArea(src)) < 100:
            raise ValueError("Der Perspektivbereich ist zu klein.")
        w = int(max(np.linalg.norm(src[1] - src[0]), np.linalg.norm(src[2] - src[3])))
        h = int(max(np.linalg.norm(src[3] - src[0]), np.linalg.norm(src[2] - src[1])))
        dest = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], np.float32)
        transformed = cv2.warpPerspective(
            np.asarray(image), cv2.getPerspectiveTransform(src, dest), (w, h), borderValue=(255, 255, 255)
        )
        image = Image.fromarray(transformed)
    contrast = float(options.get("contrast", 1))
    brightness = float(options.get("brightness", 0))
    if not 0.25 <= contrast <= 3 or not -100 <= brightness <= 100:
        raise ValueError("Ungültige Bildkorrektur.")
    image = Image.fromarray(
        np.clip(np.asarray(image).astype(float) * contrast + brightness, 0, 255).astype(np.uint8)
    )
    if options.get("black_white"):
        gray = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2GRAY)
        gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 12)
        image = Image.fromarray(gray).convert("RGB")
    image.save(destination, "PNG")
    return quality(image)
