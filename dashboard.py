import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------ تنظیمات صفحه ------------------
st.set_page_config(page_title="📊 سامانه کارنامه", layout="wide")

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
        .login-button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
        }
        </style>
        <div class="login-card">
            <div class="login-title">🔑 ورود به سامانه کارنامه</div>
        """,
        unsafe_allow_html=True,
    )

    password_input = st.text_input("رمز ورود", type="password")
    if st.button("ورود", key="login_button"):
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

else:
    st.info("برای شروع، فایل اکسل نمرات را بارگذاری کنید.")
