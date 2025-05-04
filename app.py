from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_migrate import Migrate
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = "secret"

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'vignanhealthmateteam@gmail.com'
app.config['MAIL_PASSWORD'] = 'dikogrvbztwggjeu'
app.config['MAIL_DEFAULT_SENDER'] = 'vignanhealthmateteam@gmail.com'

mail = Mail(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)
    mobile_number = db.Column(db.String(15), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(100), nullable=True)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    roll_number = request.form["roll_number"]

    if User.query.filter_by(roll_number=roll_number).first():
        return redirect(url_for("index"))

    user = User(
        roll_number=roll_number,
        name=request.form["name"],
        age=int(request.form["age"]),
        weight=float(request.form["weight"]),
        height=float(request.form["height"]),
        mobile_number=request.form["mobile"],
        gender=request.form["gender"],
        email=request.form["email"]
    )
    db.session.add(user)
    db.session.commit()

    return redirect(url_for("index"))

@app.route("/login", methods=["POST"])
def login():
    roll_number = request.form["roll_number"]
    user = User.query.filter_by(roll_number=roll_number).first()
    if user:
        session["roll_number"] = roll_number
        return redirect(url_for("dashboard"))
    return redirect(url_for("index"))

@app.route("/dashboard")
def dashboard():
    if "roll_number" not in session:
        return redirect(url_for("index"))

    roll_number = session["roll_number"]
    user_data = User.query.filter_by(roll_number=roll_number).first()

    if not user_data:
        return redirect(url_for("index"))

    weight = float(user_data.weight)
    height = float(user_data.height) / 100
    bmi = round(weight / (height ** 2), 2)

    if bmi < 18.5:
        status = "Underweight"
        precautions = [
            "Increase calorie intake with healthy foods",
            "Eat more protein-rich foods",
            "Include nuts and dairy in your diet",
            "Do strength training exercises",
            "Consult a dietitian for a personalized plan"
        ]
    elif bmi > 25:
        status = "Overweight"
        precautions = [
            "Reduce processed and high-fat foods",
            "Increase daily physical activity",
            "Drink plenty of water",
            "Monitor portion sizes",
            "Seek medical advice if needed"
        ]
    else:
        status = "Normal weight"
        precautions = [
            "Maintain a balanced diet",
            "Stay physically active",
            "Drink enough water",
            "Avoid excessive sugar and salt",
            "Have regular health check-ups"
        ]

    age = int(user_data.age)
    haemoglobin = 13.5 if age >= 18 else 12.0

    return render_template("dashboard.html", user=user_data, bmi=bmi, status=status, haemoglobin=haemoglobin, precautions=precautions)

@app.route("/upload_csv", methods=["POST"])
def upload_csv():
    if "csv_file" not in request.files:
        flash("No file part", "danger")
        return redirect(request.url)
    file = request.files["csv_file"]
    if file.filename == "":
        flash("No selected file", "danger")
        return redirect(request.url)

    if file:
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        try:
            file.save(file_path)
            df = pd.read_csv(file_path)

            required_columns = ["roll_number", "name", "age", "weight", "height", "mobile_number", "gender", "email"]
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                flash(f"Missing columns in CSV: {', '.join(missing_columns)}", "danger")
                os.remove(file_path)  # Clean up the uploaded file
                return redirect(url_for("index"))

            db.session.query(User).delete()
            db.session.commit()

            for _, row in df.iterrows():
                if not User.query.filter_by(roll_number=row["roll_number"]).first():
                    new_user = User(
                        roll_number=row["roll_number"],
                        name=row["name"],
                        age=int(row["age"]),
                        weight=float(row["weight"]),
                        height=float(row["height"]),
                        mobile_number=row["mobile_number"],
                        gender=row["gender"],
                        email=row.get("email", None)  # Handle potential missing email
                    )
                    db.session.add(new_user)

            db.session.commit()
            os.remove(file_path)  # Clean up after successful upload
            flash("CSV uploaded successfully!", "success")
            return redirect(url_for("index"))

        except Exception as e:
            flash(f"Error processing CSV: {e}", "danger")
            if os.path.exists(file_path):
                os.remove(file_path)
            return redirect(url_for("index"))

    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.pop("roll_number", None)
    return redirect(url_for("index"))

@app.route("/bmi_data")
def get_bmi_data():
    users = User.query.all()
    bmi_categories = {"Underweight": 0, "Normal": 0, "Overweight": 0}

    for user in users:
        weight = float(user.weight)
        height = float(user.height) / 100
        bmi = round(weight / (height ** 2), 2)

        if bmi < 18.5:
            bmi_categories["Underweight"] += 1
        elif bmi > 25:
            bmi_categories["Overweight"] += 1
        else:
            bmi_categories["Normal"] += 1

    return jsonify(bmi_categories)

