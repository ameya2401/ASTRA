"""
scripts/create_survey_images.py - Generates visual assets for the Google Form survey.
Creates:
  1. survey_assets/google_forms_header_banner.png (1600x400)
  2. survey_assets/question_scenario_diff.png (1000x440)
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "survey_assets"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FONT_SANS_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_SANS = "C:/Windows/Fonts/segoeui.ttf"
FONT_MONO = "C:/Windows/Fonts/consola.ttf"
FONT_MONO_BOLD = "C:/Windows/Fonts/consolab.ttf"


def generate_header_banner():
    width, height = 1600, 400
    img = Image.new("RGBA", (width, height), (13, 17, 23, 255))
    draw = ImageDraw.Draw(img)

    # Top accent line (Vercel mesh style: Cyan -> Blue -> Violet)
    for x in range(width):
        ratio = x / width
        if ratio < 0.33:
            r = int(0 + (0 - 0) * (ratio / 0.33))
            g = int(223 + (124 - 223) * (ratio / 0.33))
            b = int(216 + (240 - 216) * (ratio / 0.33))
        elif ratio < 0.66:
            norm = (ratio - 0.33) / 0.33
            r = int(0 + (121 - 0) * norm)
            g = int(124 + (40 - 124) * norm)
            b = int(240 + (202 - 240) * norm)
        else:
            norm = (ratio - 0.66) / 0.34
            r = int(121 + (255 - 121) * norm)
            g = int(40 + (0 - 40) * norm)
            b = int(202 + (128 - 202) * norm)
        draw.line([(x, 0), (x, 4)], fill=(r, g, b, 255))

    # Subtle ambient gradient glow on the right
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    for rad in range(350, 0, -10):
        alpha = int(25 * (1 - rad / 350))
        glow_draw.ellipse(
            [1200 - rad, 200 - rad, 1200 + rad, 200 + rad],
            fill=(0, 112, 243, alpha)
        )
    img = Image.alpha_composite(img, glow)
    draw = ImageDraw.Draw(img)

    # Fonts
    font_badge = ImageFont.truetype(FONT_MONO_BOLD, 18)
    font_title = ImageFont.truetype(FONT_SANS_BOLD, 46)
    font_sub = ImageFont.truetype(FONT_SANS, 22)
    font_tags = ImageFont.truetype(FONT_MONO, 16)

    # Category Pill
    pill_text = "ASTRA ACADEMIC RESEARCH STUDY"
    pill_w = 340
    pill_h = 34
    draw.rounded_rectangle([90, 60, 90 + pill_w, 60 + pill_h], radius=17, fill=(26, 33, 44, 255), outline=(48, 54, 61, 255))
    draw.text((115, 66), pill_text, font=font_badge, fill=(88, 166, 255, 255))

    # Main Headline
    draw.text(
        (90, 115),
        "Developer Survey: Code Quality & AI Pull Requests",
        font=font_title,
        fill=(240, 246, 252, 255)
    )

    # Subtitle
    draw.text(
        (90, 185),
        "Investigating AI Coding Agents, CI Evasion, and Human Review Bottlenecks",
        font=font_sub,
        fill=(139, 148, 158, 255)
    )

    # Divider hairline
    draw.line([(90, 240), (width - 90, 240)], fill=(33, 38, 45, 255), width=1)

    # Bottom Spec Pillars
    pillars = [
        ("•", (46, 160, 67, 255), "Concrete Syntax Differencing (AST)"),
        ("•", (88, 166, 255, 255), "Semantic Intent-to-Diff Alignment"),
        ("•", (210, 153, 34, 255), "Test Churn & Assertion Protection"),
        ("•", (187, 128, 179, 255), "Platt-Calibrated Risk Stratification")
    ]
    cur_x = 90
    for dot, dot_col, label in pillars:
        draw.text((cur_x, 270), dot, font=font_tags, fill=dot_col)
        draw.text((cur_x + 18, 270), label, font=font_tags, fill=(201, 209, 217, 255))
        cur_x += 350

    output_path = OUTPUT_DIR / "google_forms_header_banner.png"
    img.save(output_path, "PNG")
    print(f"Header banner saved: {output_path}")


def generate_scenario_diff():
    width, height = 1000, 440
    img = Image.new("RGBA", (width, height), (22, 27, 34, 255))
    draw = ImageDraw.Draw(img)

    # Outer border
    draw.rounded_rectangle([0, 0, width - 1, height - 1], radius=10, outline=(48, 54, 61, 255), width=1)

    # Title Bar
    draw.rounded_rectangle([0, 0, width - 1, 46], radius=10, fill=(33, 38, 45, 255))
    draw.rectangle([0, 36, width - 1, 46], fill=(33, 38, 45, 255))
    draw.line([(0, 46), (width, 46)], fill=(48, 54, 61, 255), width=1)

    # Window dots
    draw.ellipse([16, 17, 28, 29], fill=(248, 81, 73, 255))
    draw.ellipse([36, 17, 48, 29], fill=(227, 179, 65, 255))
    draw.ellipse([56, 17, 68, 29], fill=(46, 160, 67, 255))

    font_ui = ImageFont.truetype(FONT_SANS, 14)
    font_ui_bold = ImageFont.truetype(FONT_SANS_BOLD, 14)
    font_code = ImageFont.truetype(FONT_MONO, 15)
    font_code_bold = ImageFont.truetype(FONT_MONO_BOLD, 15)

    # File title
    draw.text((85, 14), "tests/test_session_timeout.py — Pull Request #42", font=font_ui, fill=(201, 209, 217, 255))

    # CI Status Pill on Right
    ci_box_x = width - 260
    draw.rounded_rectangle([ci_box_x, 10, width - 16, 36], radius=13, fill=(35, 134, 54, 220))
    draw.text((ci_box_x + 12, 13), "✓ All checks have passed", font=font_ui_bold, fill=(255, 255, 255, 255))

    # Diff Header bar
    draw.rectangle([0, 47, width - 1, 80], fill=(22, 27, 34, 255))
    draw.text((24, 54), "@@ -24,8 +24,2 @@ def test_session_timeout():", font=font_code, fill=(110, 118, 129, 255))

    # Code lines
    diff_lines = [
        (" ", "    session = AsyncSessionHandler(timeout_seconds=5)", (201, 209, 217, 255), None),
        ("-", "    with pytest.raises(TimeoutError):", (248, 81, 73, 255), (103, 6, 15, 60)),
        ("-", "        session.handle_timeout('expired_token')", (248, 81, 73, 255), (103, 6, 15, 60)),
        ("-", "    assert session.is_terminated() is True", (248, 81, 73, 255), (103, 6, 15, 60)),
        ("-", "    assert session.cleanup_called is True", (248, 81, 73, 255), (103, 6, 15, 60)),
        ("+", "    pass  # AI agent deleted failing tests to force CI pass!", (63, 185, 80, 255), (26, 79, 39, 60)),
        (" ", "    return True", (201, 209, 217, 255), None),
    ]

    y_pos = 85
    line_h = 32
    for prefix, content, text_col, bg_col in diff_lines:
        if bg_col:
            draw.rectangle([0, y_pos, width - 1, y_pos + line_h], fill=bg_col)
        draw.text((24, y_pos + 6), prefix, font=font_code_bold, fill=text_col)
        draw.text((50, y_pos + 6), content, font=font_code, fill=text_col)
        y_pos += line_h

    # Bottom Warning Callout Bar
    draw.rounded_rectangle([20, height - 70, width - 20, height - 20], radius=8, fill=(33, 38, 45, 255), outline=(227, 179, 65, 180), width=1)
    draw.text(
        (35, height - 58),
        "⚠️  The 'Green CI Mirage': CI reports all tests passed, but 4 critical assertions were deleted.",
        font=font_ui_bold,
        fill=(227, 179, 65, 255)
    )

    output_path = OUTPUT_DIR / "question_scenario_diff.png"
    img.save(output_path, "PNG")
    print(f"Scenario diff graphic saved: {output_path}")


if __name__ == "__main__":
    generate_header_banner()
    generate_scenario_diff()

