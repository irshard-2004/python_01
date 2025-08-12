from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Paronasib@123'
app.config['MYSQL_DB'] = 'event_booking'

mysql = MySQL(app)



app.config['MAIL_SERVER'] = 'smtp.srmist.edu'  # or use 'smtp.gmail.com' if using Gmail
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'ps4017@srmist.edu'
app.config['MAIL_PASSWORD'] = 'Aalia@123'




mail = Mail(app)

@app.route('/')
def home():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM events")
    data = cur.fetchall()
    cur.close()

    events = []
    for row in data:
        events.append({
            'id': row[0],
            'title': row[1],
            'location': row[2],
            'description': row[3],  # ✅ Add this line
            'event_date': row[4],   # ✅ Use correct key name as used in template
            'event_time': row[5]    # ✅ Same here
        })

    return render_template('index.html', events=events)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
        mysql.connection.commit()
        cur.close()

        flash('Registered successfully! Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
        user = cur.fetchone()
        cur.close()

        if user:
            session['user_id'] = user[0]
            session['name'] = user[1]
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

PRICE_PER_SEAT = 100  # Change this value as needed

@app.route('/book_event/<int:event_id>', methods=['GET', 'POST'])
def book_event(event_id):
    if 'user_id' not in session:
        flash("Please log in to book an event.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        applicant_name = request.form['applicant_name']
        age = request.form['age']
        sex = request.form['sex']
        id_proof = request.form['id_proof']
        selected_seats = request.form['selected_seats']
        seats = selected_seats.split(',')
        number_of_seats = len(seats)
        amount = number_of_seats * PRICE_PER_SEAT
        ticket_number = str(random.randint(1000000, 9999999))

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO bookings (user_id, event_id, applicant_name, age, sex, id_proof, seats, seat_numbers, amount, ticket_number)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (session['user_id'], event_id, applicant_name, age, sex, id_proof, number_of_seats, selected_seats, amount, ticket_number))
        mysql.connection.commit()
        booking_id = cur.lastrowid
        cur.close()

        return redirect(url_for('booking_confirmation', booking_id=booking_id))

    return render_template('book.html', event_id=event_id)


@app.route('/confirmation/<int:booking_id>')
def booking_confirmation(booking_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT b.*, u.email 
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        WHERE b.id = %s
    """, (booking_id,))
    booking = cur.fetchone()
    cur.close()

    user_email = booking[-1]  # Last column is from users.email

    msg = Message(
        subject="🎟️ Booking Confirmation",
        sender="ps4017@srmist.edu",  # Use your real sender email
        recipients=[user_email]
    )

    msg.body = f"""
🎉 Booking Confirmed!

Name: {booking[4]}
Event ID: {booking[2]}
Number of Seats: {booking[7]}
Selected Seats: {booking[8]}
Total Amount: ₹{booking[9]}
Ticket Number: {booking[10]}

Thank you for booking with us! 😊
    """

    print("Attempting to send email...")

    try:
        mail.send(msg)
        flash("Confirmation email sent successfully! 🎉")
    except Exception as e:
        flash(f"Failed to send email: {str(e)}")

    return render_template('confirmation.html', booking=booking)



@app.route('/admin')
def admin():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT bookings.id, users.name, events.title, events.date, events.time
        FROM bookings
        JOIN users ON bookings.user_id = users.id
        JOIN events ON bookings.event_id = events.id
    """)
    data = cur.fetchall()
    cur.close()

    bookings = []
    for row in data:
        bookings.append({
            'id': row[0],
            'user': row[1],
            'event': row[2],
            'date': row[3],
            'time': row[4]
        })

    return render_template('admin.html', bookings=bookings)


@app.route('/send_test_email')
def send_test_email():
    msg = Message("Test Email", recipients=["your_email@srmist.edu"])
    msg.body = "This is a test email from the Flask application."
    
    print("Attempting to send email...")  # Debug message

    try:
        mail.send(msg)
        print("Email sent successfully!")
        return "Test email sent successfully!"
    except Exception as e:
        print(f"Failed to send email: {str(e)}")  # Print error message
        return f"Failed to send email: {str(e)}"



@app.route('/book/<int:event_id>', methods=['GET'])
def book(event_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM events WHERE id = %s", (event_id,))
    row = cur.fetchone()
    cur.close()

    if row:
        event = {
            'id': row[0],
            'title': row[1],
            'location': row[2],
            'date': row[3],
            'time': row[4]
        }
        return render_template('book.html', event=event, event_id=event_id)

    else:
        flash("Event not found.")
        return redirect(url_for('home'))


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
