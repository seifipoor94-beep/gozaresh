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
# بارگذاری کاربران
# -------------------------------
users_df = pd.read_excel("data/users.xlsx")
users_df.columns = users_df.columns.str.strip().str.replace('\u200c',' ').str.replace('\xa0',' ')

# -------------------------------
# بارگذاری نمرات از همه شیت‌ها
# -------------------------------
xls = pd.ExcelFile("data/nomarat_darsi.xlsx")
all_data = []

for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name)
    df.columns = df.columns.str.strip().str.replace('\u200c',' ').str.replace('\xa0',' ')
    
    if 'نام دانش آموز' in df.columns:
        df.rename(columns={'نام دانش آموز':'نام دانش‌آموز'}, inplace=True)
    else:
        st.warning(f"ستون نام دانش‌آموز در شیت {sheet_name} یافت نشد و این شیت نادیده گرفته شد.")
        continue
    
    score_columns = [col for col in df.columns if col != 'نام دانش‌آموز']
    df_long = df.melt(id_vars=['نام دانش‌آموز'], value_vars=score_columns,
                      var_name='هفته', value_name='نمره')
    
    # تبدیل نمره به عددی
    df_long['نمره'] = pd.to_numeric(df_long['نمره'], errors='coerce')
    df_long = df_long.dropna(subset=['نمره'])
    
    df_long['درس'] = sheet_name
    all_data.append(df_long)

# ترکیب همه شیت‌ها
scores_long = pd.concat(all_data, ignore_index=True)

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
    student_scores = scores_long[scores_long['نام دانش‌آموز'] == user_name]
    lessons = student_scores['درس'].unique()
    selected_lesson = st.selectbox("درس مورد نظر را انتخاب کنید:", lessons)
    selected_student = user_name
else:
    lessons = scores_long['درس'].unique()
    selected_lesson = st.selectbox("درس مورد نظر را انتخاب کنید:", lessons)
    students = scores_long[scores_long['درس'] == selected_lesson]['نام دانش‌آموز'].unique()
    selected_student = st.selectbox("دانش‌آموز را انتخاب کنید:", students)

lesson_data = scores_long[scores_long['درس'] == selected_lesson]
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
                   hover_data=['هفته'],
                   title=f"نمرات درس {selected_lesson}")
st.plotly_chart(fig_class, use_container_width=True)

# -------------------------------
# رتبه‌بندی کلاس
# -------------------------------
st.subheader("🏆 رتبه‌بندی دانش‌آموزها")
lesson_rank = lesson_data.groupby('نام دانش‌آموز')['نمره'].mean().sort_values(ascending=False).reset_index()
lesson_rank.index = range(1, len(lesson_rank)+1)
st.dataframe(lesson_rank)

# -------------------------------
# نمودار دایره‌ای وضعیت کل کلاس
# -------------------------------
st.subheader("🍰 نمودار دایره‌ای وضعیت کل کلاس")
def categorize_grade(score):
    if score >= 17:
        return "عالی"
    elif score >= 12:
        return "متوسط"
    else:
        return "ضعیف"

lesson_data['وضعیت'] = lesson_data['نمره'].apply(categorize_grade)
fig_pie = px.pie(lesson_data, names='وضعیت', title=f"وضعیت کلاس در درس {selected_lesson}",
                 color='وضعیت', color_discrete_map={'عالی':'green', 'متوسط':'orange', 'ضعیف':'red'})
st.plotly_chart(fig_pie, use_container_width=True)

# -------------------------------
# نمودار تعاملی فردی
# -------------------------------
st.subheader(f"📊 نمودار نمرات {selected_student}")
if not student_data.empty:
    fig_student = px.bar(student_data, x='هفته', y='نمره',
                         color='نمره', color_continuous_scale='Oranges',
                         title=f"نمرات {selected_student} در درس {selected_lesson}")
    st.plotly_chart(fig_student, use_container_width=True)

# -------------------------------
# گزارش متنی فردی
# -------------------------------
st.subheader("📝 گزارش متنی نمرات")
if not student_data.empty:
    for idx, row in student_data.iterrows():
        st.text(f"{row['هفته']}: {row['نمره']}")
else:
    st.text(f"دانش‌آموز {selected_student} هنوز نمره‌ای برای درس {selected_lesson} ندارد.")
