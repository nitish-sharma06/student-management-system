import os
import csv
import io
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, url_for, flash, jsonify, Response, send_file
)
import config
from database import query_db, execute_db, execute_many_db, init_db
from pdf_generator import generate_report_card_pdf, generate_fee_receipt_pdf

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# Context processor for global template variables
@app.context_processor
def inject_global_settings():
    return {
        'school_name': config.SCHOOL_NAME,
        'school_tagline': config.SCHOOL_TAGLINE,
        'school_address': config.SCHOOL_ADDRESS,
        'school_contact': config.SCHOOL_CONTACT,
        'academic_year': config.SCHOOL_ACADEMIC_YEAR,
        'now': datetime.now()
    }

# Template filters
@app.template_filter('currency')
def currency_filter(val):
    try:
        return f"${float(val):,.2f}"
    except (ValueError, TypeError):
        return "$0.00"

@app.template_filter('percent')
def percent_filter(val):
    try:
        return f"{float(val):.1f}%"
    except (ValueError, TypeError):
        return "0.0%"

def calculate_grade(marks, max_marks=100.0):
    pct = (marks / max_marks) * 100 if max_marks > 0 else 0
    if pct >= 90: return 'A+', 'Outstanding'
    elif pct >= 80: return 'A', 'Excellent'
    elif pct >= 70: return 'B', 'Very Good'
    elif pct >= 60: return 'C', 'Good'
    elif pct >= 50: return 'D', 'Satisfactory'
    else: return 'F', 'Needs Improvement'

# ==========================================
# 1. DASHBOARD & ANALYTICS
# ==========================================
@app.route('/')
def dashboard():
    total_students = query_db("SELECT COUNT(*) as count FROM students WHERE status = 'Active'", one=True)['count']
    total_teachers = query_db("SELECT COUNT(*) as count FROM teachers WHERE status = 'Active'", one=True)['count']
    total_classes = query_db("SELECT COUNT(*) as count FROM classes", one=True)['count']
    total_courses = query_db("SELECT COUNT(*) as count FROM subjects", one=True)['count']

    # Financial KPIs
    financials = query_db("""
        SELECT 
            COALESCE(SUM(amount), 0) as total_invoiced,
            COALESCE(SUM(paid_amount), 0) as total_collected
        FROM fee_invoices
    """, one=True)
    total_invoiced = financials['total_invoiced']
    total_collected = financials['total_collected']
    total_pending = total_invoiced - total_collected

    # Attendance overall rate
    att_stats = query_db("""
        SELECT 
            COUNT(*) as total_records,
            SUM(CASE WHEN status IN ('Present', 'Late') THEN 1 ELSE 0 END) as attended
        FROM attendance
    """, one=True)
    total_records = att_stats['total_records']
    attended = att_stats['attended'] or 0
    overall_attendance = (attended / total_records * 100) if total_records > 0 else 0.0

    # Recent items
    recent_students = query_db("""
        SELECT s.*, c.name as class_name
        FROM students s
        LEFT JOIN classes c ON s.class_id = c.id
        ORDER BY s.id DESC LIMIT 5
    """)
    recent_payments = query_db("""
        SELECT p.*, i.invoice_no, s.first_name, s.last_name, s.admission_no
        FROM fee_payments p
        JOIN fee_invoices i ON p.invoice_id = i.id
        JOIN students s ON i.student_id = s.id
        ORDER BY p.id DESC LIMIT 5
    """)
    recent_notices = query_db("SELECT * FROM announcements ORDER BY id DESC LIMIT 4")

    return render_template(
        'dashboard.html',
        total_students=total_students,
        total_teachers=total_teachers,
        total_classes=total_classes,
        total_courses=total_courses,
        total_invoiced=total_invoiced,
        total_collected=total_collected,
        total_pending=total_pending,
        overall_attendance=overall_attendance,
        recent_students=recent_students,
        recent_payments=recent_payments,
        recent_notices=recent_notices
    )

@app.route('/api/dashboard/stats')
def api_dashboard_stats():
    # Grade distribution in latest exams
    grades_count = query_db("""
        SELECT grade_letter, COUNT(*) as count
        FROM grades
        WHERE grade_letter IS NOT NULL
        GROUP BY grade_letter
        ORDER BY grade_letter
    """)
    
    # Attendance breakdown
    att_breakdown = query_db("""
        SELECT status, COUNT(*) as count
        FROM attendance
        GROUP BY status
    """)
    
    # Class student count
    class_students = query_db("""
        SELECT c.name as class_name, COUNT(s.id) as student_count
        FROM classes c
        LEFT JOIN students s ON c.id = s.class_id
        GROUP BY c.id
    """)

    return jsonify({
        'grades': [{'label': r['grade_letter'], 'value': r['count']} for r in grades_count],
        'attendance': [{'label': r['status'], 'value': r['count']} for r in att_breakdown],
        'classes': [{'label': r['class_name'], 'value': r['student_count']} for r in class_students]
    })

