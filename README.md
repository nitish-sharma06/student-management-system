# Apex Student Management System (SMS)

A complete, production-grade educational administration and Student Information System (SIS) built with **Python (Flask)**, **SQLite**, and **ReportLab**.

---

## 🌟 Key Features

1. **Institutional Dashboard & Analytics**:
   - Executive KPIs: Total Students, Total Faculty, Overall Attendance Rate, Total Fees Collected vs. Pending.
   - Dynamic interactive charts (Chart.js): Academic Grade Distribution, Attendance Ratios, and Enrollment trends.
   - Management Action Hub with quick shortcuts.

2. **Student Lifecycle Management**:
   - Comprehensive student registry with instant search, filtering by grade/section/status.
   - Detailed Student Profile (360° view): Personal bio, Emergency contact, Academic standing, Attendance log, Fee ledger.
   - Full student registration/admission wizard.
   - **Student ID Card Badge generator** (Printable layout with photo, barcode, and principal signature).
   - CSV Directory Export.

3. **Classes & Curriculum Management**:
   - Classrooms & Sections management with room numbers and assigned class tutors.
   - Course curriculum and subjects directory with credit hours and assigned faculty.

4. **Batch Attendance Tracking**:
   - Fast batch attendance marker for entire classrooms with "Mark All Present" shortcut.
   - Attendance percentages automatically computed per student and per class.
   - Class attendance register report with low attendance (<75%) warning highlights.

5. **Examinations, Grading & Report Cards**:
   - Schedule exam terms (Mid-Term, Semester Finals, Assessments).
   - Batch marks entry sheet with instant max-mark validation and automatic letter grade calculation (A+, A, B, C, D, F).
   - **Official Academic Report Card / Transcript**:
     - Beautiful printable format (Ctrl+P).
     - One-click downloadable vector PDF generated via ReportLab.

6. **Fee Management & Invoicing**:
   - Invoice generation per student with fee types (Tuition, Laboratory, Library, Sports).
   - Payment collection and recording (Cash, Online, Card, Cheque) with transaction references.
   - Automatic invoice status transition (Paid, Partial, Unpaid).
   - **Official Fee Payment Receipt**:
     - Printable layout with school authorization seal.
     - One-click downloadable vector PDF.

7. **Faculty & Staff Directory**:
   - Teacher profiles with designations, departments, employee IDs, qualifications, and subject assignments.

8. **Noticeboard & Communication**:
   - Broadcast notices targeted to All, Students, Teachers, or Parents.
   - Urgency indicators (Urgent, Normal, Low).

---

## 🚀 Quick Start Guide

### Option 1: Double-Click Launcher (Windows)
Double-click `run.bat` in this folder.

### Option 2: PowerShell
```powershell
.\run.ps1
```

### Option 3: Manual Command
```powershell
& "C:\Users\ayush\AppData\Local\Programs\Python\Python311\python.exe" app.py
```

Open your browser and visit:
👉 **http://127.0.0.1:5000**

---

## 🗄️ Database & Pre-Seeded Sample Data

The project is pre-seeded with realistic data inside `sms.db`:
- **30 Enrolled Students** across 5 grade levels with realistic contacts and parent info.
- **8 Teaching Faculty Members** across departments.
- **5 Classes & 8 Subjects** mapped with credits.
- **14 Days of Attendance Records** logged for every student.
- **2 Examination Schedules** with complete grades entered.
- **Invoices & Payment Records** with real transactions.
- **Active Noticeboard Announcements**.

To re-seed fresh demo data at any time:
```powershell
& "C:\Users\ayush\AppData\Local\Programs\Python\Python311\python.exe" seed_data.py
```
