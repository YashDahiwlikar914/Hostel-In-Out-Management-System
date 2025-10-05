# app.py
import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
import qrcode
from io import BytesIO
from PIL import Image
from pyzbar.pyzbar import decode


@st.cache_resource
def init_db():
    conn = sqlite3.connect("hostel.db", check_same_thread=False)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS students (
               id INTEGER PRIMARY KEY,
               name TEXT,
               roll TEXT UNIQUE,
               current_status TEXT DEFAULT 'Outside',
               last_gate TEXT
           )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS logs (
               id INTEGER PRIMARY KEY,
               roll TEXT,
               name TEXT,
               timestamp TEXT,
               gate TEXT,
               status TEXT
           )"""
    )
    conn.commit()
    return conn


conn = init_db()
c = conn.cursor()


def add_student(name: str, roll: str):
    try:
        c.execute("INSERT INTO students (name, roll) VALUES (?, ?)", (name.strip(), roll.strip()))
        conn.commit()
        return True, "Student added."
    except Exception as e:
        return False, str(e)


def get_students_df():
    return pd.read_sql_query("SELECT id, name, roll, current_status, last_gate FROM students ORDER BY roll", conn)


def get_logs_df(limit=None):
    q = "SELECT id, roll, name, timestamp, gate, status FROM logs ORDER BY id DESC"
    if limit:
        q += f" LIMIT {limit}"
    return pd.read_sql_query(q, conn)


def generate_qr_image(data: str):
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img


def process_scan(roll: str, gate: str):
    roll = roll.strip()
    c.execute("SELECT name, current_status, last_gate FROM students WHERE roll = ?", (roll,))
    row = c.fetchone()
    now = datetime.now().isoformat(sep=" ", timespec="seconds")
    if not row:
        st.error(f"Roll '{roll}' not found in database. Admin must add student first.")
        return

    name, current_status, last_gate = row
    if current_status == "Outside":
        new_status = "Inside"
        new_last_gate = gate
        note = f"Entry recorded at Gate {gate}."
    else:
        new_status = "Outside"
        new_last_gate = None
        if last_gate and last_gate != gate:
            note = f"Exit at Gate {gate} (entered earlier at Gate {last_gate})."
        elif last_gate == gate:
            note = f"Exit at same Gate {gate} (no cross-gate)."
        else:
            note = f"Exit at Gate {gate}."

    c.execute(
        "INSERT INTO logs (roll, name, timestamp, gate, status) VALUES (?, ?, ?, ?, ?)",
        (roll, name, now, gate, new_status),
    )
    c.execute(
        "UPDATE students SET current_status = ?, last_gate = ? WHERE roll = ?", (new_status, new_last_gate, roll)
    )
    conn.commit()
    st.success(f"{name} ({roll}) → {new_status} — {note} — {now}")



st.set_page_config(page_title="Hostel In-Out System", layout="wide")
st.title("Hostel In-Out Management System")

mode = st.sidebar.selectbox("Mode", ["Gate (Scan)", "Admin", "Reports"])

if mode == "Admin":
    st.header("Register Student & Generate QR Code")
    with st.form("add_student", clear_on_submit=True):
        name = st.text_input("Student Name")
        roll = st.text_input("Roll Number (All Caps)")
        submitted = st.form_submit_button("Add Student")
        if submitted:
            if not name or not roll:
                st.error("Both Name And roll Are Required.")
            else:
                ok, msg = add_student(name, roll)
                if ok:
                    st.success("Added: " + roll)
                else:
                    st.error(msg)

    st.markdown("---")
    st.subheader("Download QR")
    st.info("QR Encodes The Student's Roll Number. Use This Image For The Student's ID Card.")
    students_df = get_students_df()
    if students_df.empty:
        st.write("No Students Yet.")
    else:
        selected = st.selectbox("Pick Student", students_df["roll"].tolist())
        if selected:
            student_row = students_df[students_df["roll"] == selected].iloc[0]
            img = generate_qr_image(selected)
            buf = BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            st.image(Image.open(buf), caption=f"QR for {student_row['name']} — {selected}", width=220)
            st.download_button(
                "Download QR (PNG)",
                buf,
                file_name=f"{selected}.png",
                mime="image/png",
            )

    st.markdown("---")
    st.subheader("Student List")
    st.dataframe(students_df, use_container_width=True)
    st.markdown("---")
    st.subheader("Admin Tools")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Export Students Csv"):
            csv = students_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download Students.csv", csv, file_name="students.csv", mime="text/csv")
    with col2:
        confirm = st.checkbox("Confirm Delete All Logs")
        if st.button("Reset All Logs?!"):
            if confirm:
                c.execute("DELETE FROM logs")
                conn.commit()
                st.success("All Logs Deleted.")
            else:
                st.error("Please Check The Confirm Box To Delete Logs.")

elif mode == "Gate (Scan)":
    st.header("Gate — Scan QR")
    gate = st.selectbox("Select Gate", ["A", "B"])
    st.write("Use camera to capture student's QR code. Camera auto-stops after capture.")
    img_file = st.camera_input("Capture QR here")
    if img_file is not None:
        img = Image.open(img_file)
        decoded = decode(img)
        if not decoded:
            st.error("No QR detected in the captured image. Try again and make sure the QR is fully inside the frame.")
        else:
            qrdata = decoded[0].data.decode("utf-8")
            st.write("Scanned:", qrdata)
            process_scan(qrdata, gate)

    st.markdown("---")
    st.subheader("Quick lookup")
    lookup_roll = st.text_input("Lookup roll (type and press Enter)")
    if lookup_roll:
        c.execute("SELECT name, current_status, last_gate FROM students WHERE roll = ?", (lookup_roll.strip(),))
        r = c.fetchone()
        if r:
            st.write(f"Name: {r[0]}  |  Status: {r[1]}  |  Last gate: {r[2]}")
        else:
            st.write("Not found.")

elif mode == "Reports":
    st.header("Reports & Logs")
    logs_df = get_logs_df(limit=1000)
    if logs_df.empty:
        st.write("No logs yet.")
    else:
        st.dataframe(logs_df, use_container_width=True)
        csv = logs_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download logs.csv", csv, file_name="logs.csv", mime="text/csv")

    st.markdown("---")
    st.subheader("Filter logs")
    r_roll = st.text_input("Filter by roll (leave blank for all)")
    r_from = st.date_input("From", value=None)
    r_to = st.date_input("To", value=None)
    if st.button("Apply filter"):
        q = "SELECT id, roll, name, timestamp, gate, status FROM logs WHERE 1=1"
        params = []
        if r_roll:
            q += " AND roll = ?"
            params.append(r_roll.strip())
        if r_from:
            q += " AND date(timestamp) >= date(?)"
            params.append(r_from.isoformat())
        if r_to:
            q += " AND date(timestamp) <= date(?)"
            params.append(r_to.isoformat())
        q += " ORDER BY id DESC"
        filtered = pd.read_sql_query(q, conn, params=params)
        st.dataframe(filtered, use_container_width=True)
        st.download_button("Download filtered CSV", filtered.to_csv(index=False).encode("utf-8"), file_name="filtered_logs.csv")