# ==========================================
# 2. STUDENTS LIFECYCLE
# ==========================================
@app.route('/students')
def students_list():
    search = request.args.get('q', '').strip()
    class_id = request.args.get('class_id', '').strip()
    status = request.args.get('status', '').strip()
    gender = request.args.get('gender', '').strip()

    query = """
        SELECT s.*, c.name as class_name
        FROM students s
        LEFT JOIN classes c ON s.class_id = c.id
        WHERE 1=1
    """
    params = []

    if search:
        query += " AND (s.first_name LIKE ? OR s.last_name LIKE ? OR s.admission_no LIKE ? OR s.roll_no LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term])

    if class_id:
        query += " AND s.class_id = ?"
        params.append(class_id)

    if status:
        query += " AND s.status = ?"
        params.append(status)

    if gender:
        query += " AND s.gender = ?"
        params.append(gender)

    query += " ORDER BY s.class_id ASC, CAST(s.roll_no AS INTEGER) ASC, s.first_name ASC"

    students = query_db(query, params)
    classes = query_db("SELECT * FROM classes ORDER BY grade_level, section")

    return render_template(
        'students/index.html',
        students=students,
        classes=classes,
        search=search,
        selected_class=class_id,
        selected_status=status,
        selected_gender=gender,
        total_count=len(students)
    )

