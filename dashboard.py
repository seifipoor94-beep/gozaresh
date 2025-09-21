import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

st.set_page_config(page_title="📊 داشبورد گزارش نمرات", layout="wide")
st.title("📊 داشبورد گزارش نمرات دانش‌آموز")

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

# پاکسازی ستون‌ها برای جلوگیری از مشکلات فاصله و کاراکترهای اضافی
scores_df.columns = scores_df.columns.str.strip().str.replace('\u200c', ' ').str.replace('\xa0', ' ')

# اصلاح نام ستون‌ها اگر نیاز باشد
if 'نام دانش آموز' in scores_df.columns:
    scores_df.rename(columns={'نام دانش آموز': 'نام دانش‌آموز'}, inplace=True)
if 'درس ' in scores_df.columns:
    scores_df.rename(columns={'درس ': 'درس'}, inplace=True)
if 'نمره ' in scores_df.columns:
    scores_df.rename(columns={'نمره ': 'نمره'}, inplace=True)

# بررسی ستون‌های مورد نیاز
required_columns = ['نام دانش‌آموز', 'درس', 'نمره']
for col in required_columns:
    if col not in scores_df.columns:
        st.error(f"❌ ستون مورد نیاز '{col}' در فایل نمرات یافت نشد!")
        st.stop()

# -------------------------------
# فرم ورود
# -------------------------------
st.sidebar.title("🔐 ورود به داشبورد")
entered_role = st.sidebar.selectbox("نقش خود را انتخاب کنید:", ["والد", "آموزگار", "مدیر"])
entered_code = st.sidebar.text_input("رمز ورود:", type="password")

# بررسی اعتبار
valid_user = users_df[(users_df["نقش"] == entered_role) & (users_df["رمز ورود"] == entered_code)]

if valid_user.empty:
    st.warning("❌ رمز یا نقش اشتباه است.")
    st.stop()

user_name = valid_user.iloc[0]["نام کاربر"]
st.success(f"✅ خوش آمدید {user_name} عزیز! شما به‌عنوان {entered_role} وارد شده‌اید.")

# -------------------------------
# انتخاب درس
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

# -------------------------------
# نمودار کلی کلاس
# -------------------------------
st.subheader("📈 نمودارهای کلی کلاس")
lesson_data = scores_df[scores_df['درس'] == selected_lesson]

fig, ax = plt.subplots(figsize=(10,5))
ax.bar(lesson_data['نام دانش‌آموز'], lesson_data['نمره'], color='skyblue')
ax.set_ylabel("نمره")
ax.set_xlabel("دانش‌آموز")
ax.set_title(f"نمرات درس {selected_lesson}")
plt.xticks(rotation=45)
st.pyplot(fig)

# -------------------------------
# رتبه‌بندی کلاس
# -------------------------------
st.subheader("🏆 رتبه‌بندی دانش‌آموزها")
lesson_rank = lesson_data.sort_values(by='نمره', ascending=False)
lesson_rank.index = range(1, len(lesson_rank)+1)
st.dataframe(lesson_rank[['نام دانش‌آموز', 'نمره']])

# -------------------------------
# نمودار فردی
# -------------------------------
st.subheader(f"📊 نمودار نمرات {selected_student}")
student_data = lesson_data[lesson_data['نام دانش‌آموز'] == selected_student]

fig2, ax2 = plt.subplots(figsize=(6,4))
if not student_data.empty:
    ax2.bar(student_data['درس'], student_data['نمره'], color='orange')
    ax2.set_ylabel("نمره")
    ax2.set_xlabel("درس")
    ax2.set_title(f"نمرات {selected_student}")
    st.pyplot(fig2)

# -------------------------------
# گزارش متنی فردی
# -------------------------------
st.subheader("📝 گزارش متنی نمرات")
if not student_data.empty:
    st.text(f"دانش‌آموز: {selected_student}\nدرس: {selected_lesson}\nنمره: {student_data['نمره'].values[0]}")
else:
    st.text(f"دانش‌آموز {selected_student} هنوز برای درس {selected_lesson} نمره‌ای ندارد.")
