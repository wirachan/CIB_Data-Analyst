"""
Streamlit application for extracting, analyzing, and reporting TPO crime statistics
from uploaded images using Google Gemini Vision API.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Tuple

import google.generativeai as genai
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image as RLImage,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


MODEL_ID = "gemini-1.5-flash"
THAI_FONT_FILE = "THSarabunNew.ttf"
DEFAULT_FONT = "Helvetica"

ANALYSIS_PROMPT = """
วิเคราะห์รูปภาพสถิติคดีออนไลน์ TPO และแยกข้อมูลดังนี้:

1. ข้อมูลหลัก (Key Metrics):
   - มูลค่าความเสียหาย (บาท)
   - จำนวนคดีทั้งหมด (เรื่อง)
   - AOC, Online, Walk In

2. ตารางรายละเอียดคดีครบทุกแถว:
   - ประเภทคดี
   - จำนวน (เรื่อง)
   - สัดส่วน (% ของจำนวนเรื่อง)
   - มูลค่าความเสียหาย (บาท)

3. วันที่ของข้อมูล (เช่น 02/11/2025 - 08/11/2025) และ label สัปดาห์ หากมี

รูปแบบผลลัพธ์: JSON เท่านั้น โดยใช้โครงสร้างต่อไปนี้
{
  "date_range": "02/11/2025 - 08/11/2025",
  "week_label": "สัปดาห์ที่ 1",
  "key_metrics": {
    "total_damage": 564614785,
    "total_cases": 7895,
    "aoc": 6236,
    "online": 1229,
    "walk_in": 430
  },
  "crime_types": [
    {
      "name": "หลอกลวงโอนเงินเข้าบัญชีเพื่อซื้อหรือจ้างสินค้าหรือบริการ",
      "cases": 1278,
      "cases_percent": 16.19,
      "damage": 172120523,
      "damage_percent": 30.48
    }
  ]
}

อย่าเพิ่มข้อความอื่นนอกจาก JSON.
"""

SAMPLE_DATA: List[Dict[str, Any]] = [
    {
        "date_range": "02/11/2025 - 08/11/2025",
        "week_label": "สัปดาห์ที่ 1",
        "key_metrics": {
            "total_damage": 564_614_785,
            "total_cases": 7_895,
            "aoc": 6_236,
            "online": 1_229,
            "walk_in": 430,
        },
        "crime_types": [
            {
                "name": "หลอกลวงโอนเงินเข้าบัญชีเพื่อซื้อหรือจ้างสินค้าหรือบริการ",
                "cases": 1_278,
                "cases_percent": 16.19,
                "damage": 172_120_523,
                "damage_percent": 30.48,
            },
            {
                "name": "หลอกให้โอนเงินผ่านแอปพลิเคชันปลอม",
                "cases": 1_012,
                "cases_percent": 12.82,
                "damage": 102_456_789,
                "damage_percent": 18.15,
            },
            {
                "name": "ปลอมเป็นเจ้าหน้าที่รัฐเพื่อข่มขู่เรียกทรัพย์",
                "cases": 865,
                "cases_percent": 10.96,
                "damage": 87_654_321,
                "damage_percent": 15.52,
            },
            {
                "name": "ปลอมเป็นลูกหลานขอยืมเงินด่วน",
                "cases": 544,
                "cases_percent": 6.89,
                "damage": 41_256_985,
                "damage_percent": 7.31,
            },
            {
                "name": "เว็บไซต์ปลอมแปลงการลงทุนและคริปโต",
                "cases": 396,
                "cases_percent": 5.02,
                "damage": 98_745_632,
                "damage_percent": 17.49,
            },
        ],
    },
    {
        "date_range": "09/11/2025 - 15/11/2025",
        "week_label": "สัปดาห์ที่ 2",
        "key_metrics": {
            "total_damage": 612_789_543,
            "total_cases": 8_104,
            "aoc": 6_410,
            "online": 1_280,
            "walk_in": 414,
        },
        "crime_types": [
            {
                "name": "หลอกโอนเงินเข้าบัญชีซื้อหรือจ้างบริการ",
                "cases": 1_320,
                "cases_percent": 16.29,
                "damage": 182_220_123,
                "damage_percent": 29.73,
            },
            {
                "name": "หลอกให้โอนเงินผ่านแอปปลอม",
                "cases": 1_045,
                "cases_percent": 12.90,
                "damage": 105_987_123,
                "damage_percent": 17.30,
            },
            {
                "name": "ปลอมเป็นเจ้าหน้าที่รัฐ",
                "cases": 902,
                "cases_percent": 11.13,
                "damage": 95_000_000,
                "damage_percent": 15.49,
            },
            {
                "name": "แชร์ลูกโซ่ออนไลน์",
                "cases": 610,
                "cases_percent": 7.52,
                "damage": 88_450_000,
                "damage_percent": 14.43,
            },
            {
                "name": "เว็บไซต์ปลอมแปลงการลงทุน",
                "cases": 430,
                "cases_percent": 5.30,
                "damage": 141_132_297,
                "damage_percent": 23.06,
            },
        ],
    },
]


# --- Streamlit configuration -------------------------------------------------
st.set_page_config(
    page_title="TPO Crime Analysis",
    page_icon="📊",
    layout="wide",
)


@st.cache_resource(show_spinner=False)
def load_font(font_file: str = THAI_FONT_FILE) -> str:
    """Register Thai font for ReportLab if available."""
    if not os.path.exists(font_file):
        return DEFAULT_FONT

    try:
        pdfmetrics.registerFont(TTFont("THSarabunNew", font_file))
        return "THSarabunNew"
    except Exception as exc:  # pragma: no cover - defensive
        st.warning(f"ไม่สามารถโหลดฟอนต์ไทยได้: {exc}")
        return DEFAULT_FONT


def configure_gemini() -> bool:
    """Configure Gemini client from secrets/env."""
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.warning("ยังไม่ได้ตั้งค่า GEMINI_API_KEY โปรดอัปเดต .streamlit/secrets.toml")
        return False
    genai.configure(api_key=api_key)
    return True


def clean_json_text(text: str) -> str:
    """Remove markdown fences and stray characters around JSON."""
    cleaned = text.strip()
    fences = ("```json", "```JSON", "```")
    for fence in fences:
        if cleaned.startswith(fence):
            cleaned = cleaned[len(fence) :].strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()
    return cleaned


def parse_json_response(text: str) -> Dict[str, Any]:
    cleaned = clean_json_text(text)
    return json.loads(cleaned)


def extract_data_from_images(uploaded_files: List[Any]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Send each uploaded image to Gemini and parse JSON responses."""
    if not uploaded_files:
        return [], []

    if not configure_gemini():
        return [], ["ยังไม่ได้ตั้งค่า GEMINI_API_KEY ใน secrets หรือ environment"]
    model = genai.GenerativeModel(MODEL_ID)

    data_list: List[Dict[str, Any]] = []
    errors: List[str] = []

    progress = st.progress(0, text="กำลังประมวลผลภาพ...")

    for idx, uploaded_file in enumerate(uploaded_files, start=1):
        try:
            image = Image.open(uploaded_file)
            response = model.generate_content(
                [ANALYSIS_PROMPT, image],
                request_options={"timeout": 120},
            )

            if not response.text:
                raise ValueError("ไม่ได้รับข้อความตอบกลับจากโมเดล")

            parsed = parse_json_response(response.text)
            data_list.append(parsed)
        except Exception as exc:
            errors.append(f"รูปที่ {idx}: {exc}")

        progress.progress(idx / len(uploaded_files))

    progress.empty()
    return data_list, errors


