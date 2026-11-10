from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from db import get_db_connection
from receipt import generate_appointment_pdf

app = Flask(__name__)
app.secret_key = "medislot_secure_secret_key"

ALL_SLOTS = [
    "09:00 AM", "09:30 AM", "10:00 AM", "10:30 AM",
    "11:00 AM", "11:30 AM", "02:00 PM", "02:30 PM",
    "03:00 PM", "03:30 PM", "04:00 PM", "04:30 PM"
]

# Home & Doctor List
@app.route("/")
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT d.id AS doctor_id, u.name, d.specialty, d.room_no, d.fee 
        FROM doctors d
        JOIN users u ON d.user_id = u.id
    """)
    doctors = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("index.html", doctors=doctors, slots=ALL_SLOTS)

# API to fetch already-booked slots for a chosen date
@app.route("/api/get-booked-slots")
def get_booked_slots():
    doctor_id = request.args.get("doctor_id")
    date = request.args.get("date")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT time_slot FROM appointments 
        WHERE doctor_id = %s AND appointment_date = %s AND status = 'Confirmed'
    """, (doctor_id, date))
    booked = [row['time_slot'] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return jsonify({"booked_slots": booked})

# Book Appointment Handler
@app.route("/book", methods=["POST"])
def book():
    if "user_id" not in session:
        flash("Please log in first to book an appointment.", "warning")
        return redirect(url_for("login"))

    doctor_id = request.form["doctor_id"]
    date = request.form["appointment_date"]
    slot = request.form["time_slot"]
    reason = request.form.get("reason", "Regular Checkup")
    patient_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Double-check availability before booking
    cursor.execute("""
        SELECT id FROM appointments 
        WHERE doctor_id = %s AND appointment_date = %s AND time_slot = %s AND status = 'Confirmed'
    """, (doctor_id, date, slot))
    
    if cursor.fetchone():
        flash("Sorry! That slot was just taken. Please choose another time.", "danger")
        cursor.close()
        conn.close()
        return redirect(url_for("index"))

    cursor.execute("""
        INSERT INTO appointments (patient_id, doctor_id, appointment_date, time_slot, reason)
        VALUES (%s, %s, %s, %s, %s)
    """, (patient_id, doctor_id, date, slot, reason))
    conn.commit()
    cursor.close()
    conn.close()

    flash("Appointment booked successfully!", "success")
    return redirect(url_for("my_bookings"))

# Patient Dashboard
@app.route("/my-bookings")
def my_bookings():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.id, u.name AS doctor_name, d.specialty, d.room_no, 
               a.appointment_date, a.time_slot, a.status, a.reason
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users u ON d.user_id = u.id
        WHERE a.patient_id = %s
        ORDER BY a.appointment_date DESC, a.time_slot ASC
    """, (session["user_id"],))
    bookings = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("my_bookings.html", bookings=bookings)

# Cancel Appointment
@app.route("/cancel/<int:appointment_id>", methods=["POST"])
def cancel_appointment(appointment_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE appointments SET status = 'Cancelled' 
        WHERE id = %s AND patient_id = %s
    """, (appointment_id, session["user_id"]))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Appointment cancelled.", "info")
    return redirect(url_for("my_bookings"))

# PDF Receipt Download Route
@app.route("/download-receipt/<int:appointment_id>")
def download_receipt(appointment_id):
    if "user_id" not in session:
        flash("Please log in to download your receipt.", "warning")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.id, a.appointment_date, a.time_slot, a.status, a.reason,
               u_pat.name AS patient_name,
               u_doc.name AS doctor_name,
               d.specialty, d.room_no, d.fee
        FROM appointments a
        JOIN users u_pat ON a.patient_id = u_pat.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users u_doc ON d.user_id = u_doc.id
        WHERE a.id = %s AND (a.patient_id = %s OR %s = 'doctor')
    """, (appointment_id, session["user_id"], session.get("role")))
    
    appointment = cursor.fetchone()
    cursor.close()
    conn.close()

    if not appointment:
        flash("Appointment receipt not found or access denied.", "danger")
        return redirect(url_for("my_bookings"))

    # Create formatted token ID: MS-0001
    token_number = f"MS-{appointment['id']:04d}"

    pdf_data = {
        "token": token_number,
        "patient_name": appointment["patient_name"],
        "doctor_name": appointment["doctor_name"],
        "specialty": appointment["specialty"],
        "room_no": appointment["room_no"],
        "date": appointment["appointment_date"],
        "time_slot": appointment["time_slot"],
        "fee": float(appointment["fee"]),
        "status": appointment["status"]
    }

    pdf_buffer = generate_appointment_pdf(pdf_data)

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"MediSlot_Receipt_{token_number}.pdf",
        mimetype="application/pdf"
    )

# Doctor Admin View
@app.route("/doctor-dashboard")
def doctor_dashboard():
    if session.get("role") != "doctor":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("index"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.id, u.name AS patient_name, u.phone, a.appointment_date, 
               a.time_slot, a.reason, a.status
        FROM appointments a
        JOIN users u ON a.patient_id = u.id
        JOIN doctors d ON a.doctor_id = d.id
        WHERE d.user_id = %s
        ORDER BY a.appointment_date ASC, a.time_slot ASC
    """, (session["user_id"],))
    appointments = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("doctor_admin.html", appointments=appointments)

# Authentication Routes
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        phone = request.form["phone"]

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (name, email, password, phone, role) VALUES (%s, %s, %s, %s, 'patient')",
                (name, email, password, phone)
            )
            conn.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
        except Exception:
            flash("Email already registered.", "danger")
        finally:
            cursor.close()
            conn.close()
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["role"] = user["role"]
            flash(f"Welcome back, {user['name']}!", "success")
            if user["role"] == "doctor":
                return redirect(url_for("doctor_dashboard"))
            return redirect(url_for("index"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, port=5000)