from flask import Flask
import cv2
from flask import request
from flask import render_template
# from newencode import signin_user
from encode import onlyregisterface, mark_attendance
from database import init_db
from database import get_attendance_by_date

app = Flask(__name__)

init_db()
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/mark_attendance", methods=['GET','POST'])
def Mark_attendance():
    if request.method == 'GET':
        result, user_id = mark_attendance()
        return render_template("mark_attendance.html", status=result, id=user_id)

    return render_template('mark_attendance.html')

@app.route("/onlyregisterface" , methods=['GET','POST'])
def Register():
    if request.method == 'POST':
        username = request.form.get('username')
        id = request.form.get('id')
        # onlyregisterface(username,id)
        # return render_template('register.html',username=username)
        result = onlyregisterface(username, id)
        return render_template("register.html", username=username, status=result)
    return render_template('register.html')

@app.route("/view_attendance", methods=["GET", "POST"])
def view_attendance():
    records = []
    selected_date = None

    if request.method == "POST":
        selected_date = request.form.get("date")
        records = get_attendance_by_date(selected_date)

    return render_template(
        "attendance_view.html", records=records, selected_date=selected_date)



if __name__ == "__main__":
    app.run(debug=True)