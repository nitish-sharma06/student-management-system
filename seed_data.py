import sqlite3
import random
from datetime import datetime, timedelta
from database import get_db, init_db

def calculate_grade(marks, max_marks=100.0):
    pct = (marks / max_marks) * 100
    if pct >= 90:
        return 'A+', 'Outstanding'
    elif pct >= 80:
        return 'A', 'Excellent'
    elif pct >= 70:
        return 'B', 'Very Good'
    elif pct >= 60:
        return 'C', 'Good'
    elif pct >= 50:
        return 'D', 'Satisfactory'
    else:
        return 'F', 'Needs Improvement'

def seed():
    init_db()
    conn = get_db()
    cur = conn.cursor()

    # Check if already seeded
    cur.execute("SELECT COUNT(*) FROM students")
    if cur.fetchone()[0] > 0:
        print("Database already contains data. Skipping seed.")
        conn.close()
        return

    print("Seeding database with comprehensive realistic records...")

    # 1. Teachers
    teachers_data = [
        ("TCH-1001", "Dr. Robert Vance", "robert.vance@apexacademy.edu", "+1 (555) 019-2831", "Mathematics", "Head of Department", "Ph.D. in Applied Mathematics", "2018-08-15"),
        ("TCH-1002", "Elena Rostova", "elena.rostova@apexacademy.edu", "+1 (555) 019-4822", "English", "Senior Faculty", "M.A. in English Literature", "2019-09-01"),
        ("TCH-1003", "Dr. Alan Turing-Lee", "alan.lee@apexacademy.edu", "+1 (555) 019-3391", "Computer Science", "Lead Instructor", "Ph.D. in Computer Engineering", "2020-01-10"),
        ("TCH-1004", "Sarah Jenkins", "sarah.jenkins@apexacademy.edu", "+1 (555) 019-7744", "Physics", "Senior Lecturer", "M.Sc. in Physics", "2019-07-20"),
        ("TCH-1005", "Marcus Brody", "marcus.brody@apexacademy.edu", "+1 (555) 019-8812", "Social Studies", "Assistant Professor", "M.A. in World History", "2021-08-12"),
        ("TCH-1006", "Dr. Priya Sharma", "priya.sharma@apexacademy.edu", "+1 (555) 019-9943", "Chemistry", "Senior Lecturer", "Ph.D. in Organic Chemistry", "2020-09-05"),
        ("TCH-1007", "David Kim", "david.kim@apexacademy.edu", "+1 (555) 019-5561", "Biology", "Faculty Member", "M.Sc. in Molecular Biology", "2022-02-01"),
        ("TCH-1008", "Jessica Taylor", "jessica.taylor@apexacademy.edu", "+1 (555) 019-1120", "Physical Education", "Sports Coordinator", "B.P.Ed, Certified Athletics Coach", "2021-03-15")
    ]
    cur.executemany("""
        INSERT INTO teachers (employee_id, full_name, email, phone, department, designation, qualification, join_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, teachers_data)

    # 2. Classes
    classes_data = [
        ("Grade 9-A", "Grade 9", "A", "Room 201", 1),
        ("Grade 10-A", "Grade 10", "A", "Room 202", 2),
        ("Grade 10-B", "Grade 10", "B", "Room 203", 4),
        ("Grade 11-Science", "Grade 11", "Science", "Lab 101", 3),
        ("Grade 12-Science", "Grade 12", "Science", "Lab 102", 6)
    ]
    cur.executemany("""
        INSERT INTO classes (name, grade_level, section, room_number, class_teacher_id)
        VALUES (?, ?, ?, ?, ?)
    """, classes_data)

    # 3. Subjects
    subjects_data = [
        ("MATH-101", "Advanced Mathematics", "Mathematics", 4, 1),
        ("ENG-101", "English Literature & Composition", "English", 3, 2),
        ("CS-101", "Computer Science & Python", "Computer Science", 4, 3),
        ("PHY-101", "Physics & Mechanics", "Physics", 4, 4),
        ("CHEM-101", "Inorganic & Physical Chemistry", "Chemistry", 4, 6),
        ("BIO-101", "Cell Biology & Genetics", "Biology", 3, 7),
        ("HIST-101", "World History & Civics", "Social Studies", 3, 5),
        ("PE-101", "Physical Education & Health", "Physical Education", 2, 8)
    ]
    cur.executemany("""
        INSERT INTO subjects (code, name, department, credits, teacher_id)
        VALUES (?, ?, ?, ?, ?)
    """, subjects_data)

    # Map all subjects to each class
    for class_id in range(1, 6):
        for subject_id in range(1, 9):
            cur.execute("INSERT OR IGNORE INTO class_subjects (class_id, subject_id) VALUES (?, ?)", (class_id, subject_id))

    # 4. Students (30 diverse students across classes)
    first_names = [
        "Liam", "Olivia", "Noah", "Emma", "Oliver", "Ava", "Elijah", "Charlotte", "William", "Sophia",
        "James", "Amelia", "Benjamin", "Isabella", "Lucas", "Mia", "Henry", "Evelyn", "Alexander", "Harper",
        "Mason", "Camila", "Michael", "Gianna", "Ethan", "Abigail", "Daniel", "Luna", "Matthew", "Ella"
    ]
    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
        "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
        "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"
    ]
    genders = ["Male", "Female", "Male", "Female", "Male", "Female", "Male", "Female", "Male", "Female",
               "Male", "Female", "Male", "Female", "Male", "Female", "Male", "Female", "Male", "Female",
               "Male", "Female", "Male", "Female", "Male", "Female", "Male", "Female", "Male", "Female"]
    blood_groups = ["A+", "B+", "O+", "AB+", "A-", "B-", "O-", "AB-"]

    random.seed(42)
    students_data = []

    for i in range(30):
        adm_no = f"ADM-2025-{i+1:03d}"
        roll_no = f"{100 + (i % 10) + 1}"
        fn = first_names[i]
        ln = last_names[i]
        gender = genders[i]
        
        # Class distribution: 6 students per class
        class_id = (i // 6) + 1
        birth_year = 2008 + (class_id - 1)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        dob = f"{birth_year}-{birth_month:02d}-{birth_day:02d}"
        
        email = f"{fn.lower()}.{ln.lower()}{random.randint(10,99)}@student.apexacademy.edu"
        phone = f"+1 (555) {random.randint(100,999)}-{random.randint(1000,9999)}"
        address = f"{random.randint(10, 999)} Maple Crescent, District {class_id}, Tech City"
        bg = blood_groups[i % len(blood_groups)]
        adm_date = f"2024-08-{random.randint(10, 25):02d}"
        
        parent_name = f"Mr. & Mrs. {ln}"
        parent_phone = f"+1 (555) {random.randint(200,899)}-{random.randint(1000,9999)}"
        parent_email = f"parents.{ln.lower()}@gmail.com"
        
        status = "Active"
        if i == 28:
            status = "Inactive"
        elif i == 29:
            status = "Graduated"
            
        avatar_url = f"https://api.dicebear.com/7.x/bottts/svg?seed={fn}{ln}"

        students_data.append((
            adm_no, roll_no, fn, ln, gender, dob, bg, email, phone, address,
            class_id, adm_date, parent_name, 'Parents', parent_phone, parent_email, status, avatar_url
        ))

    cur.executemany("""
        INSERT INTO students (
            admission_no, roll_no, first_name, last_name, gender, dob, blood_group,
            email, phone, address, class_id, admission_date, parent_name, parent_relation,
            parent_phone, parent_email, status, avatar_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, students_data)

    # 5. Attendance Records (Past 14 weekdays)
    today = datetime.now()
    dates = []
    curr = today - timedelta(days=20)
    while len(dates) < 14 and curr <= today:
        if curr.weekday() < 5:  # Monday to Friday
            dates.append(curr.strftime("%Y-%m-%d"))
        curr += timedelta(days=1)

    attendance_records = []
    for d in dates:
        for s_id in range(1, 31):
            # Class ID calculation
            c_id = ((s_id - 1) // 6) + 1
            rand_val = random.random()
            if rand_val < 0.88:
                status = 'Present'
                remarks = ''
            elif rand_val < 0.94:
                status = 'Late'
                remarks = 'Late bus arrival'
            elif rand_val < 0.98:
                status = 'Excused'
                remarks = 'Medical leave note submitted'
            else:
                status = 'Absent'
                remarks = 'Unexcused absence'
            attendance_records.append((s_id, c_id, d, status, remarks))

    cur.executemany("""
        INSERT INTO attendance (student_id, class_id, date, status, remarks)
        VALUES (?, ?, ?, ?, ?)
    """, attendance_records)

    # 6. Examinations
    exams_data = [
        ("Mid-Term Examination 2025-2026", "Semester Exam", "2025-2026", "Term 1", "2025-10-15", "2025-10-25", 1),
        ("First Terminal Assessment 2025-2026", "Assessment", "2025-2026", "Term 1", "2025-12-10", "2025-12-20", 1)
    ]
    cur.executemany("""
        INSERT INTO exams (name, exam_type, academic_year, term, start_date, end_date, is_published)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, exams_data)

    # 7. Exam Marks / Grades
    grades_records = []
    # Seed marks for Mid-Term exam (exam_id = 1) for all 30 students across 6 subjects
    for s_id in range(1, 31):
        for sub_id in range(1, 7):
            # Score between 55 and 99
            base_score = 65 + (s_id % 5) * 5 + random.randint(0, 15)
            score = min(98.5, max(52.0, base_score))
            grade_let, remark = calculate_grade(score, 100.0)
            grades_records.append((s_id, 1, sub_id, score, 100.0, grade_let, remark))

    # Also seed some for exam_id = 2
    for s_id in range(1, 15):
        for sub_id in range(1, 5):
            score = min(99.0, max(58.0, 70 + random.randint(-5, 25)))
            grade_let, remark = calculate_grade(score, 100.0)
            grades_records.append((s_id, 2, sub_id, score, 100.0, grade_let, remark))

    cur.executemany("""
        INSERT INTO grades (student_id, exam_id, subject_id, marks_obtained, max_marks, grade_letter, remarks)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, grades_records)

    # 8. Fee Types
    fee_types_data = [
        ("Tuition Fee (Quarter 1)", "Quarterly academic tuition fee covering classroom instruction & labs", 1200.00),
        ("Laboratory & Tech Fee", "Annual computer laboratory, physics/chemistry consumable charges", 350.00),
        ("Library & Digital Resources", "Library access, digital e-book licenses and research databases", 150.00),
        ("Sports & Extracurriculars", "Athletic facility maintenance, club equipment & activities", 200.00)
    ]
    cur.executemany("""
        INSERT INTO fee_types (name, description, default_amount)
        VALUES (?, ?, ?)
    """, fee_types_data)

    # 9. Invoices and Payments
    invoices_data = []
    payments_data = []
    inv_counter = 1001
    rec_counter = 5001

    for s_id in range(1, 31):
        # Invoice 1: Tuition
        inv_no = f"INV-2025-{inv_counter}"
        inv_counter += 1
        amt = 1200.00
        due_date = "2025-11-15"
        created_at = "2025-10-01"

        if s_id % 4 == 0:
            status = 'Unpaid'
            paid_amt = 0.0
        elif s_id % 4 == 1:
            status = 'Partial'
            paid_amt = 600.0
            rec_no = f"REC-2025-{rec_counter}"
            rec_counter += 1
            payments_data.append((len(invoices_data) + 1, rec_no, paid_amt, "2025-10-14", "Online", f"TXN-{random.randint(100000, 999999)}", "Installment 1 of 2"))
        else:
            status = 'Paid'
            paid_amt = 1200.0
            rec_no = f"REC-2025-{rec_counter}"
            rec_counter += 1
            payments_data.append((len(invoices_data) + 1, rec_no, paid_amt, "2025-10-10", "Card", f"POS-{random.randint(100000, 999999)}", "Full tuition payment"))

        invoices_data.append((inv_no, s_id, 1, amt, paid_amt, due_date, status, created_at))

        # Invoice 2: Lab Fee for Science students (Class 4 and 5)
        if s_id > 18:
            inv_no2 = f"INV-2025-{inv_counter}"
            inv_counter += 1
            lab_amt = 350.00
            invoices_data.append((inv_no2, s_id, 2, lab_amt, lab_amt, "2025-11-01", "Paid", "2025-09-15"))
            rec_no = f"REC-2025-{rec_counter}"
            rec_counter += 1
            payments_data.append((len(invoices_data), rec_no, lab_amt, "2025-09-28", "Online", f"TXN-{random.randint(100000, 999999)}", "Annual laboratory fee payment"))

    cur.executemany("""
        INSERT INTO fee_invoices (invoice_no, student_id, fee_type_id, amount, paid_amount, due_date, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, invoices_data)

    cur.executemany("""
        INSERT INTO fee_payments (invoice_id, receipt_no, amount_paid, payment_date, payment_method, transaction_ref, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, payments_data)

    # 10. Announcements
    announcements_data = [
        ("Mid-Term Examination Schedule Released", "The official timetable for Mid-Term Examinations (Fall Semester) is now published. All students are advised to check exam halls and seat allocations.", "All", "Urgent", "2025-10-01"),
        ("Annual Science & Robotics Exhibition 2026", "Submissions are open for student robotics and AI project exhibits. Cash prizes and scholarships will be awarded by the Apex Innovation Council.", "Students", "Normal", "2025-10-05"),
        ("Faculty Academic Review Meeting", "Mandatory quarterly review for all department heads and senior lecturers in the main conference room on Friday at 3:30 PM.", "Teachers", "Normal", "2025-10-08"),
        ("Parent-Teacher Conference (Grade 9 & 10)", "Individual academic progress reviews with parents are scheduled for next Saturday. Book your consultation slots via the portal.", "Parents", "Urgent", "2025-10-12"),
        ("Campus Sports Day & Athletic Meet", "The annual inter-house athletics competition will take place on the main sports grounds. Registrations for 100m, 400m, relay, and high jump are now open.", "All", "Low", "2025-10-14")
    ]
    cur.executemany("""
        INSERT INTO announcements (title, content, target_audience, priority, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, announcements_data)

    conn.commit()
    conn.close()
    print("Database successfully seeded with comprehensive sample data!")

if __name__ == '__main__':
    seed()
