import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import config
from database import get_db, init_db
from seed_data import seed

# Page configuration
st.set_page_config(
    page_title=f"{config.SCHOOL_NAME} - SMS",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 1.8rem;
        font-weight: 800;
        color: #1e3a8a;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 0.9rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #ffffff;
        padding: 1.2rem;
        border-radius: 1rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .status-badge-active {
        background-color: #ecfdf5;
        color: #047857;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .status-badge-unpaid {
        background-color: #fef2f2;
        color: #b91c1c;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# Ensure database exists and is seeded
@st.cache_resource
def setup_database():
    init_db()
    seed()

setup_database()

# Database helper functions
def fetch_query(query, params=()):
    conn = get_db()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def execute_cmd(query, params=()):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id

def calculate_grade(marks, max_marks=100.0):
    pct = (marks / max_marks) * 100 if max_marks > 0 else 0
    if pct >= 90: return 'A+', 'Outstanding'
    elif pct >= 80: return 'A', 'Excellent'
    elif pct >= 70: return 'B', 'Very Good'
    elif pct >= 60: return 'C', 'Good'
    elif pct >= 50: return 'D', 'Satisfactory'
    else: return 'F', 'Needs Improvement'

# Sidebar Navigation
st.sidebar.markdown(f"### 🎓 {config.SCHOOL_NAME}")
st.sidebar.markdown(f"<span style='font-size: 12px; color: #64748b;'>{config.SCHOOL_TAGLINE}</span>", unsafe_allow_html=True)
st.sidebar.divider()

nav = st.sidebar.radio(
    "Navigation Menu",
    [
        "📊 Dashboard",
        "👨‍🎓 Students Directory",
        "📝 New Admission",
        "📅 Attendance Tracking",
        "🏆 Exams & Gradebook",
        "💳 Fees & Accounts",
        "🏛️ Classes & Subjects",
        "👨‍🏫 Faculty Directory",
        "📢 Noticeboard"
    ]
)

st.sidebar.divider()
st.sidebar.info(f"**Session:** {config.SCHOOL_ACADEMIC_YEAR}\n\n**Support:** {config.SCHOOL_CONTACT}")

# ==========================================
# 1. DASHBOARD
# ==========================================
if nav == "📊 Dashboard":
    st.markdown(f"<div class='main-header'>Institutional Executive Dashboard</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub-header'>Campus metrics, academic analytics, and live administrative pulse</div>", unsafe_allow_html=True)

    # Fetch KPI metrics
    students_df = fetch_query("SELECT COUNT(*) as c FROM students WHERE status = 'Active'")
    total_students = students_df['c'][0] if not students_df.empty else 0

    teachers_df = fetch_query("SELECT COUNT(*) as c FROM teachers WHERE status = 'Active'")
    total_teachers = teachers_df['c'][0] if not teachers_df.empty else 0

    fin_df = fetch_query("SELECT COALESCE(SUM(amount), 0) as inv, COALESCE(SUM(paid_amount), 0) as col FROM fee_invoices")
    total_inv = fin_df['inv'][0] if not fin_df.empty else 0
    total_col = fin_df['col'][0] if not fin_df.empty else 0
    total_pend = total_inv - total_col

    att_df = fetch_query("""
        SELECT COUNT(*) as tot, SUM(CASE WHEN status IN ('Present', 'Late') THEN 1 ELSE 0 END) as att
        FROM attendance
    """)
    tot_rec = att_df['tot'][0] if not att_df.empty else 0
    att_rec = att_df['att'][0] if not att_df.empty else 0
    att_pct = (att_rec / tot_rec * 100) if tot_rec > 0 else 0.0

    # Top KPI Metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Enrolled Students", f"{total_students}", "Active")
    with col2:
        st.metric("Teaching Faculty", f"{total_teachers}", "Full-Time")
    with col3:
        st.metric("Campus Attendance", f"{att_pct:.1f}%", "Overall")
    with col4:
        st.metric("Fees Collected", f"${total_col:,.2f}", f"Pending: ${total_pend:,.2f}", delta_color="inverse")

    st.markdown("---")

    # Analytics Charts
    c1, c2 = st.columns([3, 2])
    with c1:
        st.subheader("📈 Grade Performance Distribution")
        grades_chart_df = fetch_query("""
            SELECT grade_letter as Grade, COUNT(*) as Count
            FROM grades
            WHERE grade_letter IS NOT NULL
            GROUP BY grade_letter
            ORDER BY grade_letter
        """)
        if not grades_chart_df.empty:
            st.bar_chart(grades_chart_df.set_index('Grade'))
        else:
            st.info("No exam grade records yet.")

    with c2:
        st.subheader("🕒 Daily Attendance Breakdown")
        att_breakdown = fetch_query("SELECT status as Status, COUNT(*) as Records FROM attendance GROUP BY status")
        if not att_breakdown.empty:
            st.bar_chart(att_breakdown.set_index('Status'))
        else:
            st.info("No attendance records logged.")

    # Recent Admissions & Notices
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🆕 Recent Admissions")
        recent_s = fetch_query("""
            SELECT s.admission_no as [Adm No], s.first_name || ' ' || s.last_name as Name,
                   c.name as Class, s.status as Status
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
            ORDER BY s.id DESC LIMIT 5
        """)
        st.dataframe(recent_s, use_container_width=True, hide_index=True)

    with col_b:
        st.subheader("📢 Active Notices")
        notices = fetch_query("SELECT title as Title, target_audience as [To], priority as Priority, created_at as Date FROM announcements ORDER BY id DESC LIMIT 5")
        st.dataframe(notices, use_container_width=True, hide_index=True)

# ==========================================
# 2. STUDENTS DIRECTORY
# ==========================================
elif nav == "👨‍🎓 Students Directory":
    st.markdown("<div class='main-header'>Student Registry & 360° Profiles</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Search, filter, inspect profiles, and export student files</div>", unsafe_allow_html=True)

    # Search and filters
    f1, f2, f3 = st.columns([3, 2, 2])
    with f1:
        search = st.text_input("🔍 Search by name, roll no, or admission no...")
    with f2:
        classes_list = fetch_query("SELECT id, name FROM classes ORDER BY grade_level, section")
        class_options = {"All Classes": ""}
        for _, row in classes_list.iterrows():
            class_options[row['name']] = row['id']
        selected_class_label = st.selectbox("Filter Class", list(class_options.keys()))
        selected_class_id = class_options[selected_class_label]
    with f3:
        status_filter = st.selectbox("Filter Status", ["All Statuses", "Active", "Inactive", "Graduated"])

    # Query builder
    query = """
        SELECT s.id, s.admission_no as [Adm No], s.roll_no as Roll,
               s.first_name || ' ' || s.last_name as [Full Name],
               c.name as Class, s.gender as Gender, s.dob as DOB,
               s.blood_group as Blood, s.phone as Phone, s.parent_name as [Parent],
               s.parent_phone as [Emergency Phone], s.status as Status
        FROM students s
        LEFT JOIN classes c ON s.class_id = c.id
        WHERE 1=1
    """
    params = []
    if search:
        query += " AND (s.first_name LIKE ? OR s.last_name LIKE ? OR s.admission_no LIKE ? OR s.roll_no LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term])
    if selected_class_id:
        query += " AND s.class_id = ?"
        params.append(selected_class_id)
    if status_filter != "All Statuses":
        query += " AND s.status = ?"
        params.append(status_filter)

    query += " ORDER BY s.class_id, CAST(s.roll_no AS INTEGER)"
    students_df = fetch_query(query, params)

    st.markdown(f"**Found {len(students_df)} students**")
    st.dataframe(students_df.drop(columns=['id']), use_container_width=True, hide_index=True)

    # Export CSV
    csv_data = students_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Export Roster to CSV", csv_data, "Students_Roster.csv", "text/csv")

    st.divider()

    # Detailed Student 360 View
    st.subheader("👤 Inspect Student Dossier")
    if not students_df.empty:
        student_choice = st.selectbox(
            "Select Student to View 360° Profile:",
            students_df['id'].tolist(),
            format_func=lambda x: f"{students_df.loc[students_df['id'] == x, 'Adm No'].values[0]} - {students_df.loc[students_df['id'] == x, 'Full Name'].values[0]} ({students_df.loc[students_df['id'] == x, 'Class'].values[0]})"
        )

        student_row = fetch_query("""
            SELECT s.*, c.name as class_name, c.room_number, t.full_name as teacher_name
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
            LEFT JOIN teachers t ON c.class_teacher_id = t.id
            WHERE s.id = ?
        """, (student_choice,)).iloc[0]

        p1, p2 = st.columns([1, 3])
        with p1:
            st.image(student_row['avatar_url'], width=140)
            st.markdown(f"### {student_row['first_name']} {student_row['last_name']}")
            st.caption(f"**Adm:** `{student_row['admission_no']}` | **Roll:** `#{student_row['roll_no']}`")
            st.info(f"**Class:** {student_row['class_name']}\n\n**Class Teacher:** {student_row['teacher_name'] or 'None'}")

        with p2:
            tab_bio, tab_grades, tab_att, tab_fees = st.tabs(["📋 Bio & Contact", "🏆 Grades & Report", "📅 Attendance", "💳 Invoices"])
            with tab_bio:
                b1, b2 = st.columns(2)
                with b1:
                    st.write(f"**Date of Birth:** {student_row['dob']}")
                    st.write(f"**Gender:** {student_row['gender']}")
                    st.write(f"**Blood Group:** {student_row['blood_group'] or 'N/A'}")
                    st.write(f"**Address:** {student_row['address']}")
                with b2:
                    st.write(f"**Parent Name:** {student_row['parent_name']}")
                    st.write(f"**Emergency Phone:** {student_row['parent_phone']}")
                    st.write(f"**Student Email:** {student_row['email']}")
                    st.write(f"**Admission Date:** {student_row['admission_date']}")

            with tab_grades:
                s_grades = fetch_query("""
                    SELECT ex.name as Exam, sub.code as Code, sub.name as Subject,
                           g.marks_obtained as [Marks Scored], g.max_marks as [Max],
                           g.grade_letter as Grade, g.remarks as Remarks
                    FROM grades g
                    JOIN subjects sub ON g.subject_id = sub.id
                    JOIN exams ex ON g.exam_id = ex.id
                    WHERE g.student_id = ?
                """, (student_choice,))
                st.dataframe(s_grades, use_container_width=True, hide_index=True)

            with tab_att:
                s_att = fetch_query("SELECT date as Date, status as Status, remarks as Remarks FROM attendance WHERE student_id = ? ORDER BY date DESC LIMIT 15", (student_choice,))
                st.dataframe(s_att, use_container_width=True, hide_index=True)

            with tab_fees:
                s_fees = fetch_query("""
                    SELECT fi.invoice_no as [Invoice No], ft.name as [Category],
                           fi.amount as [Amount], fi.paid_amount as [Paid],
                           fi.due_date as [Due Date], fi.status as [Status]
                    FROM fee_invoices fi
                    JOIN fee_types ft ON fi.fee_type_id = ft.id
                    WHERE fi.student_id = ?
                """, (student_choice,))
                st.dataframe(s_fees, use_container_width=True, hide_index=True)

# ==========================================
# 3. NEW ADMISSION
# ==========================================
elif nav == "📝 New Admission":
    st.markdown("<div class='main-header'>Student Admission Portal</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Enroll a new student and generate admission paperwork</div>", unsafe_allow_html=True)

    classes_list = fetch_query("SELECT id, name FROM classes ORDER BY grade_level, section")
    class_map = {row['name']: row['id'] for _, row in classes_list.iterrows()}

    with st.form("admission_form", clear_on_submit=True):
        st.subheader("1. Academic Placement")
        c1, c2, c3 = st.columns(3)
        with c1:
            roll_no = st.text_input("Roll Number *", placeholder="e.g. 105")
        with c2:
            sel_class = st.selectbox("Assigned Class *", list(class_map.keys()))
        with c3:
            adm_date = st.date_input("Admission Date", datetime.now())

        st.subheader("2. Personal Information")
        p1, p2, p3 = st.columns(3)
        with p1:
            fn = st.text_input("First Name *")
            gender = st.selectbox("Gender *", ["Male", "Female", "Other"])
        with p2:
            ln = st.text_input("Last Name *")
            dob = st.date_input("Date of Birth *", datetime(2010, 1, 1))
        with p3:
            blood = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
            phone = st.text_input("Phone Number")

        email = st.text_input("Student Email Address")
        address = st.text_input("Residential Street Address")

        st.subheader("3. Guardian / Emergency Details")
        g1, g2, g3 = st.columns(3)
        with g1:
            parent_name = st.text_input("Parent / Guardian Full Name *")
        with g2:
            parent_phone = st.text_input("Emergency Phone Number *")
        with g3:
            parent_email = st.text_input("Parent Email Address")

        submitted = st.form_submit_button("Complete Admission & Register Student", type="primary")
        if submitted:
            if not fn or not ln or not roll_no or not parent_name or not parent_phone:
                st.error("Please fill in all required fields marked with an asterisk (*).")
            else:
                count_df = fetch_query("SELECT COUNT(*) as c FROM students")
                next_num = count_df['c'][0] + 1
                adm_no = f"ADM-2025-{next_num:03d}"
                avatar_url = f"https://api.dicebear.com/7.x/bottts/svg?seed={fn}{ln}"

                try:
                    execute_cmd("""
                        INSERT INTO students (
                            admission_no, roll_no, first_name, last_name, gender, dob, blood_group,
                            email, phone, address, class_id, admission_date, parent_name, parent_relation,
                            parent_phone, parent_email, status, avatar_url
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Parent', ?, ?, 'Active', ?)
                    """, (
                        adm_no, roll_no, fn, ln, gender, str(dob), blood,
                        email, phone, address, class_map[sel_class], str(adm_date), parent_name,
                        parent_phone, parent_email, avatar_url
                    ))
                    st.success(f"Student **{fn} {ln}** enrolled successfully with Admission No **{adm_no}**!")
                except Exception as e:
                    st.error(f"Error registering student: {e}")

# ==========================================
# 4. ATTENDANCE TRACKING
# ==========================================
elif nav == "📅 Attendance Tracking":
    st.markdown("<div class='main-header'>Daily Attendance Tracking</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Batch roll call and class attendance registers</div>", unsafe_allow_html=True)

    tab_mark, tab_report = st.tabs(["📝 Take Daily Attendance", "📊 Attendance Register & Defaulters"])

    classes_list = fetch_query("SELECT id, name FROM classes ORDER BY grade_level, section")
    class_map = {row['name']: row['id'] for _, row in classes_list.iterrows()}

    with tab_mark:
        col_c, col_d = st.columns(2)
        with col_c:
            selected_class_name = st.selectbox("Select Class", list(class_map.keys()), key="att_class")
            c_id = class_map[selected_class_name]
        with col_d:
            selected_date = st.date_input("Attendance Date", datetime.now(), key="att_date")
            d_str = str(selected_date)

        students_att = fetch_query("""
            SELECT s.id as student_id, s.roll_no, s.first_name || ' ' || s.last_name as student_name,
                   COALESCE(a.status, 'Present') as status,
                   COALESCE(a.remarks, '') as remarks
            FROM students s
            LEFT JOIN attendance a ON s.id = a.student_id AND a.date = ?
            WHERE s.class_id = ? AND s.status = 'Active'
            ORDER BY CAST(s.roll_no AS INTEGER)
        """, (d_str, c_id))

        if students_att.empty:
            st.info("No active students enrolled in this class.")
        else:
            with st.form("save_attendance_form"):
                st.write(f"**Class:** {selected_class_name} | **Date:** {d_str} | **Roster:** {len(students_att)} students")
                
                updated_statuses = {}
                updated_remarks = {}

                for _, row in students_att.iterrows():
                    s_id = row['student_id']
                    c1, c2, c3 = st.columns([1, 2, 2])
                    with c1:
                        st.write(f"**#{row['roll_no']}**")
                    with c2:
                        st.write(row['student_name'])
                        stat = st.radio(f"Status_{s_id}", ["Present", "Late", "Absent", "Excused"],
                                        index=["Present", "Late", "Absent", "Excused"].index(row['status']),
                                        horizontal=True, key=f"radio_{s_id}", label_visibility="collapsed")
                        updated_statuses[s_id] = stat
                    with c3:
                        rem = st.text_input(f"Remarks_{s_id}", value=row['remarks'], placeholder="Optional note...",
                                            key=f"rem_{s_id}", label_visibility="collapsed")
                        updated_remarks[s_id] = rem
                    st.divider()

                save_att = st.form_submit_button("💾 Save Attendance Sheet", type="primary")
                if save_att:
                    for s_id, stat in updated_statuses.items():
                        execute_cmd("""
                            INSERT INTO attendance (student_id, class_id, date, status, remarks)
                            VALUES (?, ?, ?, ?, ?)
                            ON CONFLICT(student_id, date) DO UPDATE SET
                                status = excluded.status,
                                remarks = excluded.remarks,
                                class_id = excluded.class_id
                        """, (s_id, c_id, d_str, stat, updated_remarks[s_id]))
                    st.success("Attendance sheet saved successfully!")

    with tab_report:
        rep_class = st.selectbox("Class Register", list(class_map.keys()), key="rep_class")
        rep_c_id = class_map[rep_class]

        rep_df = fetch_query("""
            SELECT s.roll_no as [Roll], s.first_name || ' ' || s.last_name as [Name],
                   COUNT(a.id) as [Total Days],
                   SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as [Present],
                   SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as [Absent],
                   SUM(CASE WHEN a.status = 'Late' THEN 1 ELSE 0 END) as [Late],
                   SUM(CASE WHEN a.status = 'Excused' THEN 1 ELSE 0 END) as [Excused]
            FROM students s
            LEFT JOIN attendance a ON s.id = a.student_id
            WHERE s.class_id = ? AND s.status = 'Active'
            GROUP BY s.id
            ORDER BY CAST(s.roll_no AS INTEGER)
        """, (rep_c_id,))

        if not rep_df.empty:
            rep_df['Attendance %'] = ((rep_df['Present'] + rep_df['Late']) / rep_df['Total Days'] * 100).fillna(0).round(1)
            st.dataframe(rep_df, use_container_width=True, hide_index=True)

            defaulters = rep_df[rep_df['Attendance %'] < 75.0]
            if not defaulters.empty:
                st.warning(f"⚠️ **{len(defaulters)} students** have attendance below the mandatory 75% threshold.")
                st.dataframe(defaulters[['Roll', 'Name', 'Attendance %']], use_container_width=True, hide_index=True)

# ==========================================
# 5. EXAMINATIONS & GRADEBOOK
# ==========================================
elif nav == "🏆 Exams & Gradebook":
    st.markdown("<div class='main-header'>Examinations, Marks & Report Cards</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Gradebook marks entry sheets and student report card generator</div>", unsafe_allow_html=True)

    tab_marks, tab_sched, tab_card = st.tabs(["📝 Gradebook Marks Entry", "📅 Scheduled Exams", "📜 Student Report Card"])

    with tab_marks:
        exams_list = fetch_query("SELECT id, name FROM exams ORDER BY id DESC")
        subjects_list = fetch_query("SELECT id, code || ' - ' || name as label FROM subjects ORDER BY name")
        classes_list = fetch_query("SELECT id, name FROM classes ORDER BY grade_level, section")

        m1, m2, m3 = st.columns(3)
        with m1:
            sel_exam = st.selectbox("Select Exam", exams_list['name'].tolist())
            exam_id = exams_list.loc[exams_list['name'] == sel_exam, 'id'].values[0]
        with m2:
            sel_class = st.selectbox("Select Class", classes_list['name'].tolist(), key="m_class")
            cls_id = classes_list.loc[classes_list['name'] == sel_class, 'id'].values[0]
        with m3:
            sel_sub = st.selectbox("Select Subject", subjects_list['label'].tolist())
            sub_id = subjects_list.loc[subjects_list['label'] == sel_sub, 'id'].values[0]

        students_marks = fetch_query("""
            SELECT s.id as student_id, s.roll_no as Roll, s.first_name || ' ' || s.last_name as Student,
                   g.marks_obtained, g.remarks
            FROM students s
            LEFT JOIN grades g ON s.id = g.student_id AND g.exam_id = ? AND g.subject_id = ?
            WHERE s.class_id = ? AND s.status = 'Active'
            ORDER BY CAST(s.roll_no AS INTEGER)
        """, (exam_id, sub_id, cls_id))

        with st.form("marks_entry_form"):
            st.write(f"Entering marks for: **{sel_exam}** &bull; **{sel_sub}** &bull; **{sel_class}**")
            new_marks = {}
            new_rems = {}

            for _, row in students_marks.iterrows():
                s_id = row['student_id']
                col_r, col_n, col_m, col_f = st.columns([1, 2, 2, 2])
                with col_r:
                    st.write(f"**#{row['Roll']}**")
                with col_n:
                    st.write(row['Student'])
                with col_m:
                    val = float(row['marks_obtained']) if pd.notnull(row['marks_obtained']) else 0.0
                    new_marks[s_id] = st.number_input(f"Marks_{s_id}", min_value=0.0, max_value=100.0, value=val, step=0.5, label_visibility="collapsed")
                with col_f:
                    val_rem = str(row['remarks']) if pd.notnull(row['remarks']) else ""
                    new_rems[s_id] = st.text_input(f"Rem_{s_id}", value=val_rem, placeholder="Remarks...", label_visibility="collapsed")

            save_marks = st.form_submit_button("💾 Save All Marks & Grades", type="primary")
            if save_marks:
                for s_id, score in new_marks.items():
                    let, auto_rem = calculate_grade(score, 100.0)
                    final_rem = new_rems[s_id] if new_rems[s_id] else auto_rem
                    execute_cmd("""
                        INSERT INTO grades (student_id, exam_id, subject_id, marks_obtained, max_marks, grade_letter, remarks)
                        VALUES (?, ?, ?, ?, 100.0, ?, ?)
                        ON CONFLICT(student_id, exam_id, subject_id) DO UPDATE SET
                            marks_obtained = excluded.marks_obtained,
                            grade_letter = excluded.grade_letter,
                            remarks = excluded.remarks
                    """, (s_id, exam_id, sub_id, score, let, final_rem))
                st.success("Marks recorded and letter grades calculated successfully!")

    with tab_card:
        st.subheader("Official Academic Report Card")
        students_all = fetch_query("SELECT id, admission_no || ' - ' || first_name || ' ' || last_name as label FROM students WHERE status = 'Active' ORDER BY first_name")
        r_exam = st.selectbox("Exam Term", exams_list['name'].tolist(), key="r_exam")
        r_exam_id = exams_list.loc[exams_list['name'] == r_exam, 'id'].values[0]

        r_student = st.selectbox("Student", students_all['label'].tolist(), key="r_stu")
        r_student_id = students_all.loc[students_all['label'] == r_student, 'id'].values[0]

        st.markdown(f"""
        <div style="background: #ffffff; padding: 2rem; border-radius: 1rem; border: 2px solid #1e3a8a; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-top: 1rem;">
            <div style="text-align: center; border-bottom: 2px solid #1e3a8a; padding-bottom: 1rem; margin-bottom: 1.5rem;">
                <h2 style="color: #1e3a8a; margin: 0; text-transform: uppercase;">{config.SCHOOL_NAME}</h2>
                <p style="color: #64748b; margin: 0.2rem 0; font-size: 0.85rem;">{config.SCHOOL_TAGLINE} &bull; {config.SCHOOL_ADDRESS}</p>
                <h4 style="color: #0f172a; margin-top: 0.5rem;">OFFICIAL ACADEMIC REPORT CARD &mdash; {r_exam.upper()}</h4>
            </div>
        </div>
        """, unsafe_allow_html=True)

        card_grades = fetch_query("""
            SELECT sub.code as [Code], sub.name as [Subject Title],
                   g.marks_obtained as [Marks Scored], g.max_marks as [Max],
                   g.grade_letter as [Grade], g.remarks as [Remarks]
            FROM grades g
            JOIN subjects sub ON g.subject_id = sub.id
            WHERE g.student_id = ? AND g.exam_id = ?
        """, (r_student_id, r_exam_id))

        if not card_grades.empty:
            st.dataframe(card_grades, use_container_width=True, hide_index=True)
            total_scored = card_grades['Marks Scored'].sum()
            total_max = card_grades['Max'].sum()
            overall_pct = (total_scored / total_max * 100) if total_max > 0 else 0
            overall_grade, _ = calculate_grade(total_scored, total_max)

            c1, c2, c3 = st.columns(3)
            c1.metric("Cumulative Score", f"{total_scored:.1f} / {total_max:.0f}")
            c2.metric("Overall Percentage", f"{overall_pct:.1f}%")
            c3.metric("Final Grade", f"{overall_grade}", "PASSED" if overall_pct >= 50 else "FAILED")
        else:
            st.info("No exam marks entered for this student in this term.")

    with tab_sched:
        st.subheader("Manage Scheduled Exams")
        ex_df = fetch_query("SELECT id, name as Title, exam_type as Type, academic_year as Session, term as Term, start_date as Start, end_date as End FROM exams")
        st.dataframe(ex_df.drop(columns=['id']), use_container_width=True, hide_index=True)

        with st.expander("➕ Schedule New Exam"):
            with st.form("new_exam_form"):
                e_name = st.text_input("Exam Name *", placeholder="e.g. Annual Final Assessment 2026")
                e_type = st.selectbox("Exam Type", ["Semester Exam", "Mid-Term Exam", "Unit Test", "Assessment"])
                e_term = st.text_input("Term", "Term 2")
                e_start = st.date_input("Start Date", datetime.now())
                e_end = st.date_input("End Date", datetime.now() + timedelta(days=10))

                if st.form_submit_button("Save Exam"):
                    if e_name:
                        execute_cmd("INSERT INTO exams (name, exam_type, academic_year, term, start_date, end_date) VALUES (?, ?, ?, ?, ?, ?)",
                                    (e_name, e_type, config.SCHOOL_ACADEMIC_YEAR, e_term, str(e_start), str(e_end)))
                        st.success("Exam scheduled successfully!")
                        st.rerun()

# ==========================================
# 6. FEES & ACCOUNTS
# ==========================================
elif nav == "💳 Fees & Accounts":
    st.markdown("<div class='main-header'>Student Billing & Fee Accounting</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Invoices, fee collections, payment receipts, and balance ledgers</div>", unsafe_allow_html=True)

    fin_kpis = fetch_query("""
        SELECT COALESCE(SUM(amount), 0) as inv, COALESCE(SUM(paid_amount), 0) as col,
               COUNT(*) as count, SUM(CASE WHEN status = 'Unpaid' THEN 1 ELSE 0 END) as unpaid
        FROM fee_invoices
    """).iloc[0]

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Billed", f"${fin_kpis['inv']:,.2f}")
    k2.metric("Total Collected", f"${fin_kpis['col']:,.2f}")
    k3.metric("Outstanding Balance", f"${(fin_kpis['inv'] - fin_kpis['col']):,.2f}")
    k4.metric("Unpaid Invoices", f"{fin_kpis['unpaid']}")

    st.divider()

    tab_inv, tab_pay = st.tabs(["📑 Invoice Records", "💵 Record Payment"])

    with tab_inv:
        invoices = fetch_query("""
            SELECT fi.id, fi.invoice_no as [Invoice],
                   s.first_name || ' ' || s.last_name as [Student],
                   c.name as [Class], ft.name as [Category],
                   fi.amount as [Billed], fi.paid_amount as [Paid],
                   (fi.amount - fi.paid_amount) as [Balance Due],
                   fi.due_date as [Due Date], fi.status as [Status]
            FROM fee_invoices fi
            JOIN fee_types ft ON fi.fee_type_id = ft.id
            JOIN students s ON fi.student_id = s.id
            LEFT JOIN classes c ON s.class_id = c.id
            ORDER BY fi.id DESC
        """)
        st.dataframe(invoices.drop(columns=['id']), use_container_width=True, hide_index=True)

    with tab_pay:
        st.subheader("Record Payment Transaction")
        unpaid_invoices = fetch_query("""
            SELECT fi.id, fi.invoice_no || ' - ' || s.first_name || ' ' || s.last_name || ' (Due: $' || (fi.amount - fi.paid_amount) || ')' as label,
                   (fi.amount - fi.paid_amount) as due_amt
            FROM fee_invoices fi
            JOIN students s ON fi.student_id = s.id
            WHERE fi.status != 'Paid'
        """)

        if unpaid_invoices.empty:
            st.success("All student invoices are fully paid!")
        else:
            with st.form("pay_form"):
                sel_inv = st.selectbox("Select Pending Invoice", unpaid_invoices['label'].tolist())
                inv_id = unpaid_invoices.loc[unpaid_invoices['label'] == sel_inv, 'id'].values[0]
                due_val = float(unpaid_invoices.loc[unpaid_invoices['label'] == sel_inv, 'due_amt'].values[0])

                p_amt = st.number_input("Payment Amount ($) *", min_value=1.0, max_value=due_val, value=due_val, step=10.0)
                p_method = st.selectbox("Payment Method", ["Cash", "Online", "Card", "Cheque", "Bank Transfer"])
                p_ref = st.text_input("Transaction / Cheque Reference", placeholder="e.g. TXN-984210")
                p_notes = st.text_input("Payment Notes", placeholder="Optional remarks...")

                if st.form_submit_button("Record Payment & Generate Receipt", type="primary"):
                    rec_count = fetch_query("SELECT COUNT(*) as c FROM fee_payments")['c'][0] + 5001
                    rec_no = f"REC-2025-{rec_count}"
                    
                    execute_cmd("""
                        INSERT INTO fee_payments (invoice_id, receipt_no, amount_paid, payment_date, payment_method, transaction_ref, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (inv_id, rec_no, p_amt, str(datetime.now().date()), p_method, p_ref, p_notes))

                    # Update invoice
                    inv_data = fetch_query("SELECT amount, paid_amount FROM fee_invoices WHERE id = ?", (inv_id,)).iloc[0]
                    new_paid = inv_data['paid_amount'] + p_amt
                    new_stat = 'Paid' if new_paid >= inv_data['amount'] else 'Partial'

                    execute_cmd("UPDATE fee_invoices SET paid_amount = ?, status = ? WHERE id = ?", (new_paid, new_stat, inv_id))
                    st.success(f"Payment of **${p_amt:,.2f}** recorded! Receipt Number: **{rec_no}**")
                    st.rerun()

# ==========================================
# 7. CLASSES & SUBJECTS
# ==========================================
elif nav == "🏛️ Classes & Subjects":
    st.markdown("<div class='main-header'>Classes & Curriculum Management</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Classrooms, section distribution, and subject catalog</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Classrooms & Sections")
        cls_df = fetch_query("""
            SELECT c.name as [Class], c.grade_level as [Grade], c.section as [Section],
                   c.room_number as [Room], t.full_name as [Class Teacher],
                   COUNT(s.id) as [Students]
            FROM classes c
            LEFT JOIN teachers t ON c.class_teacher_id = t.id
            LEFT JOIN students s ON c.id = s.class_id
            GROUP BY c.id
        """)
        st.dataframe(cls_df, use_container_width=True, hide_index=True)

    with c2:
        st.subheader("Curriculum & Subjects")
        subs_df = fetch_query("""
            SELECT sub.code as [Code], sub.name as [Subject Title],
                   sub.department as [Department], sub.credits as [Credits],
                   t.full_name as [Instructor]
            FROM subjects sub
            LEFT JOIN teachers t ON sub.teacher_id = t.id
        """)
        st.dataframe(subs_df, use_container_width=True, hide_index=True)

# ==========================================
# 8. FACULTY DIRECTORY
# ==========================================
elif nav == "👨‍🏫 Faculty Directory":
    st.markdown("<div class='main-header'>Teaching Faculty & Staff Directory</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Instructors, department chairs, and academic advisors</div>", unsafe_allow_html=True)

    teachers = fetch_query("""
        SELECT t.employee_id as [ID], t.full_name as [Faculty Name],
               t.department as [Department], t.designation as [Designation],
               t.qualification as [Degree], t.email as [Email], t.phone as [Phone]
        FROM teachers t
        ORDER BY t.department, t.full_name
    """)
    st.dataframe(teachers, use_container_width=True, hide_index=True)

    with st.expander("➕ Register New Faculty Member"):
        with st.form("new_faculty_form"):
            f_id = st.text_input("Employee ID *", placeholder="e.g. TCH-1009")
            f_name = st.text_input("Full Name *", placeholder="e.g. Dr. John Doe")
            f_email = st.text_input("Email *")
            f_phone = st.text_input("Phone Number")
            f_dept = st.text_input("Department *", placeholder="e.g. Mathematics")
            f_desig = st.text_input("Designation *", placeholder="e.g. Senior Lecturer")
            f_qual = st.text_input("Qualification", placeholder="e.g. Ph.D. in Physics")

            if st.form_submit_button("Add Faculty Member"):
                if f_id and f_name and f_email:
                    execute_cmd("""
                        INSERT INTO teachers (employee_id, full_name, email, phone, department, designation, qualification, join_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (f_id, f_name, f_email, f_phone, f_dept, f_desig, f_qual, str(datetime.now().date())))
                    st.success(f"Faculty member {f_name} registered!")
                    st.rerun()

# ==========================================
# 9. NOTICEBOARD
# ==========================================
elif nav == "📢 Noticeboard":
    st.markdown("<div class='main-header'>Institutional Noticeboard & Advisories</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Broadcast communications, urgency bulletins, and academic circulars</div>", unsafe_allow_html=True)

    with st.expander("➕ Publish Announcement"):
        with st.form("new_notice_form"):
            n_title = st.text_input("Notice Title *")
            n_aud = st.selectbox("Target Audience", ["All", "Students", "Teachers", "Parents"])
            n_prio = st.selectbox("Priority Level", ["Normal", "Urgent", "Low"])
            n_body = st.text_area("Announcement Details *")

            if st.form_submit_button("Publish to Noticeboard", type="primary"):
                if n_title and n_body:
                    execute_cmd("INSERT INTO announcements (title, content, target_audience, priority, created_at) VALUES (?, ?, ?, ?, ?)",
                                (n_title, n_body, n_aud, n_prio, str(datetime.now().date())))
                    st.success("Notice published successfully!")
                    st.rerun()

    notices = fetch_query("SELECT * FROM announcements ORDER BY id DESC")
    for _, n in notices.iterrows():
        st.markdown(f"""
        <div style="background: #ffffff; padding: 1.2rem; border-radius: 1rem; border-left: 5px solid {'#ef4444' if n['priority'] == 'Urgent' else '#3b82f6'}; margin-bottom: 1rem; border-top: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 0.75rem; font-weight: 700; color: {'#b91c1c' if n['priority'] == 'Urgent' else '#1d4ed8'}; text-transform: uppercase;">
                    {n['priority']} &bull; Target: {n['target_audience']}
                </span>
                <span style="font-size: 0.75rem; color: #94a3b8;">{n['created_at']}</span>
            </div>
            <h4 style="margin: 0; color: #0f172a;">{n['title']}</h4>
            <p style="margin-top: 0.5rem; color: #475569; font-size: 0.9rem;">{n['content']}</p>
        </div>
        """, unsafe_allow_html=True)