@app.route('/students/new', methods=['GET', 'POST'])
def student_create():
    classes = query_db("SELECT * FROM classes ORDER BY grade_level, section")
    if request.method == 'POST':
        adm_no = request.form.get('admission_no', '').strip()
        if not adm_no:
            count = query_db("SELECT COUNT(*) as c FROM students", one=True)['c'] + 1
            adm_no = f"ADM-2025-{count:03d}"

        roll_no = request.form.get('roll_no', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        gender = request.form.get('gender', 'Male')
        dob = request.form.get('dob', '')
        blood_group = request.form.get('blood_group', '')
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        address = request.form.get('address', '')
        class_id = request.form.get('class_id')
        adm_date = request.form.get('admission_date') or datetime.now().strftime("%Y-%m-%d")
        parent_name = request.form.get('parent_name', '')
        parent_relation = request.form.get('parent_relation', 'Parent')
        parent_phone = request.form.get('parent_phone', '')
        parent_email = request.form.get('parent_email', '')
        status = request.form.get('status', 'Active')
        avatar_url = f"https://api.dicebear.com/7.x/bottts/svg?seed={first_name}{last_name}"

        try:
            student_id = execute_db("""
                INSERT INTO students (
                    admission_no, roll_no, first_name, last_name, gender, dob, blood_group,
                    email, phone, address, class_id, admission_date, parent_name, parent_relation,
                    parent_phone, parent_email, status, avatar_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                adm_no, roll_no, first_name, last_name, gender, dob, blood_group,
                email, phone, address, class_id, adm_date, parent_name, parent_relation,
                parent_phone, parent_email, status, avatar_url
            ))
            flash(f"Student {first_name} {last_name} enrolled successfully with Admission No {adm_no}!", "success")
            return redirect(url_for('student_detail', id=student_id))
        except Exception as e:
            flash(f"Error enrolling student: {str(e)}", "danger")

    return render_template('students/form.html', student=None, classes=classes)

@app.route('/students/<int:id>')
def student_detail(id):
    student = query_db("""
        SELECT s.*, c.name as class_name, c.room_number, c.grade_level, c.section,
               t.full_name as class_teacher_name, t.email as class_teacher_email
        FROM students s
        LEFT JOIN classes c ON s.class_id = c.id
        LEFT JOIN teachers t ON c.class_teacher_id = t.id
        WHERE s.id = ?
    """, (id,), one=True)

    if not student:
        flash("Student not found", "warning")
        return redirect(url_for('students_list'))

    # Attendance Stats
    att_stats = query_db("""
        SELECT 
            COUNT(*) as total_days,
            SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_days,
            SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent_days,
            SUM(CASE WHEN status = 'Late' THEN 1 ELSE 0 END) as late_days,
            SUM(CASE WHEN status = 'Excused' THEN 1 ELSE 0 END) as excused_days
        FROM attendance
        WHERE student_id = ?
    """, (id,), one=True)

    total_days = att_stats['total_days'] or 0
    present_equiv = (att_stats['present_days'] or 0) + (att_stats['late_days'] or 0)
    attendance_rate = (present_equiv / total_days * 100) if total_days > 0 else 0.0

    recent_attendance = query_db("""
        SELECT * FROM attendance WHERE student_id = ? ORDER BY date DESC LIMIT 10
    """, (id,))

    # Exam Grades
    grades = query_db("""
        SELECT g.*, sub.code as subject_code, sub.name as subject_name, ex.name as exam_name, ex.academic_year
        FROM grades g
        JOIN subjects sub ON g.subject_id = sub.id
        JOIN exams ex ON g.exam_id = ex.id
        WHERE g.student_id = ?
        ORDER BY ex.start_date DESC, sub.name ASC
    """, (id,))

    # Fee Invoices
    invoices = query_db("""
        SELECT fi.*, ft.name as fee_type_name
        FROM fee_invoices fi
        JOIN fee_types ft ON fi.fee_type_id = ft.id
        WHERE fi.student_id = ?
        ORDER BY fi.id DESC
    """, (id,))

    return render_template(
        'students/profile.html',
        student=student,
        att_stats=att_stats,
        attendance_rate=attendance_rate,
        recent_attendance=recent_attendance,
        grades=grades,
        invoices=invoices
    )

@app.route('/students/<int:id>/edit', methods=['GET', 'POST'])
def student_edit(id):
    student = query_db("SELECT * FROM students WHERE id = ?", (id,), one=True)
    if not student:
        flash("Student not found", "warning")
        return redirect(url_for('students_list'))

    classes = query_db("SELECT * FROM classes ORDER BY grade_level, section")

    if request.method == 'POST':
        roll_no = request.form.get('roll_no')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        gender = request.form.get('gender')
        dob = request.form.get('dob')
        blood_group = request.form.get('blood_group')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        class_id = request.form.get('class_id')
        parent_name = request.form.get('parent_name')
        parent_relation = request.form.get('parent_relation')
        parent_phone = request.form.get('parent_phone')
        parent_email = request.form.get('parent_email')
        status = request.form.get('status')

        try:
            execute_db("""
                UPDATE students SET
                    roll_no = ?, first_name = ?, last_name = ?, gender = ?, dob = ?,
                    blood_group = ?, email = ?, phone = ?, address = ?, class_id = ?,
                    parent_name = ?, parent_relation = ?, parent_phone = ?, parent_email = ?, status = ?
                WHERE id = ?
            """, (
                roll_no, first_name, last_name, gender, dob, blood_group, email, phone,
                address, class_id, parent_name, parent_relation, parent_phone, parent_email, status, id
            ))
            flash(f"Student profile for {first_name} {last_name} updated successfully!", "success")
            return redirect(url_for('student_detail', id=id))
        except Exception as e:
            flash(f"Error updating student: {str(e)}", "danger")

    return render_template('students/form.html', student=student, classes=classes)

@app.route('/students/<int:id>/delete', methods=['POST'])
def student_delete(id):
    student = query_db("SELECT * FROM students WHERE id = ?", (id,), one=True)
    if student:
        execute_db("DELETE FROM students WHERE id = ?", (id,))
        flash(f"Student {student['first_name']} {student['last_name']} removed successfully.", "info")
    return redirect(url_for('students_list'))

@app.route('/students/<int:id>/id-card')
def student_id_card(id):
    student = query_db("""
        SELECT s.*, c.name as class_name
        FROM students s
        LEFT JOIN classes c ON s.class_id = c.id
        WHERE s.id = ?
    """, (id,), one=True)
    if not student:
        flash("Student not found", "warning")
        return redirect(url_for('students_list'))
    return render_template('students/id_card.html', student=student)

@app.route('/students/export/csv')
def export_students_csv():
    students = query_db("""
        SELECT s.admission_no, s.roll_no, s.first_name, s.last_name, s.gender, s.dob,
               s.blood_group, s.email, s.phone, c.name as class_name, s.parent_name,
               s.parent_phone, s.status, s.admission_date
        FROM students s
        LEFT JOIN classes c ON s.class_id = c.id
        ORDER BY s.class_id ASC, s.first_name ASC
    """)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Admission No", "Roll No", "First Name", "Last Name", "Gender", "Date of Birth",
        "Blood Group", "Email", "Phone", "Class", "Parent Name", "Parent Phone", "Status", "Admission Date"
    ])
    for s in students:
        writer.writerow([
            s['admission_no'], s['roll_no'], s['first_name'], s['last_name'], s['gender'],
            s['dob'], s['blood_group'], s['email'], s['phone'], s['class_name'],
            s['parent_name'], s['parent_phone'], s['status'], s['admission_date']
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=Students_Directory_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

# ==========================================
# 3. ATTENDANCE MANAGEMENT
# ==========================================
@app.route('/attendance')
def attendance_index():
    class_id = request.args.get('class_id', '1')
    date_str = request.args.get('date', datetime.now().strftime("%Y-%m-%d"))

    classes = query_db("SELECT * FROM classes ORDER BY grade_level, section")
    current_class = query_db("SELECT * FROM classes WHERE id = ?", (class_id,), one=True)

    # Fetch students in this class with their attendance status for this date
    students_attendance = query_db("""
        SELECT s.id as student_id, s.admission_no, s.roll_no, s.first_name, s.last_name, s.gender,
               COALESCE(a.status, 'Present') as att_status,
               a.remarks as att_remarks
        FROM students s
        LEFT JOIN attendance a ON s.id = a.student_id AND a.date = ?
        WHERE s.class_id = ? AND s.status = 'Active'
        ORDER BY CAST(s.roll_no AS INTEGER) ASC, s.first_name ASC
    """, (date_str, class_id))

    return render_template(
        'attendance/mark.html',
        classes=classes,
        current_class=current_class,
        selected_class_id=int(class_id),
        selected_date=date_str,
        records=students_attendance
    )

@app.route('/attendance/save', methods=['POST'])
def attendance_save():
    class_id = request.form.get('class_id')
    date_str = request.form.get('date')

    # Extract all student attendance form items
    student_ids = request.form.getlist('student_id[]')

    for s_id in student_ids:
        status = request.form.get(f"status_{s_id}", 'Present')
        remarks = request.form.get(f"remarks_{s_id}", '').strip()

        # UPSERT attendance
        execute_db("""
            INSERT INTO attendance (student_id, class_id, date, status, remarks)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(student_id, date) DO UPDATE SET
                status = excluded.status,
                remarks = excluded.remarks,
                class_id = excluded.class_id
        """, (s_id, class_id, date_str, status, remarks))

    flash(f"Attendance for Class saved successfully for {date_str}!", "success")
    return redirect(url_for('attendance_index', class_id=class_id, date=date_str))

@app.route('/attendance/report')
def attendance_report():
    class_id = request.args.get('class_id', '1')
    classes = query_db("SELECT * FROM classes ORDER BY grade_level, section")
    current_class = query_db("SELECT * FROM classes WHERE id = ?", (class_id,), one=True)

    # Class summary
    student_summaries = query_db("""
        SELECT 
            s.id, s.admission_no, s.roll_no, s.first_name, s.last_name,
            COUNT(a.id) as total_days,
            SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_count,
            SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_count,
            SUM(CASE WHEN a.status = 'Late' THEN 1 ELSE 0 END) as late_count,
            SUM(CASE WHEN a.status = 'Excused' THEN 1 ELSE 0 END) as excused_count
        FROM students s
        LEFT JOIN attendance a ON s.id = a.student_id
        WHERE s.class_id = ? AND s.status = 'Active'
        GROUP BY s.id
        ORDER BY CAST(s.roll_no AS INTEGER) ASC
    """, (class_id,))

    processed = []
    for row in student_summaries:
        tot = row['total_days'] or 0
        pres = (row['present_count'] or 0) + (row['late_count'] or 0)
        pct = (pres / tot * 100) if tot > 0 else 0.0
        processed.append({
            **dict(row),
            'rate': pct
        })

    return render_template(
        'attendance/report.html',
        classes=classes,
        current_class=current_class,
        selected_class_id=int(class_id),
        summaries=processed
    )

# ==========================================
# 4. ACADEMICS: CLASSES & SUBJECTS
# ==========================================
@app.route('/academics/classes')
def classes_list():
    classes = query_db("""
        SELECT c.*, t.full_name as teacher_name, COUNT(s.id) as student_count
        FROM classes c
        LEFT JOIN teachers t ON c.class_teacher_id = t.id
        LEFT JOIN students s ON c.id = s.class_id
        GROUP BY c.id
        ORDER BY c.grade_level, c.section
    """)
    teachers = query_db("SELECT * FROM teachers ORDER BY full_name")
    return render_template('academics/classes.html', classes=classes, teachers=teachers)

@app.route('/academics/classes/new', methods=['POST'])
def class_create():
    name = request.form.get('name')
    grade_level = request.form.get('grade_level')
    section = request.form.get('section')
    room_number = request.form.get('room_number')
    teacher_id = request.form.get('class_teacher_id') or None

    try:
        execute_db("""
            INSERT INTO classes (name, grade_level, section, room_number, class_teacher_id)
            VALUES (?, ?, ?, ?, ?)
        """, (name, grade_level, section, room_number, teacher_id))
        flash(f"Class '{name}' created successfully!", "success")
    except Exception as e:
        flash(f"Error creating class: {str(e)}", "danger")

    return redirect(url_for('classes_list'))

@app.route('/academics/subjects')
def subjects_list():
    subjects = query_db("""
        SELECT sub.*, t.full_name as teacher_name
        FROM subjects sub
        LEFT JOIN teachers t ON sub.teacher_id = t.id
        ORDER BY sub.department, sub.name
    """)
    teachers = query_db("SELECT * FROM teachers ORDER BY full_name")
    return render_template('academics/subjects.html', subjects=subjects, teachers=teachers)

@app.route('/academics/subjects/new', methods=['POST'])
def subject_create():
    code = request.form.get('code')
    name = request.form.get('name')
    department = request.form.get('department')
    credits = request.form.get('credits', 3)
    teacher_id = request.form.get('teacher_id') or None

    try:
        execute_db("""
            INSERT INTO subjects (code, name, department, credits, teacher_id)
            VALUES (?, ?, ?, ?, ?)
        """, (code, name, department, credits, teacher_id))
        flash(f"Subject '{name}' ({code}) added successfully!", "success")
    except Exception as e:
        flash(f"Error adding subject: {str(e)}", "danger")

    return redirect(url_for('subjects_list'))

# ==========================================
# 5. EXAMINATIONS & MARKS
# ==========================================
@app.route('/examinations')
def examinations_list():
    exams = query_db("SELECT * FROM exams ORDER BY start_date DESC")
    classes = query_db("SELECT * FROM classes ORDER BY grade_level, section")
    subjects = query_db("SELECT * FROM subjects ORDER BY name")
    return render_template('examinations/index.html', exams=exams, classes=classes, subjects=subjects)

@app.route('/examinations/new', methods=['POST'])
def exam_create():
    name = request.form.get('name')
    exam_type = request.form.get('exam_type')
    academic_year = request.form.get('academic_year') or config.SCHOOL_ACADEMIC_YEAR
    term = request.form.get('term')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    try:
        execute_db("""
            INSERT INTO exams (name, exam_type, academic_year, term, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, exam_type, academic_year, term, start_date, end_date))
        flash(f"Examination '{name}' scheduled successfully!", "success")
    except Exception as e:
        flash(f"Error scheduling exam: {str(e)}", "danger")

    return redirect(url_for('examinations_list'))

@app.route('/examinations/<int:exam_id>/marks')
def marks_entry(exam_id):
    exam = query_db("SELECT * FROM exams WHERE id = ?", (exam_id,), one=True)
    if not exam:
        flash("Exam not found", "warning")
        return redirect(url_for('examinations_list'))

    class_id = request.args.get('class_id', '1')
    subject_id = request.args.get('subject_id', '1')

    classes = query_db("SELECT * FROM classes ORDER BY grade_level, section")
    subjects = query_db("SELECT * FROM subjects ORDER BY name")
    current_subject = query_db("SELECT * FROM subjects WHERE id = ?", (subject_id,), one=True)

    # Students and existing marks
    students_marks = query_db("""
        SELECT s.id as student_id, s.admission_no, s.roll_no, s.first_name, s.last_name,
               g.marks_obtained, g.max_marks, g.grade_letter, g.remarks
        FROM students s
        LEFT JOIN grades g ON s.id = g.student_id AND g.exam_id = ? AND g.subject_id = ?
        WHERE s.class_id = ? AND s.status = 'Active'
        ORDER BY CAST(s.roll_no AS INTEGER) ASC
    """, (exam_id, subject_id, class_id))

    return render_template(
        'examinations/marks_entry.html',
        exam=exam,
        classes=classes,
        subjects=subjects,
        current_subject=current_subject,
        selected_class_id=int(class_id),
        selected_subject_id=int(subject_id),
        records=students_marks
    )

@app.route('/examinations/<int:exam_id>/marks/save', methods=['POST'])
def marks_save(exam_id):
    class_id = request.form.get('class_id')
    subject_id = request.form.get('subject_id')
    max_marks = float(request.form.get('max_marks', 100.0))

    student_ids = request.form.getlist('student_id[]')

    for s_id in student_ids:
        raw_marks = request.form.get(f"marks_{s_id}")
        remarks = request.form.get(f"remarks_{s_id}", '').strip()

        if raw_marks is not None and raw_marks.strip() != "":
            marks = float(raw_marks)
            grade_let, auto_rem = calculate_grade(marks, max_marks)
            rem = remarks if remarks else auto_rem

            execute_db("""
                INSERT INTO grades (student_id, exam_id, subject_id, marks_obtained, max_marks, grade_letter, remarks)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(student_id, exam_id, subject_id) DO UPDATE SET
                    marks_obtained = excluded.marks_obtained,
                    max_marks = excluded.max_marks,
                    grade_letter = excluded.grade_letter,
                    remarks = excluded.remarks
            """, (s_id, exam_id, subject_id, marks, max_marks, grade_let, rem))

    flash("Examination marks recorded and saved successfully!", "success")
    return redirect(url_for('marks_entry', exam_id=exam_id, class_id=class_id, subject_id=subject_id))

@app.route('/examinations/report-card/<int:student_id>/<int:exam_id>')
def report_card(student_id, exam_id):
    student = query_db("""
        SELECT s.*, c.name as class_name, t.full_name as class_teacher_name
        FROM students s
        LEFT JOIN classes c ON s.class_id = c.id
        LEFT JOIN teachers t ON c.class_teacher_id = t.id
        WHERE s.id = ?
    """, (student_id,), one=True)

    exam = query_db("SELECT * FROM exams WHERE id = ?", (exam_id,), one=True)
    if not student or not exam:
        flash("Report card record not found.", "warning")
        return redirect(url_for('examinations_list'))

    grades = query_db("""
        SELECT g.*, sub.code as subject_code, sub.name as subject_name, sub.credits
        FROM grades g
        JOIN subjects sub ON g.subject_id = sub.id
        WHERE g.student_id = ? AND g.exam_id = ?
        ORDER BY sub.name ASC
    """, (student_id, exam_id))

    total_obtained = sum(g['marks_obtained'] for g in grades)
    total_max = sum(g['max_marks'] for g in grades)
    pct = (total_obtained / total_max * 100) if total_max > 0 else 0
    overall_grade, overall_remark = calculate_grade(total_obtained, total_max if total_max > 0 else 100)

    return render_template(
        'examinations/report_card.html',
        student=student,
        exam=exam,
        grades=grades,
        total_obtained=total_obtained,
        total_max=total_max,
        percentage=pct,
        overall_grade=overall_grade,
        overall_remark=overall_remark
    )

@app.route('/examinations/report-card/<int:student_id>/<int:exam_id>/pdf')
def report_card_pdf(student_id, exam_id):
    student = query_db("""
        SELECT s.*, c.name as class_name
        FROM students s
        LEFT JOIN classes c ON s.class_id = c.id
        WHERE s.id = ?
    """, (student_id,), one=True)
    exam = query_db("SELECT * FROM exams WHERE id = ?", (exam_id,), one=True)
    grades = query_db("""
        SELECT g.*, sub.code as subject_code, sub.name as subject_name
        FROM grades g
        JOIN subjects sub ON g.subject_id = sub.id
        WHERE g.student_id = ? AND g.exam_id = ?
        ORDER BY sub.name ASC
    """, (student_id, exam_id))

    pdf_bytes = generate_report_card_pdf(student, exam, grades)
    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'inline; filename=ReportCard_{student["admission_no"]}_{exam["term"]}.pdf'}
    )

