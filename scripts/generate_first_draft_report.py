"""Generate the French first-delivery PDF report from a JSON validation summary."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

INK = colors.HexColor("#172033")
NAVY = colors.HexColor("#17365D")
TEAL = colors.HexColor("#17807A")
PALE = colors.HexColor("#EAF3F5")
LIGHT = colors.HexColor("#F5F7FA")
MUTED = colors.HexColor("#5B6576")
WHITE = colors.white


def _register_fonts() -> tuple[str, str]:
    """Register ReportLab's bundled Vera fonts for reliable French glyph support."""
    import reportlab

    font_dir = Path(reportlab.__file__).resolve().parent / "fonts"
    regular = font_dir / "Vera.ttf"
    bold = font_dir / "VeraBd.ttf"
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("AsteriaSans", regular))
        pdfmetrics.registerFont(TTFont("AsteriaSans-Bold", bold))
        return "AsteriaSans", "AsteriaSans-Bold"
    return "Helvetica", "Helvetica-Bold"


def _safe(value: object) -> str:
    """Escape content for ReportLab paragraphs."""
    import html

    return html.escape(str(value)).replace("\n", "<br/>")


def _load_summary(path: Path) -> dict[str, Any]:
    """Load and minimally validate the report summary."""
    data = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "project",
        "task_division",
        "decisions",
        "deliverables",
        "validation",
        "progress",
        "limitations",
        "next_steps",
        "git",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise ValueError(f"Résumé incomplet, champs manquants : {', '.join(missing)}")
    return data


