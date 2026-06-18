from flask import Flask, render_template, request, redirect, jsonify
from flask_mysqldb import MySQL
from dotenv import load_dotenv
from datetime import date
import os

load_dotenv()

app = Flask(__name__)

# ---------------------------
# MySQL Configuration
# ---------------------------

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

mysql = MySQL(app)


# ==================================================
# DASHBOARD
# ==================================================
@app.route('/')
def dashboard():

    cur = mysql.connection.cursor()

    # Total Equipment
    cur.execute("SELECT COUNT(*) FROM equipment")
    total_equipment = cur.fetchone()[0]

    # Active
    cur.execute(
        "SELECT COUNT(*) FROM equipment WHERE status='Active'"
    )
    active_count = cur.fetchone()[0]

    # Under Maintenance
    cur.execute(
        "SELECT COUNT(*) FROM equipment WHERE status='Under Maintenance'"
    )
    maintenance_count = cur.fetchone()[0]

    # Decommissioned
    cur.execute(
        "SELECT COUNT(*) FROM equipment WHERE status='Decommissioned'"
    )
    decommissioned_count = cur.fetchone()[0]

    # Overdue maintenance
    cur.execute("""
        SELECT e.equipment_name,
               e.department,
               m.next_due_date
        FROM maintenance_log m
        JOIN equipment e
        ON e.equipment_id = m.equipment_id
        WHERE m.next_due_date < CURDATE()
    """)

    overdue_items = cur.fetchall()

    overdue_list = []

    for item in overdue_items:
        overdue_list.append({
            "equipment_name": item[0],
            "department": item[1],
            "next_due_date": item[2]
        })

    cur.close()

    return render_template(
        "dashboard.html",
        total_equipment=total_equipment,
        active_count=active_count,
        maintenance_count=maintenance_count,
        decommissioned_count=decommissioned_count,
        overdue_items=overdue_list
    )


# ==================================================
# ADD EQUIPMENT
# ==================================================
@app.route('/add-equipment', methods=['GET', 'POST'])
def add_equipment():

    if request.method == 'POST':

        equipment_name = request.form['equipment_name']
        serial_number = request.form['serial_number']
        department = request.form['department']
        purchase_date = request.form['purchase_date']
        status = request.form['status']

        cur = mysql.connection.cursor()

        cur.execute("""
            INSERT INTO equipment
            (
                equipment_name,
                serial_number,
                department,
                purchase_date,
                status
            )
            VALUES (%s,%s,%s,%s,%s)
        """, (
            equipment_name,
            serial_number,
            department,
            purchase_date,
            status
        ))

        mysql.connection.commit()
        cur.close()

        return redirect('/equipment')

    return render_template('add_equipment.html')


# ==================================================
# EQUIPMENT LIST
# ==================================================
@app.route('/equipment')
def equipment_list():

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
        equipment_id,
        equipment_name,
        serial_number,
        department,
        purchase_date,
        status
        FROM equipment
    """)

    rows = cur.fetchall()

    equipments = []

    for row in rows:
        equipments.append({
            "equipment_id": row[0],
            "equipment_name": row[1],
            "serial_number": row[2],
            "department": row[3],
            "purchase_date": row[4],
            "status": row[5]
        })

    cur.close()

    return render_template(
        "equipment_list.html",
        equipments=equipments
    )


# ==================================================
# EQUIPMENT DETAILS
# ==================================================
@app.route('/equipment/<int:id>')
def equipment_details(id):

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT *
        FROM equipment
        WHERE equipment_id=%s
    """, (id,))

    row = cur.fetchone()

    equipment = {
        "equipment_id": row[0],
        "equipment_name": row[1],
        "serial_number": row[2],
        "department": row[3],
        "purchase_date": row[4],
        "status": row[5]
    }

    cur.execute("""
        SELECT
        maintenance_date,
        technician_name,
        issue_reported,
        resolution_notes,
        next_due_date
        FROM maintenance_log
        WHERE equipment_id=%s
        ORDER BY maintenance_date DESC
    """, (id,))

    logs = cur.fetchall()

    maintenance_logs = []

    for log in logs:
        maintenance_logs.append({
            "maintenance_date": log[0],
            "technician_name": log[1],
            "issue_reported": log[2],
            "resolution_notes": log[3],
            "next_due_date": log[4]
        })

    cur.close()

    return render_template(
        "equipment_details.html",
        equipment=equipment,
        maintenance_logs=maintenance_logs
    )


# ==================================================
# ADD MAINTENANCE
# ==================================================
@app.route('/add-maintenance/<int:id>',
           methods=['GET', 'POST'])
def add_maintenance(id):

    if request.method == 'POST':

        maintenance_date = request.form['maintenance_date']
        technician_name = request.form['technician_name']
        issue_reported = request.form['issue_reported']
        resolution_notes = request.form['resolution_notes']
        next_due_date = request.form['next_due_date']

        cur = mysql.connection.cursor()

        cur.execute("""
            INSERT INTO maintenance_log
            (
                equipment_id,
                maintenance_date,
                technician_name,
                issue_reported,
                resolution_notes,
                next_due_date
            )
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (
            id,
            maintenance_date,
            technician_name,
            issue_reported,
            resolution_notes,
            next_due_date
        ))

        mysql.connection.commit()
        cur.close()

        return redirect(f'/equipment/{id}')

    return render_template(
        'add_maintenance.html'
    )


# ==================================================
# UPDATE STATUS
# ==================================================
@app.route('/update-status/<int:id>',
           methods=['GET', 'POST'])
def update_status(id):

    cur = mysql.connection.cursor()

    if request.method == 'POST':

        status = request.form['status']

        cur.execute("""
            UPDATE equipment
            SET status=%s
            WHERE equipment_id=%s
        """, (status, id))

        mysql.connection.commit()

        return redirect(f'/equipment/{id}')

    cur.execute("""
        SELECT *
        FROM equipment
        WHERE equipment_id=%s
    """, (id,))

    row = cur.fetchone()

    equipment = {
        "equipment_id": row[0],
        "equipment_name": row[1],
        "serial_number": row[2],
        "department": row[3],
        "purchase_date": row[4],
        "status": row[5]
    }

    cur.close()

    return render_template(
        'update_status.html',
        equipment=equipment
    )


# ==================================================
# JSON API
# ==================================================
@app.route('/api/overdue')
def overdue_json():

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
        e.equipment_id,
        e.equipment_name,
        e.department,
        m.next_due_date
        FROM maintenance_log m
        JOIN equipment e
        ON e.equipment_id=m.equipment_id
        WHERE m.next_due_date < CURDATE()
    """)

    rows = cur.fetchall()

    data = []

    for row in rows:
        data.append({
            "equipment_id": row[0],
            "equipment_name": row[1],
            "department": row[2],
            "next_due_date": str(row[3])
        })

    cur.close()

    return jsonify(data)


if __name__ == '__main__':
    app.run(debug=True)