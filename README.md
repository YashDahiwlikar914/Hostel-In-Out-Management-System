# Hostel In-Out Management System

A QR-based entry/exit tracking system for hostels. Students get a QR code tied to their roll number. Gates scan it. The system logs who went in or out, from which gate, and when.

That's it.

---

## What It Does

- **Admin** registers students and generates a QR code for each one.
- **Gate operators** scan the QR using a webcam. The system flips the student's status (Inside → Outside, Outside → Inside) and logs the event.
- **Reports** let you view and filter the full log, and export it as CSV.

It also handles cross-gate exits — if a student entered at Gate A and exits at Gate B, that gets noted.

---

## Stack

- [Streamlit](https://streamlit.io/) — UI
- SQLite — local database (`hostel.db`)
- `pyzbar` + `Pillow` — QR decoding
- `qrcode` — QR generation

---

## Setup

**1. Install system dependency (Linux only)**
```bash
sudo apt install libzbar0
```

**2. Install Python packages**
```bash
pip install -r requirements.txt
```

**3. Run**
```bash
streamlit run App.py
```

The database file (`hostel.db`) gets created automatically on first run.

---

## Usage

Three modes, selectable from the sidebar:

**Admin**
Register a student by name and roll number. Once added, select them from the dropdown to view and download their QR code. This QR goes on their ID card.

**Gate (Scan)**
Pick the gate (A or B), then use the camera to scan the student's QR. The system reads the roll number, looks it up, and updates their status. You can also do a manual roll number lookup without scanning.

**Reports**
View the last 1000 log entries. Filter by roll number or date range. Export to CSV.

---

## Notes

- Roll numbers are unique. Duplicate entries get rejected.
- Admins can reset all logs from the Admin panel (there's a confirm checkbox, don't worry).
- Students can't self-register. Admin always goes first.