def build_report(summary_path: Path, output_path: Path) -> None:
    """Build a styled A4 PDF report."""
    summary = _load_summary(summary_path)
    regular_font, bold_font = _register_fonts()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "AsteriaTitle",
        parent=styles["Title"],
        fontName=bold_font,
        fontSize=25,
        leading=30,
        textColor=NAVY,
        alignment=TA_CENTER,
        spaceAfter=8 * mm,
    )
    subtitle = ParagraphStyle(
        "AsteriaSubtitle",
        parent=styles["Normal"],
        fontName=regular_font,
        fontSize=11,
        leading=16,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceAfter=7 * mm,
    )
    heading = ParagraphStyle(
        "AsteriaHeading",
        parent=styles["Heading1"],
        fontName=bold_font,
        fontSize=15,
        leading=19,
        textColor=NAVY,
        spaceBefore=6 * mm,
        spaceAfter=3 * mm,
    )
    subheading = ParagraphStyle(
        "AsteriaSubheading",
        parent=styles["Heading2"],
        fontName=bold_font,
        fontSize=11,
        leading=14,
        textColor=TEAL,
        spaceBefore=4 * mm,
        spaceAfter=2 * mm,
    )
    body = ParagraphStyle(
        "AsteriaBody",
        parent=styles["BodyText"],
        fontName=regular_font,
        fontSize=9.2,
        leading=13.2,
        textColor=INK,
        alignment=TA_LEFT,
        spaceAfter=2.2 * mm,
    )
    small = ParagraphStyle(
        "AsteriaSmall",
        parent=body,
        fontSize=7.6,
        leading=10.2,
        spaceAfter=0,
    )
    bullet = ParagraphStyle(
        "AsteriaBullet",
        parent=body,
        leftIndent=5 * mm,
        firstLineIndent=-3.5 * mm,
        bulletIndent=1.5 * mm,
        spaceAfter=1.4 * mm,
    )
    callout = ParagraphStyle(
        "AsteriaCallout",
        parent=body,
        fontName=bold_font,
        fontSize=10,
        leading=15,
        textColor=NAVY,
        borderColor=TEAL,
        borderWidth=1,
        borderPadding=8,
        backColor=PALE,
        spaceBefore=2 * mm,
        spaceAfter=5 * mm,
    )

    def footer(canvas: Any, doc: Any) -> None:
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D7DEE8"))
        canvas.line(20 * mm, 14 * mm, 190 * mm, 14 * mm)
        canvas.setFont(regular_font, 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(20 * mm, 9 * mm, "Asteria Composites Lab — Rapport du premier jet")
        canvas.drawRightString(190 * mm, 9 * mm, f"Page {doc.page}")
        canvas.restoreState()

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title="Asteria Composites Lab — Rapport du premier jet",
        author="Asteria Composites Lab",
        subject="Architecture, implémentation et validation de la première livraison",
    )

    story: list[Any] = [
        Spacer(1, 17 * mm),
        Paragraph("ASTERIA COMPOSITES LAB", title),
        Paragraph(
            "Rapport d’architecture, d’implémentation et d’avancement — premier jet", subtitle
        ),
        Table(
            [
                [
                    Paragraph("<b>Version</b><br/>0.1.0", body),
                    Paragraph(
                        f"<b>Date</b><br/>{_safe(summary.get('generated_at', datetime.now(UTC).date()))}",
                        body,
                    ),
                    Paragraph(f"<b>Branche</b><br/>{_safe(summary['git']['branch'])}", body),
                ]
            ],
            colWidths=[55 * mm, 55 * mm, 60 * mm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D7DEE8")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D7DEE8")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            ),
        ),
        Spacer(1, 10 * mm),
        Paragraph(
            "Périmètre : architecture Phase 0 et jumeau numérique minimal Phase 1, exécutables "
            "de bout en bout avec données exclusivement synthétiques.",
            callout,
        ),
        Paragraph("0. Répartition du travail", heading),
        Paragraph(
            "Le travail a été départagé par frontières de fichiers et responsabilités techniques "
            "afin que les contributions puissent progresser en parallèle sans mélanger les contrats, "
            "le moteur et la documentation.",
            body,
        ),
    ]

    task_rows = [
        [
            Paragraph("<b>Responsable</b>", small),
            Paragraph("<b>Périmètre</b>", small),
            Paragraph("<b>Livrable principal</b>", small),
        ]
    ]
    for item in summary["task_division"]:
        task_rows.append(
            [
                Paragraph(_safe(item["owner"]), small),
                Paragraph(_safe(item["scope"]), small),
                Paragraph(_safe(item["output"]), small),
            ]
        )
    story.extend(
        [
            Table(
                task_rows,
                colWidths=[34 * mm, 69 * mm, 67 * mm],
                repeatRows=1,
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                        ("BACKGROUND", (0, 1), (-1, -1), WHITE),
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CFD7E3")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                ),
            ),
            Paragraph("1. Résumé exécutif", heading),
            Paragraph(_safe(summary["executive_summary"]), callout),
            Paragraph("2. Décisions structurantes", heading),
        ]
    )
    for item in summary["decisions"]:
        story.append(
            KeepTogether(
                [
                    Paragraph(_safe(item["title"]), subheading),
                    Paragraph(_safe(item["rationale"]), body),
                ]
            )
        )

    story.extend([PageBreak(), Paragraph("3. Livrables réalisés", heading)])
    deliverable_rows = [
        [
            Paragraph("<b>Bloc</b>", small),
            Paragraph("<b>État</b>", small),
            Paragraph("<b>Contenu</b>", small),
        ]
    ]
    for item in summary["deliverables"]:
        deliverable_rows.append(
            [
                Paragraph(_safe(item["name"]), small),
                Paragraph(_safe(item["status"]), small),
                Paragraph(_safe(item["details"]), small),
            ]
        )
    story.extend(
        [
            Table(
                deliverable_rows,
                colWidths=[42 * mm, 27 * mm, 101 * mm],
                repeatRows=1,
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
                        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CFD7E3")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                ),
            ),
            Paragraph("4. Validation et qualité", heading),
        ]
    )
    validation_rows = [
        [
            Paragraph("<b>Contrôle</b>", small),
            Paragraph("<b>Résultat</b>", small),
            Paragraph("<b>Observation</b>", small),
        ]
    ]
    for item in summary["validation"]:
        validation_rows.append(
            [
                Paragraph(_safe(item["check"]), small),
                Paragraph(_safe(item["result"]), small),
                Paragraph(_safe(item["evidence"]), small),
            ]
        )
    story.append(
        Table(
            validation_rows,
            colWidths=[48 * mm, 31 * mm, 91 * mm],
            repeatRows=1,
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), TEAL),
                    ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PALE]),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#BFCFD3")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            ),
        )
    )

    story.extend([Paragraph("5. Avancement du programme", heading)])
    progress_rows = [
        [
            Paragraph("<b>Phase</b>", small),
            Paragraph("<b>Avancement</b>", small),
            Paragraph("<b>Commentaire</b>", small),
        ]
    ]
    for item in summary["progress"]:
        progress_rows.append(
            [
                Paragraph(_safe(item["phase"]), small),
                Paragraph(_safe(item["completion"]), small),
                Paragraph(_safe(item["comment"]), small),
            ]
        )
    story.append(
        Table(
            progress_rows,
            colWidths=[45 * mm, 30 * mm, 95 * mm],
            repeatRows=1,
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CFD7E3")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            ),
        )
    )

    story.extend(
        [
            PageBreak(),
            Paragraph("6. Traçabilité Git", heading),
            Paragraph(
                f"<b>Dépôt :</b> {_safe(summary['git']['repository'])}<br/>"
                f"<b>Branche :</b> {_safe(summary['git']['branch'])}<br/>"
                f"<b>Commits du premier jet :</b> {_safe(summary['git']['commits'])}<br/>"
                f"<b>Pull Request :</b> {_safe(summary['git']['pull_request'])}",
                callout,
            ),
            Paragraph("7. Limites connues", heading),
        ]
    )
    for item in summary["limitations"]:
        story.append(Paragraph(f"• {_safe(item)}", bullet))

    story.append(Paragraph("8. Prochaines étapes recommandées", heading))
    for index, item in enumerate(summary["next_steps"], start=1):
        story.append(Paragraph(f"{index}. {_safe(item)}", bullet))

    story.extend(
        [
            Spacer(1, 6 * mm),
            Paragraph(
                "Conclusion — Le premier jet fournit un socle logiciel cohérent et vérifiable. "
                "Il démontre l’intégration complète configuration → validation → simulation → événements "
                "→ KPI → exports → figures, tout en maintenant une séparation nette entre données "
                "synthétiques, hypothèses d’ingénierie et futures méthodes scientifiques.",
                callout,
            ),
        ]
    )
    document.build(story, onFirstPage=footer, onLaterPages=footer)


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("reports/first_draft_summary.json"),
        help="JSON summary used to populate the report.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/Asteria_Composites_Lab_Rapport_Premier_Jet.pdf"),
        help="Destination PDF path.",
    )
    args = parser.parse_args()
    build_report(args.summary, args.output)


if __name__ == "__main__":
    main()
