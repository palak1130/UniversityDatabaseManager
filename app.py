

import os
from dotenv import load_dotenv
from flask import Flask, render_template, abort, request, redirect, url_for, flash
import mysql.connector

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE", "university_db")
    )


def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Palak@301106",
        database="university_db"
    )


@app.route("/")
def home():
    tables = [
        "Department",
        "Student",
        "Instructor",
        "Course",
        "Section",
        "Enrollment",
        "Exam",
        "Result"
    ]

    connection = get_connection()
    cursor = connection.cursor()

    stats = {}

    try:
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
            stats[table] = cursor.fetchone()[0]
    finally:
        cursor.close()
        connection.close()

    return render_template("index.html", stats=stats)


@app.route("/table/<table>")
def view_table(table):
    tables = [
        "Department",
        "Student",
        "Instructor",
        "Course",
        "Section",
        "Enrollment",
        "Exam",
        "Result"
    ]

    if table not in tables:
        abort(404)

    search = request.args.get("search", "").strip()

    connection = get_connection()
    cursor = connection.cursor(dictionary=True, buffered=True)

    try:
        cursor.execute(f"SELECT * FROM `{table}` LIMIT 0")
        columns = [item[0] for item in cursor.description]

        query = f"SELECT * FROM `{table}`"
        values = []

        if search:
            conditions = [
                f"CAST(`{column}` AS CHAR) LIKE %s"
                for column in columns
            ]

            query += " WHERE " + " OR ".join(conditions)
            values = [f"%{search}%"] * len(columns)

        query += " ORDER BY 1"

        cursor.execute(query, values)
        records = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    
    return render_template(
    "table.html",
    table=table,
    records=records,
    columns=columns,
    search=search,
    delete_keys=DELETE_KEYS[table]
)



    
@app.route("/add/<table>", methods=["GET", "POST"])
def add_record(table):
    allowed_tables = {
        "Department": ["dept_id", "dept_name", "building"],
        "Student": [
            "student_id", "name", "email",
            "dept_id", "phone_number", "dob"
        ],
        "Instructor": [
            "ins_id", "name", "email", "salary", "dept_id"
        ],
        "Course": ["course_id", "course_name", "credits", "dept_id"],
        "Section": [
            "sec_id", "course_id", "instructor_id", "semester", "year"
        ],
        "Enrollment": [
            "student_id", "sec_id", "enroll_date", "grade"
        ],
        "Exam": ["exam_id", "sec_id", "exam_date", "exam_type"],
        "Result": ["student_id", "exam_id", "marks", "grade"]
    }

    if table not in allowed_tables:
        abort(404)

    columns = allowed_tables[table]

    if request.method == "POST":
        values = [request.form.get(column) for column in columns]
        placeholders = ", ".join(["%s"] * len(columns))
        column_names = ", ".join(f"`{column}`" for column in columns)

        connection = get_connection()
        cursor = connection.cursor()

        try:
            query = (
                f"INSERT INTO `{table}` ({column_names}) "
                f"VALUES ({placeholders})"
            )
            cursor.execute(query, values)
            connection.commit()
        except mysql.connector.Error as error:
            connection.rollback()
            return render_template(
                "form.html",
                table=table,
                columns=columns,
                error=str(error)
            ), 400
        finally:
            cursor.close()
            connection.close()

        return redirect(url_for("view_table", table=table))

    return render_template(
        "form.html",
        table=table,
        columns=columns,
        error=None,
        is_edit=False
    )


    if table not in tables:
        abort(404)

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(f"SELECT * FROM `{table}`")
        records = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

    columns = list(records[0].keys()) if records else []

    return render_template(
        "table.html",
        table=table,
        records=records,
        columns=columns,
        is_edit=False
    )




# Tables and their primary keys
PRIMARY_KEYS = {
    "Department": "dept_id",
    "Student": "student_id",
    "Instructor": "ins_id",
    "Course": "course_id",
    "Section": "sec_id",
    "Exam": "exam_id"
}


@app.route("/edit/<table>/<int:record_id>", methods=["GET", "POST"])
def edit_record(table, record_id):
    if table not in PRIMARY_KEYS:
        abort(404)

    primary_key = PRIMARY_KEYS[table]

    allowed_columns = {
        "Department": ["dept_id", "dept_name", "building"],
        "Student": [
            "student_id", "name", "email",
            "dept_id", "phone_number", "dob"
        ],
        "Instructor": [
            "ins_id", "name", "email", "salary", "dept_id"
        ],
        "Course": ["course_id", "course_name", "credits", "dept_id"],
        "Section": [
            "sec_id", "course_id", "instructor_id", "semester", "year"
        ],
        "Exam": ["exam_id", "sec_id", "exam_date", "exam_type"]
    }

    columns = allowed_columns[table]
    connection = get_connection()
    cursor = connection.cursor(dictionary=True, buffered=True)

    try:
        if request.method == "POST":
            values = [request.form.get(column) for column in columns]
            assignments = ", ".join(
                f"`{column}` = %s"
                for column in columns
                if column != primary_key
            )
            update_values = [
                request.form.get(column)
                for column in columns
                if column != primary_key
            ]

            cursor.execute(
                f"UPDATE `{table}` SET {assignments} "
                f"WHERE `{primary_key}` = %s",
                update_values + [record_id]
            )
            connection.commit()
            return redirect(url_for("view_table", table=table))

        cursor.execute(
            f"SELECT * FROM `{table}` WHERE `{primary_key}` = %s",
            (record_id,)
        )
        record = cursor.fetchone()

        if record is None:
            abort(404)

    except mysql.connector.Error as error:
        connection.rollback()
        return render_template(
            "form.html",
            table=f"Edit {table}",
            columns=columns,
            error=str(error),
            record=request.form,
            is_edit=True
        ), 400

    finally:
        cursor.close()
        connection.close()

    return render_template(
        "form.html",
        table=f"Edit {table}",
        columns=columns,
        error=None,
        record=record,
        is_edit=True
    )

# Primary keys used for safe deletion
DELETE_KEYS = {
    "Department": ["dept_id"],
    "Student": ["student_id"],
    "Instructor": ["ins_id"],
    "Course": ["course_id"],
    "Section": ["sec_id"],
    "Enrollment": ["student_id", "sec_id"],
    "Exam": ["exam_id"],
    "Result": ["student_id", "exam_id"]
}


@app.route("/delete/<table>", methods=["POST"])
def delete_record(table):
    if table not in DELETE_KEYS:
        abort(404)

    primary_keys = DELETE_KEYS[table]

    # Get the primary-key values from the submitted form
    key_values = [
        request.form.get(key)
        for key in primary_keys
    ]

    if any(value is None or value == "" for value in key_values):
        abort(400)

    conditions = " AND ".join(
        f"`{key}` = %s" for key in primary_keys
    )

    connection = get_connection()
    cursor = connection.cursor()

    try:
        query = f"DELETE FROM `{table}` WHERE {conditions}"
        cursor.execute(query, key_values)

        if cursor.rowcount == 0:
            connection.rollback()
            flash("Record not found. Nothing was deleted.", "error")
        else:
            connection.commit()
            flash(f"{table} record deleted successfully.", "success")

    except mysql.connector.Error:
        connection.rollback()
        flash(
            "Could not delete this record. Other records may depend on it "
            "through foreign-key relationships.",
            "error"
        )

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("view_table", table=table))

if __name__ == "__main__":
    app.run(debug=True)