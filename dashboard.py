import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
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

    # تبدیل به حالت long
    score_columns = [col for col in df.columns if col != 'نام دانش‌آموز']
    df_long = df.melt(id_vars=['نام دانش‌آموز'], value_vars=score_columns,
                      var_name='هفته', value_name='نمره')

    df_long['نمره'] = pd.to_numeric(df_long['نمره'], errors='coerce')
    df_long = df_long.dropna(subset=['نمره'])
    df_long['نمره'] = df_long['نمره'].astype(int)
    df_long['درس'] = sheet_name
    all_data.append(df_long)

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
# نقشه وضعیت کیفی
# -------------------------------
status_map = {1:"نیاز به تلاش بیشتر", 2:"قابل قبول", 3:"خوب", 4:"خیلی خوب"}
status_colors = {"نیاز به تلاش بیشتر": "red", "قابل قبول":"orange","خوب":"blue","خیلی خوب":"green"}

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
student_avg = lesson_data.groupby('نام دانش‌آموز')['نمره'].mean().astype(int).map(status_map).reset_index(name='وضعیت')
fig_pie = px.pie(
    student_avg,
    names='وضعیت',
    title=f"درصد وضعیت کیفی دانش‌آموزان در درس {selected_lesson}",
    color='وضعیت',
    color_discrete_map=status_colors
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
# نمودار خطی دانش‌آموز
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
        status = status_map.get(int(row['نمره']), "نامشخص")
        st.text(f"{row['هفته']}: {row['نمره']} ➝ {status}")
else:
    st.text(f"دانش‌آموز {selected_student} هنوز نمره‌ای برای درس {selected_lesson} ندارد.")

# -------------------------------
# تولید PDF با کارنامه رنگی و نمودارها
# -------------------------------
def generate_full_pdf(student_name, scores_long, status_map, status_colors):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width/2, height - 50, f"کارنامه دانش‌آموز {student_name}")

    # جدول درس‌ها
    lessons = scores_long['درس'].unique()
    y = height - 100
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "درس")
    c.drawString(250, y, "میانگین نمره")
    c.drawString(400, y, "وضعیت کیفی")
    y -= 20
    c.setFont("Helvetica", 12)
    for lesson in lessons:
        df = scores_long[(scores_long['درس']==lesson) & (scores_long['نام دانش‌آموز']==student_name)]
        if df.empty: continue
        avg_score = df['نمره'].mean()
        avg_score_int = int(round(avg_score))
        status = status_map.get(avg_score_int, "نامشخص")
        # رنگ وضعیت
        c.setFillColorRGB(0,0,0)
        if status=="نیاز به تلاش بیشتر": c.setFillColorRGB(1,0,0)
        elif status=="قابل قبول": c.setFillColorRGB(1,0.65,0)
        elif status=="خوب": c.setFillColorRGB(0,0,1)
        elif status=="خیلی خوب": c.setFillColorRGB(0,0.5,0)
        c.drawString(50, y, lesson)
        c.setFillColorRGB(0,0,0)
        c.drawString(250, y, f"{round(avg_score,2)}")
        c.setFillColorRGB(*c.getFillColorRGB()) # رنگ وضعیت
        c.drawString(400, y, status)
        y -= 20

    # میانگین کل
    student_overall_avg = scores_long[scores_long['نام دانش‌آموز']==student_name]['نمره'].mean()
    overall_status = status_map.get(int(round(student_overall_avg)), "نامشخص")
    y -= 10
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0,0,0)
    c.drawString(50, y, f"میانگین کل: {round(student_overall_avg,2)} → {overall_status}")
    y -= 30

    # نمودار خطی دانش‌آموز (درس‌ها را پشت سر هم)
    df_student = scores_long[scores_long['نام دانش‌آموز']==student_name]
    plt.figure(figsize=(6,3))
    for lesson in df_student['درس'].unique():
        df_lesson = df_student[df_student['درس']==lesson]
        plt.plot(df_lesson['هفته'], df_lesson['نمره'], marker='o', label=lesson)
    plt.title("روند نمرات دانش‌آموز")
    plt.xlabel("هفته")
    plt.ylabel("نمره")
    plt.legend()
    line_buffer = BytesIO()
    plt.tight_layout()
    plt.savefig(line_buffer, format='png')
    plt.close()
    line_buffer.seek(0)
    c.drawImage(ImageReader(line_buffer), 50, y-150, width=500, height=150)
    y -= 170

    # نمودار دایره‌ای وضعیت کل کلاس
    class_status = scores_long.groupby(['درس','نام دانش‌آموز'])['نمره'].mean().astype(int).map(status_map)
    status_counts = class_status.value_counts()
    plt.figure(figsize=(5,3))
    plt.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%',
            colors=['red','orange','blue','green'])
    plt.title("وضعیت کیفی کل کلاس")
    pie_buffer = BytesIO()
    plt.savefig(pie_buffer, format='png')
    plt.close()
    pie_buffer.seek(0)
    c.drawImage(ImageReader(pie_buffer), 50, y-150, width=300, height=150)

    c.save()
    buffer.seek(0)
    return buffer

# دکمه دانلود PDF
pdf_buffer = generate_full_pdf(user_name, scores_long, status_map, status_colors)
st.download_button(
    label="📥 دانلود کارنامه کامل رنگی با نمودارها",
    data=pdf_buffer,
    file_name=f"کارنامه_{user_name}.pdf",
    mime="application/pdf"
)
