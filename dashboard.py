import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import os

# -------------------------------
# تنظیمات اولیه
# -------------------------------
st.set_page_config(page_title="📊 داشبورد گزارش نمرات", layout="wide")
st.title("📊 داشبورد گزارش نمرات دانش‌آموز")

# -------------------------------
# بارگذاری اطلاعات کاربران
# -------------------------------
users_df = pd.read_excel("data/users.xlsx")
users_df.columns = users_df.columns.str.strip().str.replace('\u200c', ' ').str.replace('\xa0', ' ')

# -------------------------------
# بارگذاری نمرات (همه شیت‌ها)
# -------------------------------
scores_dict = pd.read_excel("data/nomarat_darsi.xlsx", sheet_name=None)
scores_long = []
for lesson, df in scores_dict.items():
    df = df.rename(columns=lambda x: str(x).strip())
    df = df.melt(id_vars=["نام دانش آموز"], var_name="هفته", value_name="نمره")
    df["درس"] = lesson
    scores_long.append(df)
scores_long = pd.concat(scores_long, ignore_index=True)

# -------------------------------
# وضعیت کیفی نمرات
# -------------------------------
status_map = {
    1: "نیاز به تلاش بیشتر",
    2: "قابل قبول",
    3: "خوب",
    4: "خیلی خوب"
}
status_colors = {
    "نیاز به تلاش بیشتر": "#e74c3c",
    "قابل قبول": "#f1c40f",
    "خوب": "#3498db",
    "خیلی خوب": "#2ecc71"
}

# -------------------------------
# مدیریت وضعیت ورود با session_state
# -------------------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_name"] = ""
    st.session_state["role"] = ""

if not st.session_state["logged_in"]:
    st.subheader("🔐 ورود به داشبورد")
    entered_role = st.selectbox("نقش خود را انتخاب کنید:", ["والد", "آموزگار", "مدیر"])
    entered_code = st.text_input("رمز ورود:", type="password")

    if st.button("ورود"):
        valid_user = users_df[(users_df["نقش"] == entered_role) & (users_df["رمز ورود"] == entered_code)]
        if valid_user.empty:
            st.warning("❌ رمز یا نقش اشتباه است.")
        else:
            st.session_state["logged_in"] = True
            st.session_state["user_name"] = valid_user.iloc[0]["نام کاربر"]
            st.session_state["role"] = entered_role
            st.success("✅ ورود موفقیت‌آمیز بود. لطفاً دوباره روی ورود کلیک کنید.")
else:
    # -------------------------------
    # صفحه اصلی داشبورد
    # -------------------------------
    user_name = st.session_state["user_name"]
    entered_role = st.session_state["role"]
    st.success(f"✅ خوش آمدید {user_name} عزیز! شما به‌عنوان {entered_role} وارد شده‌اید.")

    # -------------------------------
    # انتخاب درس
    # -------------------------------
    lessons = scores_long["درس"].unique()
    selected_lesson = st.selectbox("📘 درس مورد نظر را انتخاب کنید:", lessons)

    # -------------------------------
    # انتخاب دانش‌آموز
    # -------------------------------
    if entered_role == "والد":
        selected_student = user_name
    else:
        students = scores_long[scores_long["درس"] == selected_lesson]["نام دانش آموز"].unique()
        selected_student = st.selectbox("👩‍🎓 دانش‌آموز را انتخاب کنید:", students)

    # -------------------------------
    # داده‌های درس انتخابی
    # -------------------------------
    lesson_data = scores_long[scores_long["درس"] == selected_lesson]

    # -------------------------------
    # نمودار دایره‌ای وضعیت کل کلاس
    # -------------------------------
    st.subheader(f"📊 وضعیت کیفی کلاس در درس {selected_lesson}")
    status_counts = lesson_data["نمره"].map(status_map).value_counts()

    fig_pie = px.pie(
        names=status_counts.index,
        values=status_counts.values,
        title=f"وضعیت کیفی کلاس در درس {selected_lesson}",
        color=status_counts.index,
        color_discrete_map=status_colors
    )
    st.plotly_chart(fig_pie)

    # -------------------------------
    # نمودار روند نمرات دانش‌آموز
    # -------------------------------
    st.subheader(f"📈 روند نمرات {selected_student} در درس {selected_lesson}")
    student_data = lesson_data[lesson_data["نام دانش آموز"] == selected_student]

    fig_line = px.line(
        student_data,
        x="هفته",
        y="نمره",
        markers=True,
        title=f"روند نمرات {selected_student} در درس {selected_lesson}"
    )
    st.plotly_chart(fig_line)

    # -------------------------------
    # رتبه‌بندی دانش‌آموزها در درس انتخابی (فقط برای معلم و مدیر)
    # -------------------------------
    if entered_role in ["آموزگار", "مدیر"]:
        st.subheader(f"🏆 رتبه‌بندی دانش‌آموزان در درس {selected_lesson}")
        student_avg = lesson_data.groupby("نام دانش آموز")["نمره"].mean().reset_index()
        student_avg["وضعیت"] = student_avg["نمره"].map(status_map)
        ranking = student_avg.sort_values(by="نمره", ascending=False).reset_index(drop=True)
        ranking.index = ranking.index + 1
        st.dataframe(ranking)

    # -------------------------------
    # رتبه‌بندی کلی (میانگین همه درس‌ها)
    # -------------------------------
    if entered_role in ["آموزگار", "مدیر"]:
        st.subheader("🌍 رتبه‌بندی کلی دانش‌آموزان (میانگین همه درس‌ها)")
        overall_avg = scores_long.groupby("نام دانش آموز")["نمره"].mean().reset_index()
        overall_avg["وضعیت"] = overall_avg["نمره"].map(status_map)
        overall_rank = overall_avg.sort_values(by="نمره", ascending=False).reset_index(drop=True)
        overall_rank.index = overall_rank.index + 1
        st.dataframe(overall_rank)