def analyze_trends(data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize metrics across weeks and highlight trends."""
    if not data_list:
        return {}

    weeks_comparison = []
    for data in data_list:
        metrics = data.get("key_metrics", {})
        weeks_comparison.append(
            {
                "ช่วงเวลา": data.get("date_range", data.get("week_label", "N/A")),
                "จำนวนคดี": metrics.get("total_cases", 0),
                "มูลค่าความเสียหาย": metrics.get("total_damage", 0),
            }
        )

    trend_text = "ยังไม่มีข้อมูลเพียงพอสำหรับเปรียบเทียบแนวโน้ม"
    if len(data_list) >= 2:
        first = data_list[0]["key_metrics"]
        last = data_list[-1]["key_metrics"]

        def pct_change(new: float, old: float) -> float:
            return ((new - old) / old) * 100 if old else 0.0

        case_change = pct_change(last.get("total_cases", 0), first.get("total_cases", 0))
        damage_change = pct_change(last.get("total_damage", 0), first.get("total_damage", 0))

        case_status = "เพิ่มขึ้น" if case_change >= 0 else "ลดลง"
        damage_status = "เพิ่มขึ้น" if damage_change >= 0 else "ลดลง"
        trend_text = (
            f"📈 จำนวนคดี {case_status} {abs(case_change):.2f}% | "
            f"มูลค่าความเสียหาย {damage_status} {abs(damage_change):.2f}%"
        )

    return {
        "weeks_comparison": weeks_comparison,
        "trend_text": trend_text,
        "top_cases": aggregate_crime_stats(data_list, key="cases"),
        "top_damage": aggregate_crime_stats(data_list, key="damage"),
    }


def aggregate_crime_stats(data_list: List[Dict[str, Any]], key: str) -> List[Dict[str, Any]]:
    aggregated: Dict[str, Dict[str, float]] = {}
    for data in data_list:
        for crime in data.get("crime_types", []):
            name = crime.get("name", "N/A")
            if name not in aggregated:
                aggregated[name] = {"cases": 0.0, "damage": 0.0}
            aggregated[name]["cases"] += crime.get("cases", 0)
            aggregated[name]["damage"] += crime.get("damage", 0)

    sorted_items = sorted(
        ({**{"name": name}, **values} for name, values in aggregated.items()),
        key=lambda item: item[key],
        reverse=True,
    )
    return sorted_items[:5]


def create_visualizations(
    data_list: List[Dict[str, Any]],
    analysis: Dict[str, Any],
) -> Dict[str, go.Figure]:
    if not data_list:
        return {}

    charts: Dict[str, go.Figure] = {}

    weeks = [data.get("week_label") or data.get("date_range") for data in data_list]
    total_cases = [data["key_metrics"].get("total_cases", 0) for data in data_list]
    total_damage = [data["key_metrics"].get("total_damage", 0) / 1_000_000 for data in data_list]

    fig1 = go.Figure()
    fig1.add_bar(x=weeks, y=total_cases, name="จำนวนคดี", marker_color="#3b82f6")
    fig1.add_trace(
        go.Scatter(
            x=weeks,
            y=total_damage,
            name="มูลค่าความเสียหาย (ล้านบาท)",
            mode="lines+markers",
            yaxis="y2",
            marker_color="#ef4444",
        )
    )
    fig1.update_layout(
        title="เปรียบเทียบจำนวนคดีและมูลค่า",
        yaxis=dict(title="จำนวนคดี (เรื่อง)"),
        yaxis2=dict(
            title="มูลค่าความเสียหาย (ล้านบาท)",
            overlaying="y",
            side="right",
        ),
        hovermode="x unified",
    )
    charts["key_metrics"] = fig1

    top_cases = analysis.get("top_cases", [])
    if top_cases:
        fig2 = px.pie(
            names=[c["name"] for c in top_cases],
            values=[c["cases"] for c in top_cases],
            title="5 อันดับคดีตามจำนวนเรื่อง",
            hole=0.4,
        )
        fig2.update_layout(height=500)
        charts["top_cases"] = fig2

        fig3 = px.pie(
            names=[c["name"] for c in top_cases],
            values=[c["damage"] for c in top_cases],
            title="5 อันดับคดีตามความเสียหาย",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Reds_r,
        )
        fig3.update_layout(height=500)
        charts["top_damage"] = fig3

        avg_damage = [
            (c["damage"] / c["cases"]) if c["cases"] else 0 for c in top_cases
        ]
        fig4 = go.Figure(
            go.Bar(
                x=avg_damage,
                y=[c["name"] for c in top_cases],
                orientation="h",
                text=[f"{value:,.0f}" for value in avg_damage],
                textposition="auto",
                marker_color="#10b981",
            )
        )
        fig4.update_layout(
            title="มูลค่าความเสียหายเฉลี่ยต่อคดี",
            xaxis_title="บาทต่อคดี",
            height=450,
        )
        charts["avg_damage"] = fig4

    return charts


def render_data_tables(data_list: List[Dict[str, Any]]):
    for idx, data in enumerate(data_list, start=1):
        st.subheader(f"ช่วงที่ {idx}: {data.get('date_range', 'N/A')}")
        metrics = data.get("key_metrics", {})
        cols = st.columns(4)
        cols[0].metric("จำนวนคดี", f"{metrics.get('total_cases', 0):,}")
        cols[1].metric("ความเสียหาย (บาท)", f"{metrics.get('total_damage', 0):,}")
        cols[2].metric("AOC", f"{metrics.get('aoc', 0):,}")
        cols[3].metric("Online / Walk-In", f"{metrics.get('online', 0):,} / {metrics.get('walk_in', 0):,}")

        crime_df = pd.DataFrame(data.get("crime_types", []))
        if not crime_df.empty:
            st.dataframe(crime_df, use_container_width=True)
        st.divider()


def save_fig_to_image(fig: go.Figure) -> BytesIO:
    buffer = BytesIO()
    buffer.write(fig.to_image(format="png", width=900, height=500))
    buffer.seek(0)
    return buffer


def generate_pdf_report(
    data_list: List[Dict[str, Any]],
    analysis: Dict[str, Any],
    charts: Dict[str, go.Figure],
    font_name: str,
) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=24,
    )

    styles = getSampleStyleSheet()
    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading1"],
        fontName=font_name,
        fontSize=20,
        textColor=colors.HexColor("#1e40af"),
        spaceAfter=12,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=12,
        leading=16,
    )

    story = []
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("รายงานการวิเคราะห์ข้อมูลคดีออนไลน์ TPO", heading_style))
    story.append(
        Paragraph(
            f"จัดทำเมื่อ: {datetime.now().strftime('%d/%m/%Y %H:%M น.')}",
            body_style,
        )
    )
    story.append(PageBreak())

    for idx, data in enumerate(data_list, start=1):
        story.append(Paragraph(f"ช่วงที่ {idx}: {data.get('date_range','N/A')}", heading_style))
        metrics = data.get("key_metrics", {})
        table_data = [
            ["ตัวชี้วัด", "ค่า"],
            ["จำนวนคดีทั้งหมด", f"{metrics.get('total_cases', 0):,} เรื่อง"],
            ["มูลค่าความเสียหาย", f"{metrics.get('total_damage', 0):,} บาท"],
            ["AOC", f"{metrics.get('aoc', 0):,}"],
            ["Online", f"{metrics.get('online', 0):,}"],
            ["Walk-In", f"{metrics.get('walk_in', 0):,}"],
        ]
        table = Table(table_data, colWidths=[2.5 * inch, 3 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3b82f6")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, -1), font_name),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph("การวิเคราะห์แนวโน้ม", heading_style))
    story.append(Paragraph(analysis.get("trend_text", ""), body_style))
    story.append(Spacer(1, 0.3 * inch))

    for name, fig in charts.items():
        try:
            img_buffer = save_fig_to_image(fig)
            rl_img = RLImage(img_buffer, width=6 * inch, height=3.5 * inch)
            story.append(rl_img)
            story.append(Spacer(1, 0.2 * inch))
        except Exception as exc:  # pragma: no cover - depends on kaleido
            story.append(Paragraph(f"ไม่สามารถแปลงกราฟ {name}: {exc}", body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer


def render_sidebar() -> Tuple[List[Any], bool]:
    with st.sidebar:
        st.header("⚙️ การตั้งค่า")
        uploaded_files = st.file_uploader(
            "อัปโหลดรูปภาพสถิติ (รองรับหลายไฟล์)",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
        )
        uploaded_files = uploaded_files or []
        use_sample = st.toggle("ใช้ข้อมูลตัวอย่างแทน", value=not uploaded_files)

        if uploaded_files:
            st.success(f"อัปโหลดแล้ว {len(uploaded_files)} ไฟล์")
            for idx, file in enumerate(uploaded_files, start=1):
                st.image(file, caption=f"รูปที่ {idx}", use_column_width=True)

        st.markdown("---")
        st.markdown(
            """
            **คำแนะนำการใช้งาน**

            1. เตรียมภาพกราฟสถิติที่อ่านชัด
            2. กด "เริ่มวิเคราะห์" เพื่อเรียก Gemini
            3. ดาวน์โหลดรายงาน PDF ได้ทันที
            """
        )
        return uploaded_files, use_sample


def main() -> None:
    st.title("📊 ระบบวิเคราะห์ข้อมูล TPO Crime Statistics")
    st.markdown("วิเคราะห์ภาพสถิติคดีออนไลน์แบบอัตโนมัติ พร้อมกราฟและรายงาน PDF")

    font_name = load_font()
    uploaded_files, use_sample = render_sidebar()

    start_button = st.button("🚀 เริ่มวิเคราะห์", type="primary")

    if "tpo_data" not in st.session_state:
        st.session_state["tpo_data"] = []

    data_list: List[Dict[str, Any]] = st.session_state["tpo_data"]
    if start_button:
        with st.spinner("กำลังประมวลผลข้อมูล..."):
            if use_sample:
                data_list = SAMPLE_DATA
            else:
                data_list, errors = extract_data_from_images(uploaded_files)
                for err in errors:
                    st.error(err)

            if not data_list:
                st.warning("ยังไม่ได้รับข้อมูลจากภาพ กรุณาตรวจสอบอีกครั้ง")
                return
            st.session_state["tpo_data"] = data_list

    if data_list:
        analysis = analyze_trends(data_list)
        st.success("✅ วิเคราะห์ข้อมูลเสร็จสมบูรณ์")
        st.markdown(f"**แนวโน้มโดยรวม:** {analysis.get('trend_text','')}")

        render_data_tables(data_list)

        st.header("📈 กราฟวิเคราะห์")
        charts = create_visualizations(data_list, analysis)
        for fig in charts.values():
            st.plotly_chart(fig, use_container_width=True)

        st.header("📥 ดาวน์โหลดรายงาน")
        with st.spinner("กำลังสร้าง PDF..."):
            pdf_buffer = generate_pdf_report(data_list, analysis, charts, font_name)
            st.download_button(
                label="⬇️ ดาวน์โหลดรายงาน PDF",
                data=pdf_buffer,
                file_name=f"TPO_Crime_Analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
            )

        with st.expander("📦 ดูข้อมูล JSON"):
            st.json(data_list)
    else:
        st.info("👈 กรุณาอัปโหลดรูปภาพ หรือเลือกใช้ข้อมูลตัวอย่างจากแถบด้านซ้าย")


if __name__ == "__main__":
    main()
