import sqlite3
import os
from config import DATABASE_PATH

def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def query_db(query, args=(), one=False):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(query, args)
        rv = cur.fetchall()
        return (rv[0] if rv else None) if one else rv
    finally:
        conn.close()

def execute_db(query, args=()):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(query, args)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

def execute_many_db(query, args_list):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.executemany(query, args_list)
        conn.commit()
    finally:
        conn.close()

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.executescript("""
    -- Teachers / Staff
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        department TEXT NOT NULL,
        designation TEXT NOT NULL,
        qualification TEXT,
        join_date TEXT NOT NULL,
        status TEXT DEFAULT 'Active'
    );

    -- Classes
    CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        grade_level TEXT NOT NULL,
        section TEXT NOT NULL,
        room_number TEXT,
        class_teacher_id INTEGER,
        FOREIGN KEY (class_teacher_id) REFERENCES teachers(id) ON DELETE SET NULL,
        UNIQUE(grade_level, section)
    );

    -- Subjects
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        credits INTEGER DEFAULT 3,
        teacher_id INTEGER,
        FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL
    );

    -- Class Subject mapping
    CREATE TABLE IF NOT EXISTS class_subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_id INTEGER NOT NULL,
        subject_id INTEGER NOT NULL,
        FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
        UNIQUE(class_id, subject_id)
    );

    -- Students
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admission_no TEXT UNIQUE NOT NULL,
        roll_no TEXT NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        gender TEXT NOT NULL,
        dob TEXT NOT NULL,
        blood_group TEXT,
        email TEXT,
        phone TEXT,
        address TEXT,
        class_id INTEGER NOT NULL,
        admission_date TEXT NOT NULL,
        parent_name TEXT NOT NULL,
        parent_relation TEXT DEFAULT 'Parent',
        parent_phone TEXT NOT NULL,
        parent_email TEXT,
        status TEXT DEFAULT 'Active',
        avatar_url TEXT,
        FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE RESTRICT
    );

    -- Attendance
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        class_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('Present', 'Absent', 'Late', 'Excused')),
        remarks TEXT,
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
        UNIQUE(student_id, date)
    );

    -- Examinations
    CREATE TABLE IF NOT EXISTS exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        exam_type TEXT NOT NULL,
        academic_year TEXT NOT NULL,
        term TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        is_published INTEGER DEFAULT 1
    );

    -- Grades / Marks
    CREATE TABLE IF NOT EXISTS grades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        exam_id INTEGER NOT NULL,
        subject_id INTEGER NOT NULL,
        marks_obtained REAL NOT NULL,
        max_marks REAL NOT NULL DEFAULT 100.0,
        grade_letter TEXT,
        remarks TEXT,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
        UNIQUE(student_id, exam_id, subject_id)
    );

    -- Fee Types
    CREATE TABLE IF NOT EXISTS fee_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        default_amount REAL NOT NULL
    );

    -- Fee Invoices
    CREATE TABLE IF NOT EXISTS fee_invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_no TEXT UNIQUE NOT NULL,
        student_id INTEGER NOT NULL,
        fee_type_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        paid_amount REAL DEFAULT 0.0,
        due_date TEXT NOT NULL,
        status TEXT DEFAULT 'Unpaid' CHECK(status IN ('Paid', 'Partial', 'Unpaid')),
        created_at TEXT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (fee_type_id) REFERENCES fee_types(id) ON DELETE RESTRICT
    );

    -- Fee Payments
    CREATE TABLE IF NOT EXISTS fee_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        receipt_no TEXT UNIQUE NOT NULL,
        amount_paid REAL NOT NULL,
        payment_date TEXT NOT NULL,
        payment_method TEXT NOT NULL CHECK(payment_method IN ('Cash', 'Online', 'Card', 'Cheque', 'Bank Transfer')),
        transaction_ref TEXT,
        notes TEXT,
        FOREIGN KEY (invoice_id) REFERENCES fee_invoices(id) ON DELETE CASCADE
    );

    -- Announcements
    CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        target_audience TEXT DEFAULT 'All' CHECK(target_audience IN ('All', 'Students', 'Teachers', 'Parents')),
        priority TEXT DEFAULT 'Normal' CHECK(priority IN ('Low', 'Normal', 'Urgent')),
        created_at TEXT NOT NULL
    );
    """)

    conn.commit()
    conn.close()
    print("Database tables initialized successfully.")

if __name__ == '__main__':
    init_db()
