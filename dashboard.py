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
    
    # تغییر نام ستون نام دانش‌آموز
    if 'نام دانش آموز' in df.columns:
        df.rename(columns={'نام دانش آموز':'نام دانش‌آموز'}, inplace=True)
    elif 'نام دانش‌آموز' not in df.columns:
        st.warning(f"ستون نام دانش‌آموز در شیت {sheet_name} یافت نشد و این شیت نادیده گرفته شد.")
        continue

    # استانداردسازی اسم هفته‌ها
    rename_map = {}
    for col in df.columns:
        if "هفته" in col:
            if "اول" in col: rename_map[col] = "هفته اول"
            elif "دوم" in col: rename_map[col] = "هفته دوم"
            elif "سوم" in col: rename_map[col] = "هفته سوم"
            elif "چهارم" in col: rename_map[col] = "هفته چهارم"
    df.rename(columns=rename_map, inplace=True)

    # تبدیل داده‌ها به حالت long
    score_columns = [col for col in df.columns if col != 'نام دانش‌آموز']
    df_long = df.melt(id_vars=['نام دانش‌آموز'], value_vars=score_columns,
                      var_name='هفته', value_name='نمره')

    # تبدیل نمره به عدد
    df_long['نمره'] = pd.to_numeric(df_long['نمره'], errors='coerce')
    df_long = df_long.dropna(subset=['نمره'])
    df_long['نمره'] = df_long['نمره'].astype(int)

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
# نمودار دایره‌ای وضعیت کیفی کلاس
# -------------------------------
st.subheader("🍩 نمودار وضعیت کیفی کلاس")

status_map = {
    1: "نیاز به تلاش بیشتر",
    2: "قابل قبول",
    3: "خوب",
    4: "خیلی خوب"
}

student_avg = lesson_data.groupby('نام دانش‌آموز')['نمره'].mean().reset_index()
student_avg['وضعیت'] = student_avg['نمره'].round().map(status_map)

fig_pie = px.pie(
    student_avg,
    names='وضعیت',
    title=f"درصد وضعیت کیفی دانش‌آموزان در درس {selected_lesson}",
    color='وضعیت',
    color_discrete_map={
        "نیاز به تلاش بیشتر": "red",
        "قابل قبول": "orange",
        "خوب": "blue",
        "خیلی خوب": "green"
    }
)
st.plotly_chart(fig_pie, use_container_width=True)

# -------------------------------
# رتبه‌بندی کلاس (فقط برای معلم و مدیر)
# -------------------------------
if entered_role in ["آموزگار", "مدیر"]:
    st.subheader("🏆 رتبه‌بندی دانش‌آموزان در این درس")
    ranking = student_avg.sort_values(by='نمره', ascending=False).reset_index(drop=True)
    ranking.index = ranking.index + 1
    st.dataframe(ranking[['نام دانش‌آموز', 'نمره', 'وضعیت']])

# -------------------------------
# نمودار فردی (خطی)
# -------------------------------
st.subheader(f"📊 روند نمرات {selected_student}")
if not student_data.empty:
    fig_line = px.line(
        student_data,
        x='هفته',
        y='نمره',
        markers=True,
        title=f"روند تغییرات نمرات {selected_student} در درس {selected_lesson}"
    )
    fig_line.update_traces(line_color='orange')
    st.plotly_chart(fig_line, use_container_width=True)

# -------------------------------
# مقایسه دانش‌آموز با میانگین کلاس
# -------------------------------
st.subheader("⚖️ مقایسه با میانگین کلاس")

student_avg_score = student_data['نمره'].mean()
class_avg_score = lesson_data['نمره'].mean()
diff = round(student_avg_score - class_avg_score, 2)

comparison_df = pd.DataFrame({
    "مقایسه": ["میانگین کلاس", f"{selected_student}"],
    "نمره": [class_avg_score, student_avg_score]
})

fig_compare = px.bar(
    comparison_df,
    x="مقایسه",
    y="نمره",
    color="مقایسه",
    title=f"مقایسه میانگین {selected_student} با میانگین کلاس"
)
st.plotly_chart(fig_compare, use_container_width=True)

if diff > 0:
    st.success(f"✅ {selected_student} به طور میانگین {abs(diff)} نمره بالاتر از میانگین کلاس است.")
elif diff < 0:
    st.warning(f"⚠️ {selected_student} به طور میانگین {abs(diff)} نمره پایین‌تر از میانگین کلاس است.")
else:
    st.info(f"ℹ️ {selected_student} دقیقا برابر با میانگین کلاس است.")

# -------------------------------
# گزارش متنی فردی
# -------------------------------
st.subheader("📝 گزارش متنی نمرات")
if not student_data.empty:
    for idx, row in student_data.iterrows():
        status = status_map.get(round(row['نمره']), "نامشخص")
        st.text(f"{row['هفته']}: {row['نمره']} ➝ {status}")
else:
    st.text(f"دانش‌آموز {selected_student} هنوز نمره‌ای برای درس {selected_lesson} ندارد.")
