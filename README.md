# 🩺 MediSlot — Smart Clinic & Appointment Booking System

MediSlot is a full-stack clinical scheduling and consultation reservation platform designed to streamline outpatient visits, eliminate double-booking conflicts, and generate instant verified digital consultation slips.

---

## 🚀 Key Features

- **Dynamic Conflict-Free Slot Picker:** Real-time availability verification preventing overlapping patient reservations.
- **Role-Based Access Control:** Dual dashboards for Patients (book, track, cancel) and Doctors (schedule oversight, patient queues).
- **Automated Digital Token & Receipt Engine:** Generates downloadable, tamper-verifiable PDF consultation passes complete with unique token IDs (`#MS-XXXX`) and embedded QR codes.
- **Relational Integrity:** Backed by MySQL relational tables with foreign keys and unique multi-column constraints.

---

## 🛠️ Tech Stack

- **Backend:** Python (Flask), MySQL Connector
- **Database:** MySQL
- **Frontend:** HTML5, CSS3, Vanilla JavaScript (Fetch API)
- **PDF & QR Generation:** ReportLab, QRCode, Pillow

---

## 👤 Test Credentials

| Role | Email | Password |
| :--- | :--- | :--- |
| **Doctor** | `priya@medislot.com` | `doctor123` |
| **Doctor** | `rajesh@medislot.com` | `doctor123` |
| **Patient** | Register a new account via the `/register` portal |
