import streamlit as st
import pandas as pd
import plotly.express as px
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ------------------ تنظیمات صفحه ------------------
st.set_page_config(page_title="📊 سامانه کارنامه", layout="wide")

# ------------------ ثبت فونت فارسی ------------------
pdfmetrics.registerFont(TTFont("Vazir", "fonts/Vazir.ttf"))

# ------------------ ورود کاربر ------------------
PASSWORD = "1234"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown(
        """
        <style>
        .login-card {
            max-width: 400px;
            margin: auto;
            margin-top: 150px;
            padding: 30px;
            border-radius: 15px;
            background: linear-gradient(135deg, #dfe9f3 0%, #ffffff 100%);
            box-shadow: 0px 8px 20px rgba(0,0,0,0.15);
            text-align: center;
        }
        .login-title {
            font-size: 22px;
            font-weight: bold;
            margin-bottom: 20px;
            color: #2c3e50;
        }
        </style>
        <div class="login-card">
            <div class="login-title">🔑 ورود به سامانه کارنامه</div>
        """,
        unsafe_allow_html=True,
    )

    password_input = st.text_input("رمز ورود", type="password")
    if st.button("ورود"):
        if password_input == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ رمز اشتباه است")

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ------------------ بارگذاری فایل اکسل ------------------
uploaded_file = st.file_uploader("📂 فایل اکسل نمرات را بارگذاری کنید", type=["xlsx"])

if uploaded_file:
    scores_long = pd.read_excel(uploaded_file)

    # تبدیل ستون نمره به عدد و حذف غیرعددی‌ها
    scores_long["نمره"] = pd.to_numeric(scores_long["نمره"], errors="coerce")
    scores_long = scores_long.dropna(subset=["نمره"])

    # میانگین هر دانش‌آموز
    overall_avg = scores_long.groupby("نام دانش آموز")["نمره"].mean().reset_index()

    # ------------------ نمودار میانگین ------------------
    st.subheader("📊 نمودار میانگین نمرات دانش‌آموزان")
    fig = px.bar(overall_avg, x="نام دانش آموز", y="نمره", color="نمره",
                 color_continuous_scale="Blues", title="میانگین نمرات دانش‌آموزان")
    st.plotly_chart(fig, use_container_width=True)

    # ------------------ جدول کارنامه ------------------
    st.subheader("📑 کارنامه کلی")
    st.dataframe(overall_avg.style.background_gradient(subset=["نمره"], cmap="Blues"), use_container_width=True)

    # ------------------ تابع تولید PDF ------------------
    def generate_student_pdf(student_name, student_data, status_map):
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # عنوان کارنامه
        c.setFont("Vazir", 18)
        c.drawCentredString(width / 2, height - 50, f"کارنامه‌ی {student_name}")

        c.setFont("Vazir", 12)
        y = height - 100

        # نمایش نمره‌ها و وضعیت کیفی
        for _, row in student_data.iterrows():
            lesson = row["درس"]
            score = row["نمره"]
            status = status_map.get(score, "نامشخص")
            text_line = f"درس: {lesson}   |   نمره: {score}   |   وضعیت: {status}"
            c.drawRightString(width - 50, y, text_line)
            y -= 25
            if y < 50:
                c.showPage()
                c.setFont("Vazir", 12)
                y = height - 50

        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer

    # ------------------ دانلود PDF ------------------
    # تعریف وضعیت عددی → متنی
    status_map = {1: "نیاز به تلاش بیشتر", 2: "قابل قبول", 3: "خوب", 4: "خیلی خوب"}

    st.subheader("⬇️ دانلود کارنامه PDF")
    for student in overall_avg["نام دانش آموز"]:
        student_data = scores_long[scores_long["نام دانش آموز"] == student]
        pdf_buffer = generate_student_pdf(student, student_data, status_map)
        st.download_button(f"دانلود PDF {student}", data=pdf_buffer,
                           file_name=f"{student}_report.pdf", mime="application/pdf")

else:
    st.info("برای شروع، فایل اکسل نمرات را بارگذاری کنید.")
