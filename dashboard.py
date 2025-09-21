import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------ تنظیمات صفحه ------------------
st.set_page_config(page_title="📊 مدیریت عملکرد کلاس", layout="wide")

# ------------------ داده کاربران ------------------
# در فایل users.xlsx ذخیره شده
# ستون‌ها: نام کاربر | نقش | رمز ورود
users_df = pd.read_excel("data/users.xlsx")
users_df.columns = users_df.columns.str.strip()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.session_state.user_name = None

# ------------------ ورود با نقش ------------------
if not st.session_state.authenticated:
    st.markdown(
        """
        <style>
        .login-card {
            max-width: 450px;
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
            <div class="login-title">📊 مدیریت عملکرد کلاس</div>
        """,
        unsafe_allow_html=True,
    )

    role = st.selectbox("نقش خود را انتخاب کنید:", ["والد", "آموزگار", "مدیر"])
    user_name_input = st.text_input("نام کاربری")
    password_input = st.text_input("رمز ورود", type="password")

    if st.button("ورود"):
        valid_user = users_df[(users_df["نقش"] == role) & 
                              (users_df["نام کاربر"] == user_name_input) & 
                              (users_df["رمز ورود"] == password_input)]
        if not valid_user.empty:
            st.session_state.authenticated = True
            st.session_state.user_role = role
            st.session_state.user_name = user_name_input
            st.success(f"✅ خوش آمدید {user_name_input} عزیز! شما به عنوان {role} وارد شدید.")
            st.rerun()
        else:
            st.error("❌ نام کاربری، نقش یا رمز اشتباه است")

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ------------------ بارگذاری فایل اکسل ------------------
uploaded_file = st.file_uploader("📂 فایل اکسل نمرات را بارگذاری کنید", type=["xlsx"])

if uploaded_file:
    scores_long = pd.read_excel(uploaded_file)
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
