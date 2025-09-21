import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="📊 داشبورد پیشرفته نمرات", layout="wide")
st.title("📊 داشبورد پیشرفته نمرات دانش‌آموز")

# -------------------------------
# بررسی وجود فایل‌ها
# -------------------------------
if not os.path.exists("data/users.xlsx") or not os.path.exists("data/nomarat_darsi.xlsx"):
    st.error("❌ یکی از فایل‌های داده پیدا نشد! لطفا مسیرها را بررسی کنید.")
    st.stop()

# -------------------------------
# بارگذاری اطلاعات کاربران
# -------------------------------
users_df = pd.read_excel("data/users.xlsx")
users_df.columns = users_df.columns.str.strip().str.replace('\u200c', ' ').str.replace('\xa0', ' ')

# -------------------------------
# بارگذاری نمرات
# -------------------------------
scores_df = pd.read_excel("data/nomarat_darsi.xlsx")
scores_df.columns = scores_df.columns.str.strip().str.replace('\u200c', ' ').str.replace('\xa0', ' ')

# -------------------------------
# شناسایی خودکار ستون‌ها
# -------------------------------
column_map = {}

for col in scores_df.columns:
    col_clean = col.strip().replace('\u200c',' ').replace('\xa0',' ')
    if 'نام' in col_clean and 'دانش' in col_clean:
        column_map['نام دانش‌آموز'] = col
    elif 'درس' in col_clean:
        column_map['درس'] = col
    elif 'نمره' in col_clean:
        column_map['نمره'] = col

# بررسی پیدا شدن همه ستون‌ها
required_columns = ['نام دانش‌آموز', 'درس', 'نمره']
missing_columns = [col for col in required_columns if col not in column_map]
if missing_columns:
    st.error(f"❌ ستون(های) مورد نیاز {missing_columns} در فایل نمرات یافت نشد! ستون‌های موجود: {scores_df.columns.tolist()}")
    st.stop()

# تغییر نام ستون‌ها به نام استاندارد
scores_df.rename(columns={v:k for k,v in column_map.items()}, inplace=True)

# -------------------------------
# فرم ورود
# -------------------------------
st.sidebar.title("🔐 ورود به داشبورد")
entered_role = st.sidebar.selectbox("نقش خود را انتخاب کنید:", ["والد", "آموزگار", "مدیر"])
entered_code = st.sidebar.text_input("رمز ورود:", type="password")

valid_user = users_df[(users_df["نقش"] == entered_role) & (users_df["رمز ورود"] == entered_code)]

if valid_user.empty:
    st.warning("❌ رمز یا نقش اشتباه است.")
    st.stop()

user_name = valid_user.iloc[0]["نام کاربر"]
st.success(f"✅ خوش آمدید {user_name} عزیز! شما به‌عنوان {entered_role} وارد شده‌اید.")

# -------------------------------
# انتخاب درس و دانش‌آموز
# -------------------------------
if entered_role == "والد":
    student_scores = scores_df[scores_df['نام دانش‌آموز'] == user_name]
    lessons = student_scores['درس'].unique()
    selected_lesson = st.selectbox("درس مورد نظر را انتخاب کنید:", lessons)
    selected_student = user_name
else:
    lessons = scores_df['درس'].unique()
    selected_lesson = st.selectbox("درس مورد نظر را انتخاب کنید:", lessons)
    students = scores_df[scores_df['درس'] == selected_lesson]['نام دانش‌آموز'].unique()
    selected_student = st.selectbox("دانش‌آموز را انتخاب کنید:", students)

lesson_data = scores_df[scores_df['درس'] == selected_lesson]
student_data = lesson_data[lesson_data['نام دانش‌آموز'] == selected_student]

# -------------------------------
# کارت‌های خلاصه کلاس
# -------------------------------
col1, col2, col3 = st.columns(3)
col1.metric("میانگین کلاس", round(lesson_data['نمره'].mean(), 2))
col2.metric("بیشترین نمره", lesson_data['نمره'].max())
col3.metric("کمترین نمره", lesson_data['نمره'].min())

# -------------------------------
# نمودار تعاملی کلاس
# -------------------------------
st.subheader("📈 نمودار تعاملی کلاس")
fig_class = px.bar(lesson_data, x='نام دانش‌آموز', y='نمره',
                   color='نمره', color_continuous_scale='Blues',
                   title=f"نمرات درس {selected_lesson}")
st.plotly_chart(fig_class, use_container_width=True)

# -------------------------------
# رتبه‌بندی کلاس
# -------------------------------
st.subheader("🏆 رتبه‌بندی دانش‌آموزها")
lesson_rank = lesson_data.sort_values(by='نمره', ascending=False)
lesson_rank.index = range(1, len(lesson_rank)+1)
st.dataframe(lesson_rank[['نام دانش‌آموز', 'نمره']])

# -------------------------------
# نمودار تعاملی فردی
# -------------------------------
st.subheader(f"📊 نمودار نمرات {selected_student}")
if not student_data.empty:
    fig_student = px.bar(student_data, x='درس', y='نمره',
                         color='نمره', color_continuous_scale='Oranges',
                         title=f"نمرات {selected_student}")
    st.plotly_chart(fig_student, use_container_width=True)

# -------------------------------
# گزارش متنی فردی
# -------------------------------
st.subheader("📝 گزارش متنی نمرات")
if not student_data.empty:
    st.text(f"دانش‌آموز: {selected_student}\nدرس: {selected_lesson}\nنمره: {student_data['نمره'].values[0]}")
else:
    st.text(f"دانش‌آموز {selected_student} هنوز برای درس {selected_lesson} نمره‌ای ندارد.")