# ==========================================
# 6. FEE MANAGEMENT
# ==========================================
@app.route('/fees')
def fees_list():
    status_filter = request.args.get('status', '').strip()
    search = request.args.get('q', '').strip()

    query = """
        SELECT fi.*, ft.name as fee_type_name, s.first_name, s.last_name, s.admission_no, s.roll_no, c.name as class_name
        FROM fee_invoices fi
        JOIN fee_types ft ON fi.fee_type_id = ft.id
        JOIN students s ON fi.student_id = s.id
        LEFT JOIN classes c ON s.class_id = c.id
        WHERE 1=1
    """
    params = []

    if status_filter:
        query += " AND fi.status = ?"
        params.append(status_filter)

    if search:
        query += " AND (s.first_name LIKE ? OR s.last_name LIKE ? OR fi.invoice_no LIKE ? OR s.admission_no LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term])

    query += " ORDER BY fi.id DESC"
    invoices = query_db(query, params)

    # Summary KPIs
    kpis = query_db("""
        SELECT 
            COALESCE(SUM(amount), 0) as total_invoiced,
            COALESCE(SUM(paid_amount), 0) as total_collected,
            COUNT(*) as total_invoices,
            SUM(CASE WHEN status = 'Unpaid' THEN 1 ELSE 0 END) as unpaid_count
        FROM fee_invoices
    """, one=True)

    fee_types = query_db("SELECT * FROM fee_types ORDER BY name")
    students = query_db("SELECT id, admission_no, roll_no, first_name, last_name FROM students WHERE status = 'Active' ORDER BY first_name")

    return render_template(
        'fees/index.html',
        invoices=invoices,
        kpis=kpis,
        fee_types=fee_types,
        students=students,
        selected_status=status_filter,
        search=search
    )

