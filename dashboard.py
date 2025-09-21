import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

st.set_page_config(page_title="📊 داشبورد گزارش نمرات", layout="wide")
st.title("📊 داشبورد پیشرفته نمرات دانش‌آموزان")

# -------------------------------
# بارگذاری فایل‌ها
# -------------------------------
users_df = pd.read_excel("data/users.xlsx")
users_df.columns = users_df.columns.str.strip().str.replace('\u200c',' ').str.replace('\xa0',' ')

scores_file = "data/nomarat_darsi.xlsx"
scores_xl = pd.ExcelFile(scores_file)
lessons = scores_xl.sheet_names  # هر شیت = یک درس

# -------------------------------
# فرم ورود (صفحه اصلی)
# -------------------------------
st.subheader("🔐 ورود به داشبورد")
entered_role = st.selectbox("نقش خود را انتخاب کنید:", ["والد", "آموزگار", "مدیر"])
entered_code = st.text_input("رمز ورود:", type="password")
login_button = st.button("ورود")

if login_button:
    valid_user = users_df[(users_df["نقش"] == entered_role) & (users_df["رمز ورود"] == entered_code)]
    if valid_user.empty:
        st.warning("❌ رمز یا نقش اشتباه است.")
        st.stop()
    user_name = valid_user.iloc[0]["نام کاربر"]
    st.success(f"✅ خوش آمدید {user_name} عزیز! شما به‌عنوان {entered_role} وارد شده‌اید.")

    # -------------------------------
    # انتخاب درس
    # -------------------------------
    selected_lesson = st.selectbox("درس مورد نظر را انتخاب کنید:", lessons)
    lesson_data = pd.read_excel(scores_file, sheet_name=selected_lesson)
    lesson_data.columns = lesson_data.columns.str.strip().str.replace('\u200c',' ').str.replace('\xa0',' ')

    # -------------------------------
    # انتخاب دانش‌آموز
    # -------------------------------
    if entered_role == "والد":
        selected_student = user_name
    else:
        students = lesson_data['نام دانش‌آموز'].unique()
        selected_student = st.selectbox("دانش‌آموز را انتخاب کنید:", students)

    student_data = lesson_data[lesson_data['نام دانش‌آموز']==selected_student]

    # -------------------------------
    # نمودار دایره‌ای وضعیت کلاس
    # -------------------------------
    status_map = {1:'نیاز به تلاش بیشتر', 2:'قابل قبول', 3:'خوب', 4:'خیلی خوب'}
    status_colors = {'نیاز به تلاش بیشتر':'#FF6347', 'قابل قبول':'#FFD700',
                     'خوب':'#87CEFA', 'خیلی خوب':'#32CD32'}
    lesson_avg_status = lesson_data.drop('نام دانش‌آموز', axis=1).mean(axis=1).map(lambda x: int(round(x)))
    lesson_status_counts = lesson_avg_status.map(status_map).value_counts()

    fig1, ax1 = plt.subplots()
    ax1.pie([lesson_status_counts.get(s,0) for s in status_map.values()],
            labels=status_map.values(),
            colors=[status_colors[s] for s in status_map.values()],
            autopct='%1.1f%%', startangle=90)
    ax1.set_title(f"وضعیت کل کلاس در درس {selected_lesson}")
    st.pyplot(fig1)

    # -------------------------------
    # نمودار خطی هفته‌ها برای دانش‌آموز
    # -------------------------------
    weeks = [c for c in lesson_data.columns if c!='نام دانش‌آموز']
    student_scores = student_data[weeks].iloc[0]
    fig2, ax2 = plt.subplots()
    ax2.plot(weeks, student_scores, marker='o', linestyle='-', color='orange')
    ax2.set_title(f"نمرات {selected_student} در درس {selected_lesson}")
    ax2.set_ylabel("نمره")
    ax2.set_xlabel("هفته")
    st.pyplot(fig2)

    # -------------------------------
    # کارنامه مدرسه‌ای برای دانش‌آموز
    # -------------------------------
    st.subheader(f"📝 کارنامه {selected_student}")
    report_df = pd.DataFrame(columns=['درس','میانگین','وضعیت'])
    for lesson in lessons:
        df = pd.read_excel(scores_file, sheet_name=lesson)
        df.columns = df.columns.str.strip().str.replace('\u200c',' ').str.replace('\xa0',' ')
        student_row = df[df['نام دانش‌آموز']==selected_student]
        if not student_row.empty:
            avg_score = student_row.drop('نام دانش‌آموز', axis=1).mean(axis=1).values[0]
            status = status_map[int(round(avg_score))]
            report_df = report_df.append({'درس':lesson,'میانگین':round(avg_score,2),'وضعیت':status}, ignore_index=True)
    st.dataframe(report_df.style.apply(lambda x: [f"background-color: {status_colors[v]}" for v in x['وضعیت']], axis=1))

    # -------------------------------
    # دانلود PDF کارنامه
    # -------------------------------
    def generate_pdf(df, student_name):
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        c.setFont("Helvetica", 12)
        c.drawString(50, 800, f"کارنامه {student_name}")
        y = 770
        for index, row in df.iterrows():
            c.drawString(50, y, f"{row['درس']}: {row['میانگین']} - {row['وضعیت']}")
            y -= 20
        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer

    pdf_buffer = generate_pdf(report_df, selected_student)
    st.download_button(label="📥 دانلود PDF کارنامه", data=pdf_buffer, file_name=f"report_{selected_student}.pdf", mime='application/pdf')
