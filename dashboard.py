import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# ------------------ تنظیمات اولیه ------------------
st.set_page_config(page_title="کارنامه دانش‌آموز", layout="wide")

# تعریف فونت فارسی برای PDF
pdfmetrics.registerFont(TTFont("Vazir", "Vazir.ttf"))

# پسورد ورود
PASSWORD = "1234"

# ------------------ صفحه ورود ------------------
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

# ------------------ داده‌ها ------------------
uploaded_file = st.file_uploader("📂 فایل اکسل نمرات را بارگذاری کنید", type=["xlsx"])

if uploaded_file:
    scores_long = pd.read_excel(uploaded_file)

    # اطمینان از عددی بودن نمره
    scores_long["نمره"] = pd.to_numeric(scores_long["نمره"], errors="coerce")
    scores_long = scores_long.dropna(subset=["نمره"])

    # میانگین هر دانش‌آموز
    overall_avg = scores_long.groupby("نام دانش آموز")["نمره"].mean().reset_index()

    # ------------------ نمایش ------------------
    st.subheader("📊 نمودار نمرات")
    fig = px.bar(overall_avg, x="نام دانش آموز", y="نمره", color="نمره",
                 color_continuous_scale="Blues", title="میانگین نمرات دانش‌آموزان")
    st.plotly_chart(fig, use_container_width=True)

    # جدول کارنامه
    st.subheader("📑 کارنامه کلی")
    st.dataframe(overall_avg, use_container_width=True)

    # ------------------ PDF ------------------
    def generate_pdf(df):
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        c.setFont("Vazir", 14)

        width, height = A4
        c.drawString(200, height - 50, "📖 کارنامه دانش‌آموزان")

        y = height - 100
        for idx, row in df.iterrows():
            text = f"{row['نام دانش آموز']} : {round(row['نمره'], 2)}"
            c.drawString(100, y, text)
            y -= 30

        c.save()
        buffer.seek(0)
        return buffer

    pdf_buffer = generate_pdf(overall_avg)
    st.download_button("⬇️ دانلود کارنامه PDF", data=pdf_buffer,
                       file_name="report.pdf", mime="application/pdf")

else:
    st.info("برای شروع، فایل اکسل نمرات را بارگذاری کنید.")