@app.route('/fees/new-invoice', methods=['POST'])
def fee_invoice_create():
    student_id = request.form.get('student_id')
    fee_type_id = request.form.get('fee_type_id')
    amount = float(request.form.get('amount'))
    due_date = request.form.get('due_date')

    inv_count = query_db("SELECT COUNT(*) as c FROM fee_invoices", one=True)['c'] + 1001
    invoice_no = f"INV-2025-{inv_count}"
    created_at = datetime.now().strftime("%Y-%m-%d")

    try:
        execute_db("""
            INSERT INTO fee_invoices (invoice_no, student_id, fee_type_id, amount, paid_amount, due_date, status, created_at)
            VALUES (?, ?, ?, ?, 0.0, ?, 'Unpaid', ?)
        """, (invoice_no, student_id, fee_type_id, amount, due_date, created_at))
        flash(f"Invoice {invoice_no} issued successfully!", "success")
    except Exception as e:
        flash(f"Error issuing invoice: {str(e)}", "danger")

    return redirect(url_for('fees_list'))

@app.route('/fees/record-payment', methods=['POST'])
def fee_payment_record():
    invoice_id = request.form.get('invoice_id')
    amount_paid = float(request.form.get('amount_paid', 0))
    payment_method = request.form.get('payment_method', 'Cash')
    payment_date = request.form.get('payment_date') or datetime.now().strftime("%Y-%m-%d")
    transaction_ref = request.form.get('transaction_ref', '').strip()
    notes = request.form.get('notes', '').strip()

    invoice = query_db("SELECT * FROM fee_invoices WHERE id = ?", (invoice_id,), one=True)
    if not invoice:
        flash("Invoice not found", "danger")
        return redirect(url_for('fees_list'))

    rec_count = query_db("SELECT COUNT(*) as c FROM fee_payments", one=True)['c'] + 5001
    receipt_no = f"REC-2025-{rec_count}"

    payment_id = execute_db("""
        INSERT INTO fee_payments (invoice_id, receipt_no, amount_paid, payment_date, payment_method, transaction_ref, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (invoice_id, receipt_no, amount_paid, payment_date, payment_method, transaction_ref, notes))

    # Update invoice paid_amount and status
    new_paid = float(invoice['paid_amount']) + amount_paid
    total_due = float(invoice['amount'])
    new_status = 'Paid' if new_paid >= total_due else 'Partial'

    execute_db("""
        UPDATE fee_invoices
        SET paid_amount = ?, status = ?
        WHERE id = ?
    """, (new_paid, new_status, invoice_id))

    flash(f"Payment of ${amount_paid:,.2f} recorded! Receipt: {receipt_no}", "success")
    return redirect(url_for('fee_receipt', payment_id=payment_id))

@app.route('/fees/receipt/<int:payment_id>')
def fee_receipt(payment_id):
    payment = query_db("SELECT * FROM fee_payments WHERE id = ?", (payment_id,), one=True)
    if not payment:
        flash("Receipt record not found", "warning")
        return redirect(url_for('fees_list'))

    invoice = query_db("""
        SELECT fi.*, ft.name as fee_type_name
        FROM fee_invoices fi
        JOIN fee_types ft ON fi.fee_type_id = ft.id
        WHERE fi.id = ?
    """, (payment['invoice_id'],), one=True)

    student = query_db("""
        SELECT s.*, c.name as class_name
        FROM students s
        LEFT JOIN classes c ON s.class_id = c.id
        WHERE s.id = ?
    """, (invoice['student_id'],), one=True)

    return render_template('fees/receipt.html', payment=payment, invoice=invoice, student=student)

@app.route('/fees/receipt/<int:payment_id>/pdf')
def fee_receipt_pdf(payment_id):
    payment = query_db("SELECT * FROM fee_payments WHERE id = ?", (payment_id,), one=True)
    invoice = query_db("""
        SELECT fi.*, ft.name as fee_type_name
        FROM fee_invoices fi
        JOIN fee_types ft ON fi.fee_type_id = ft.id
        WHERE fi.id = ?
    """, (payment['invoice_id'],), one=True)
    student = query_db("""
        SELECT s.*, c.name as class_name
        FROM students s
        LEFT JOIN classes c ON s.class_id = c.id
        WHERE s.id = ?
    """, (invoice['student_id'],), one=True)

    pdf_bytes = generate_fee_receipt_pdf(payment, invoice, student)
    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'inline; filename=Receipt_{payment["receipt_no"]}.pdf'}
    )

# ==========================================
# 7. TEACHERS & FACULTY DIRECTORY
# ==========================================
@app.route('/teachers')
def teachers_list():
    dept = request.args.get('department', '').strip()
    search = request.args.get('q', '').strip()

    query = """
        SELECT t.*, 
               GROUP_CONCAT(sub.name, ', ') as subjects_taught
        FROM teachers t
        LEFT JOIN subjects sub ON t.id = sub.teacher_id
        WHERE 1=1
    """
    params = []

    if dept:
        query += " AND t.department = ?"
        params.append(dept)

    if search:
        query += " AND (t.full_name LIKE ? OR t.employee_id LIKE ? OR t.email LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])

    query += " GROUP BY t.id ORDER BY t.full_name ASC"
    teachers = query_db(query, params)
    departments = query_db("SELECT DISTINCT department FROM teachers ORDER BY department")

    return render_template(
        'teachers/index.html',
        teachers=teachers,
        departments=[d['department'] for d in departments],
        selected_dept=dept,
        search=search
    )

@app.route('/teachers/new', methods=['POST'])
def teacher_create():
    emp_id = request.form.get('employee_id')
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    department = request.form.get('department')
    designation = request.form.get('designation')
    qualification = request.form.get('qualification')
    join_date = request.form.get('join_date') or datetime.now().strftime("%Y-%m-%d")

    try:
        execute_db("""
            INSERT INTO teachers (employee_id, full_name, email, phone, department, designation, qualification, join_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (emp_id, full_name, email, phone, department, designation, qualification, join_date))
        flash(f"Teacher {full_name} added successfully!", "success")
    except Exception as e:
        flash(f"Error adding teacher: {str(e)}", "danger")

    return redirect(url_for('teachers_list'))

# ==========================================
# 8. ANNOUNCEMENTS & NOTICEBOARD
# ==========================================
@app.route('/announcements')
def announcements_list():
    audience = request.args.get('audience', '').strip()
    priority = request.args.get('priority', '').strip()

    query = "SELECT * FROM announcements WHERE 1=1"
    params = []

    if audience:
        query += " AND (target_audience = ? OR target_audience = 'All')"
        params.append(audience)

    if priority:
        query += " AND priority = ?"
        params.append(priority)

    query += " ORDER BY id DESC"
    notices = query_db(query, params)

    return render_template(
        'notices/index.html',
        notices=notices,
        selected_audience=audience,
        selected_priority=priority
    )

@app.route('/announcements/new', methods=['POST'])
def announcement_create():
    title = request.form.get('title')
    content = request.form.get('content')
    target_audience = request.form.get('target_audience', 'All')
    priority = request.form.get('priority', 'Normal')
    created_at = datetime.now().strftime("%Y-%m-%d")

    try:
        execute_db("""
            INSERT INTO announcements (title, content, target_audience, priority, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (title, content, target_audience, priority, created_at))
        flash("Announcement published to noticeboard!", "success")
    except Exception as e:
        flash(f"Error publishing notice: {str(e)}", "danger")

    return redirect(url_for('announcements_list'))

@app.route('/announcements/<int:id>/delete', methods=['POST'])
def announcement_delete(id):
    execute_db("DELETE FROM announcements WHERE id = ?", (id,))
    flash("Announcement deleted.", "info")
    return redirect(url_for('announcements_list'))

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting {config.SCHOOL_NAME} SMS on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
