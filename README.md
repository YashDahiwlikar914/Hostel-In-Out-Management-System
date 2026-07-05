# Hostel In-Out Management System

This is a system that tracks hostel entry and exit using QR codes. Students get a code tied to their roll number. The gate scans it, and the system logs who is inside and who is out, from which gate, and exactly when they moved. 

## What It Does

An admin registers students and generates a QR code for each one. Gate operators then scan that code using a webcam. The system reads it, flips the student's status from inside to outside or vice versa, and logs the event. 

It handles cross-gate exits correctly. If a student enters at Gate A and leaves from Gate B, the system logs that cleanly. You can pull reports to view, filter, and export the full log as a CSV.

The app uses Streamlit for the interface and SQLite for the local database. It uses `pyzbar` and `Pillow` to decode QR codes and `qrcode` to generate them.

## Setup

If you are on Linux, install the system dependency first.

```bash
sudo apt install libzbar0
```

Install the Python packages.

```bash
pip install -r requirements.txt
```

Start the app.

```bash
streamlit run App.py
```

The app creates the database file automatically on its first run.

## Usage

You can select three modes from the sidebar.

| Mode | What It Does |
|---|---|
| Admin | Register a student by name and roll number. Select them from the dropdown to download their QR code to put on their ID card. |
| Gate | Pick the gate and scan the student's QR code with the camera. The system reads the roll number and updates their status. You can also type the roll number manually if scanning fails. |
| Reports | View the last 1000 log entries, filter them by roll number or date range, and export them to a CSV. |

## Notes
Claude helped build the Streamlit interface and some of the core Python code. I designed and verified the QR tracking logic and cross-gate handling manually.

Roll numbers have to be unique. The system rejects duplicate entries, and students cannot register themselves. The admin has to set them up. 
If you need to wipe the data, admins can reset all logs from the Admin panel. It asks for confirmation first, so you do not do it by accident.
