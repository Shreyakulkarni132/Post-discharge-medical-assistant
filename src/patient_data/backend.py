from flask import Flask, render_template_string, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "supersecretkey" 

DB_PATH = os.path.join(os.path.dirname(__file__), "hospital_discharge.db")

FORM_HTML = """
<!doctype html>
<html>
<head>
    <title>Patient Data Entry</title>
    <style>
        body { font-family: Arial; margin: 0px; }
        form { max-width: 500px; margin: auto; }
        label { display: block; margin-top: 0px; }
        input, textarea { width: 100%; padding: 8px; margin-top: 4px; }
        button { margin-top: 15px; padding: 10px 20px; }
        .flash { color: green; }
    </style>
</head>
<body>
    <div style="background-color: orange; width: 100%; margin: 0; padding: 30px 15px; text-align: center; color: white; font-size: 28px; font-weight: bold;">
        After Doctor - Your Post Discharge Assistant
    </div>
    <h2 style="text-align: center; margin-top: 20px; margin-left: 10px; margin-right: 10px; padding-left: 15px; padding-right: 15px;">Enter Patient Details:</h2>
    {% with messages = get_flashed_messages() %}
    {% if messages %}
        <div style="display: flex; justify-content: center; margin-top: 15px; margin-bottom:15px">
        {% for message in messages %}
            <div style="background-color: #28a745; color: white; padding: 10px 20px; border-radius: 5px;">
            {{ message }}
            </div>
        {% endfor %}
        </div>
    {% endif %}
    {% endwith %}
    <form method="POST">
        <label>Patient Name:</label>
        <input type="text" name="patient_name" required>
        
        <label>Discharge Date (YYYY-MM-DD):</label>
        <input type="text" name="discharge_date" required>
        
        <label>Primary Diagnosis:</label>
        <input type="text" name="primary_diagnosis" required>
        
        <label>Medications (comma-separated):</label>
        <input type="text" name="medications">
        
        <label>Dietary Restrictions:</label>
        <input type="text" name="dietary_restrictions">
        
        <label>Follow-up Instructions:</label>
        <textarea name="follow_up"></textarea>
        
        <label>Warning Signs:</label>
        <textarea name="warning_signs"></textarea>
        
        <label>Discharge Instructions:</label>
        <textarea name="discharge_instructions"></textarea>
        
        <button type="submit">Submit</button>
    </form>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def add_patient():
    if request.method == "POST":
        try:
            data = (
                request.form["patient_name"],
                request.form["discharge_date"],
                request.form["primary_diagnosis"],
                request.form["medications"],
                request.form["dietary_restrictions"],
                request.form["follow_up"],
                request.form["warning_signs"],
                request.form["discharge_instructions"]
            )

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO discharge_summaries 
                (patient_name, discharge_date, primary_diagnosis, medications, dietary_restrictions, follow_up, warning_signs, discharge_instructions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, data)
            conn.commit()
            conn.close()

            flash(f"Patient '{data[0]}' added successfully!")
            return redirect(url_for("add_patient"))

        except Exception as e:
            flash(f"Error: {str(e)}")
            return redirect(url_for("add_patient"))

    return render_template_string(FORM_HTML)

if __name__ == "__main__":
    app.run(debug=True)
