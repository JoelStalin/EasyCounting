from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Iterable

from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def _iter_pngs(artifacts_dir: Path) -> Iterable[Path]:
    files = sorted(
        (p for p in artifacts_dir.glob("*.png") if p.is_file()),
        key=lambda p: p.name.lower(),
    )
    return files


def _draw_header(pdf: canvas.Canvas, title: str, subtitle: str) -> None:
    width, height = A4
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(36, height - 48, title)
    pdf.setFont("Helvetica", 10)
    pdf.drawString(36, height - 66, subtitle)
    pdf.line(36, height - 72, width - 36, height - 72)


def _draw_image_page(pdf: canvas.Canvas, image_path: Path, page_no: int, total: int) -> None:
    width, height = A4
    _draw_header(
        pdf,
        "EasyCounting - Evidencia funcional Odoo + Facturas",
        f"Paso {page_no}/{total}  |  Archivo: {image_path.name}",
    )

    img = ImageReader(str(image_path))
    img_w, img_h = img.getSize()
    available_w = width - 72
    available_h = height - 150
    scale = min(available_w / img_w, available_h / img_h)
    draw_w = img_w * scale
    draw_h = img_h * scale
    x = (width - draw_w) / 2
    y = 48 + (available_h - draw_h) / 2
    pdf.drawImage(img, x, y, width=draw_w, height=draw_h, preserveAspectRatio=True, anchor="c")

    pdf.setFont("Helvetica", 9)
    pdf.drawString(36, 30, f"Generado: {datetime.now().isoformat(timespec='seconds')}")
    pdf.drawRightString(width - 36, 30, "EasyCounting QA Evidence")
    pdf.showPage()


def build_pdf(artifacts_dir: Path, output_pdf: Path) -> Path:
    images = list(_iter_pngs(artifacts_dir))
    if not images:
        raise RuntimeError(f"No hay imagenes .png en {artifacts_dir}")

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output_pdf), pagesize=A4)

    width, height = A4
    _draw_header(
        pdf,
        "EasyCounting - Evidencia de pruebas Odoo",
        f"Origen: {artifacts_dir}  |  Total capturas: {len(images)}",
    )
    pdf.setFont("Helvetica", 11)
    pdf.drawString(36, height - 110, "Incluye evidencia visual de:")
    pdf.setFont("Helvetica", 10)
    bullets = [
        "- Login y acceso a integracion Odoo",
        "- Generacion de token para Odoo",
        "- Endpoints visibles para integracion",
        "- Emision de e-CF (cliente)",
        "- Emision demo (seller) como evidencia complementaria",
    ]
    y = height - 130
    for line in bullets:
        pdf.drawString(48, y, line)
        y -= 16
    pdf.showPage()

    total = len(images)
    for idx, image_path in enumerate(images, start=1):
        _draw_image_page(pdf, image_path, idx, total)

    pdf.save()
    return output_pdf


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera PDF de evidencia desde capturas PNG de E2E.")
    parser.add_argument("--artifacts-dir", required=True, help="Directorio con PNG de evidencias")
    parser.add_argument("--out", required=True, help="Ruta del PDF de salida")
    args = parser.parse_args()

    artifacts_dir = Path(args.artifacts_dir).resolve()
    output_pdf = Path(args.out).resolve()
    result = build_pdf(artifacts_dir, output_pdf)
    print(f"PDF generado: {result}")


if __name__ == "__main__":
    main()

