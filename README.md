🎓 Apex Student Management System (SMS)
![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)
![GitHub license](https://img.shields.io/github/license/nitish-sharma06/student-management-system)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)
![Streamlit Cloud](https://img.shields.io/badge/Streamlit-Cloud%20Deployable-FF4B4B?logo=streamlit&logoColor=white)
A complete, production-grade educational administration and Student Information System (SIS) built with Python, Streamlit Cloud, Flask, SQLite, and ReportLab.
---

---
🌟 Key Management Modules
Executive Dashboard & Analytics:
High-level KPIs: Enrolled Students, Teaching Faculty, Campus Attendance %, Fees Collected vs. Pending.
Interactive analytics charts: Grade performance distribution and daily attendance ratios.
Live activity streams for newly registered students and campus notices.
Student 360° Directory & Dossiers:
Instant search-as-you-type and multi-filter registry (by class, section, status).
Comprehensive student profile tabs: Bio, emergency contacts, exam transcripts, attendance logs, and fee history.
Student ID Card Badge generator (standard ID-1 PVC badge layout with barcode and signatures).
One-click CSV Roster Export.
Admissions & Registration:
Streamlined admission portal generating admission numbers and student avatars with input validation.
Batch Attendance Tracking:
Rapid daily roll call marker with a "Mark All Present" shortcut.
Class attendance register calculating overall attendance rates and flagging defaulters below 75%.
Examinations & Gradebook:
Exam scheduler (Mid-Term, Semester Finals, Assessments).
Gradebook marks entry sheet with automatic letter grade calculation (A+, A, B, C, D, F).
Official Academic Report Card / Transcript (Printable HTML view & downloadable vector PDF).
Fee Management & Invoicing:
Invoicing per student across fee categories (Tuition, Laboratory, Library, Sports).
Payment collection and recording (Cash, Card, Online, Cheque) with transaction references.
Official Fee Payment Receipt (Printable view & downloadable vector PDF).
Faculty Directory:
Instructor profiles, departments, designations, qualifications, and taught courses.
Campus Noticeboard:
Broadcast advisories with audience targeting (Students, Faculty, Parents) and urgency badges.
---
💻 Running Locally
Streamlit Mode:
```bash
streamlit run streamlit_app.py
```
Access at: `http://localhost:8501`
Flask Mode:
```bash
python app.py
```
Access at: `http://127.0.0.1:5000`
Windows Launchers:
Double-click `run.bat` or run `./run.ps1`