@app.route("/student_weight_data")
def get_student_weight_data():
    if "roll_number" not in session:
        return jsonify({"error": "Not logged in"}), 403

    roll_number = session["roll_number"]
    user_data = User.query.filter_by(roll_number=roll_number).first()

    if not user_data:
        return jsonify({"error": "User not found"}), 404

    height_m = float(user_data.height) / 100
    ideal_weight = round(22 * (height_m ** 2), 2)

    return jsonify({
        "Actual Weight": user_data.weight,
        "Ideal Weight": ideal_weight
    })

@app.route("/users")
def get_users():
    users = User.query.all()
    user_data = {"Overweight": [], "Underweight": [], "Normal": []}

    for user in users:
        weight = float(user.weight)
        height = float(user.height) / 100
        bmi = round(weight / (height ** 2), 2)

        if bmi < 18.5:
            user_data["Underweight"].append(user.name)
        elif bmi > 25:
            user_data["Overweight"].append(user.name)
        else:
            user_data["Normal"].append(user.name)

    return jsonify(user_data)

@app.route("/view_all_users")
def view_all_users():
    users = User.query.all()
    return render_template("users_table.html", users=users)

@app.route("/filter_users", methods=["GET"])
def filter_users():
    gender = request.args.get("gender")
    bmi_category = request.args.get("bmi")
    min_age = request.args.get("min_age", type=int)
    max_age = request.args.get("max_age", type=int)

    query = User.query
    if gender:
        query = query.filter_by(gender=gender)
    if min_age is not None:
        query = query.filter(User.age >= min_age)
    if max_age is not None:
        query = query.filter(User.age <= max_age)

    filtered_users = []
    for user in query.all():
        height_m = float(user.height) / 100
        bmi = round(float(user.weight) / (height_m ** 2), 2)

        if bmi_category == "Underweight" and bmi < 18.5:
            filtered_users.append(user)
        elif bmi_category == "Normal" and 18.5 <= bmi <= 25:
            filtered_users.append(user)
        elif bmi_category == "Overweight" and bmi > 25:
            filtered_users.append(user)
        elif not bmi_category:
            filtered_users.append(user)

    return render_template("users_table.html", users=filtered_users)

@app.route("/send_email", methods=["POST"])
def send_email():
    if "roll_number" not in session:
        return redirect(url_for("index"))

    user = User.query.filter_by(roll_number=session["roll_number"]).first()

    if not user or not user.email:
        return redirect(url_for("dashboard"))

    height_m = float(user.height) / 100
    bmi = round(user.weight / (height_m ** 2), 2)
    haemoglobin = 13.5 if user.age >= 18 else 12.0

    if bmi < 18.5:
        status = "Underweight"
        precautions = [
            "Eat more frequent meals and snacks",
            "Add calorie-dense foods like nuts, cheese, and dairy",
            "Incorporate strength training exercises",
            "Increase protein intake (e.g., eggs, chicken, legumes)",
            "Drink smoothies and shakes"
        ]
        doctor = "Nutritionist or General Physician"
    elif bmi > 25:
        status = "Overweight"
        precautions = [
            "Avoid sugary drinks and junk food",
            "Exercise for at least 30 minutes daily",
            "Follow a calorie-controlled diet plan",
            "Eat more fruits and vegetables",
            "Track your weight and food intake regularly"
        ]
        doctor = "Dietitian or Endocrinologist"
    else:
        status = "Normal"
        precautions = [
            "Maintain a balanced diet",
            "Engage in regular moderate exercise",
            "Stay hydrated with at least 2L water/day",
            "Avoid stress eating or skipping meals",
            "Visit doctor for yearly check-ups"
        ]
        doctor = "General Physician"

    message_body = f"""
Hello {user.name},

Here is your Health Mate Dashboard Summary:

- Age: {user.age}
- Height: {user.height} cm
- Weight: {user.weight} kg
- BMI: {bmi} ({status})
- Required Hemoglobin Level: {haemoglobin} g/dL

Precautionary Steps:
{chr(10).join(f"- {step}" for step in precautions)}

Recommended Specialist: {doctor}

Regards,
Health Mate Team
    """

    msg = Message("Your Health Mate Report", recipients=[user.email], body=message_body)
    mail.send(msg)

    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)


