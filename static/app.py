from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash
import mysql.connector
from flask import render_template
import hashlib
from datetime import datetime, timedelta

app = Flask(__name__)

db_config = {
    'host': 'vtmotorsportsinv-server.mysql.database.azure.com',
    'user': 'udugeqkkup',
    'password': '7QJYY876G6BB8125$',
    'database': 'vtm'
}

app.secret_key = 'your_secret_key' 

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    else: 
        return render_template('index.html')

@app.route('/delete/<part_number>', methods=['GET'])
@app.route('/delete/<part_number>', methods=['DELETE'])
def delete_item(part_number):
    if 'username' not in session or session.get('role') != 'Lead':
        return jsonify({"message": "You don't have the permissions necessary to delete"}), 401

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(buffered=True)

    delete_query = "DELETE FROM items WHERE `Part Number` = %s"
    cursor.execute(delete_query, (part_number,))
        
    log_action(cursor, 'delete', part_number)

    conn.commit()
    cursor.close()
    conn.close()
    log_change('delete', part_number)

    return jsonify({"message": "Item deleted successfully"})

@app.route('/insert', methods=['GET', 'POST'])
def insert():
    if 'username' not in session or session.get('role') != 'Lead':
        return jsonify({"message": "You don't have the permissions necessary to insert"}), 401

    if request.method == 'POST':
        partNumber = request.form.get('partNumber')
        try:
            quantity = int(request.form.get('quantity'))
        except ValueError:
            quantity = 0  

        description = request.form.get('description')
        location = request.form.get('location')
        link = request.form.get('link')
        price = request.form.get('price')
        type = request.form.get('type')
        cabinet = request.form.get('cabinet')
        subteam = request.form.get('subteam')
        # dateadded = request.form.get('datadded')

        dateadded = datetime.now().strftime('%m/%d/%Y')  

        if isinstance(price, str) and not price.startswith('$'):
            price = f'${price}'

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(buffered=True)

        insert_query = "INSERT INTO items (`Part Number`, `Quantity`, `Description`, `Location`, `Link`, `Price`, `Type`, `Cabinet`, `Subteam`, `DateAdded`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(insert_query, (partNumber, quantity, description, location, link, price, type, cabinet, subteam, dateadded))
        log_action(cursor, 'insert', partNumber)
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('index'))

    return render_template('insert.html')

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    if 'username' not in session:
        return jsonify({"message": "Unauthorized"}), 401

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM items"
    cursor.execute(query)
    records = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(records)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(buffered=True)

        try:
            select_query = "SELECT * FROM members WHERE Username = %s"
            cursor.execute(select_query, (username,))
            user = cursor.fetchone()

            if user:
                stored_password = user[4]  
                hashed_password = hashlib.sha256(password.encode()).hexdigest()


                if stored_password == hashed_password:
                    session['username'] = username
                    session['role'] = user[5]  
                    print (session['role'])
                    return redirect(url_for('index'))
                else:
                    message = 'Invalid username or password.'
                    return render_template('login.html', message=message)
            else:
                message = 'Invalid username or password.'
                return render_template('login.html', message=message)
            
        except Exception as e:
            return jsonify({"message": f"Error: {str(e)}"})
        finally:
            cursor.close()
            conn.close()
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('firstname')
        last_name = request.form.get('lastname')
        username = request.form.get('username')
        password = request.form.get('password')

        if not (first_name and last_name and username and password):
            return jsonify({"message": "All fields are required."})

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(buffered=True)

        try:
            select_query = "SELECT * FROM members WHERE FirstName = %s AND LastName = %s"
            cursor.execute(select_query, (first_name, last_name))
            user = cursor.fetchone()

            if user:
                update_query = "UPDATE members SET Username = %s, Password = %s WHERE FirstName = %s AND LastName = %s"
                hashed_password = hashlib.sha256(password.encode()).hexdigest()
                cursor.execute(update_query, (username, hashed_password, first_name, last_name))
                conn.commit()
            else:
               message = "User not found in the database. Please check your first name and last name."
               return render_template('registration.html', message=message)

            session['username'] = username
            return redirect(url_for('login'))
        except Exception as e:
            return jsonify({"message": f"Error: {str(e)}"})
        finally:
            cursor.close()
            conn.close()

    return render_template('registration.html')

  
@app.route('/changepassword', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            return render_template('changepassword.html', message="New passwords do not match.")

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(buffered=True)

        try:
            username = session['username']
            select_query = "SELECT * FROM members WHERE Username = %s"
            cursor.execute(select_query, (username,))
            user = cursor.fetchone()

            if user:
                stored_password = user[4]  
                hashed_old_password = hashlib.sha256(old_password.encode()).hexdigest()

                if stored_password != hashed_old_password:
                    return render_template('changepassword.html', message="Old password is incorrect.")

                hashed_new_password = hashlib.sha256(new_password.encode()).hexdigest()
                update_query = "UPDATE members SET Password = %s WHERE Username = %s"
                cursor.execute(update_query, (hashed_new_password, username))
                conn.commit()

                return render_template('login.html', message="Password successfully changed.")
            else:
                return render_template('changepassword.html', message="User not found.")

        except Exception as e:
            return jsonify({"message": f"Error: {str(e)}"})
        finally:
            cursor.close()
            conn.close()

    return render_template('changepassword.html')

@app.route('/make_lead', methods=['GET', 'POST'])
def make_lead():
    if 'username' not in session or session.get('role') != 'Lead':
        flash("You do not have permission to access this page.", "error")
        return redirect(url_for('index'))

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        user_to_update = request.form.get('user_pid')
        update_query = "UPDATE members SET Role = 'Lead' WHERE PID = %s"
        cursor.execute(update_query, (user_to_update,))
        conn.commit()

        return redirect(url_for('make_lead'))

    cursor.execute("SELECT PID, FirstName, LastName, Role FROM members")
    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('make_lead.html', users=users)


@app.route('/edit/<part_number>', methods=['GET'])
def edit_item(part_number):
    if 'username' not in session or session.get('role') != 'Lead':
        flash("You do not have permission to access this page.", "error")
        return redirect(url_for('login'))

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM items WHERE `Part Number` = %s"
    cursor.execute(query, (part_number,))
    item = cursor.fetchone()
    log_action(cursor, 'edit', part_number)

    cursor.close()
    conn.close()

    if item:
        log_change('edit', part_number)
        return render_template('edit.html', item=item)
    else:
        flash("Item not found.", "error")
        return redirect(url_for('index'))


@app.route('/update/<part_number>', methods=['POST'])
def update_item(part_number):
    if 'username' not in session or session.get('role') != 'Lead':
        flash("You do not have permission to perform this action.", "error")
        return redirect(url_for('login'))

    updated_partNumber = request.form.get('partNumber')
    updated_quantity = request.form.get('quantity')
    updated_description = request.form.get('description')
    updated_location = request.form.get('location')
    updated_link = request.form.get('link')
    updated_price = request.form.get('price')
    updated_type = request.form.get('type')
    updated_cabinet = request.form.get('cabinet')
    updated_subteam = request.form.get('subteam')

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(buffered=True)

    update_query = """
    UPDATE items SET 
    `Part Number` = %s, 
    `Quantity` = %s, 
    `Description` = %s, 
    `Location` = %s, 
    `Link` = %s, 
    `Price` = %s, 
    `Type` = %s, 
    `Cabinet` = %s, 
    `Subteam` = %s
    WHERE `Part Number` = %s
    """
    cursor.execute(update_query, (updated_partNumber, updated_quantity, updated_description, updated_location, updated_link, updated_price, updated_type, updated_cabinet, updated_subteam, part_number))
    conn.commit()

    cursor.close()
    conn.close()

    flash("Item updated successfully.", "success")
    return redirect(url_for('index'))




def log_change(action, part_number):
    try:
        timestamp = datetime.utcnow()
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(buffered=True)

        query = "INSERT INTO change_log (action, part_number, timestamp) VALUES (%s, %s, %s)"
        values = (action, part_number, timestamp)

        cursor.execute(query, values)
        conn.commit()

        print("Logged change:", action, part_number, timestamp) 

    except Exception as e:
        print("Error logging change:", e)  

    finally:
        cursor.close()
        conn.close()

@app.route('/stat_report')
def stat_report():
    if 'username' not in session:
        return redirect(url_for('login'))

    stats_data = get_stats()
    return render_template('stat_report.html', stats_data=stats_data)

def get_stats():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    stats_data = {}

    time_periods = {
        'last_24_hours': datetime.utcnow() - timedelta(days=1),
        'last_7_days': datetime.utcnow() - timedelta(days=7),
        'last_30_days': datetime.utcnow() - timedelta(days=30)
    }

    for period, start_time in time_periods.items():
        cursor.execute("""
            SELECT action, COUNT(*) as count 
            FROM change_log 
            WHERE timestamp >= %s
            GROUP BY action
        """, (start_time,))
        actions_count = cursor.fetchall()

        stats = {'added': 0, 'edited': 0, 'deleted': 0}
        for action in actions_count:
            if action['action'] == 'insert':
                stats['added'] = action['count']
            elif action['action'] == 'update':
                stats['edited'] = action['count']
            elif action['action'] == 'delete':
                stats['deleted'] = action['count']

        stats_data[period] = stats

    cursor.close()
    conn.close()

    return stats_data


@app.route('/get_change_details')
def get_change_details():
    action = request.args.get('action')

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT part_number, timestamp 
        FROM change_log 
        WHERE action = %s
    """, (action,))
    
    details = cursor.fetchall()
    print("Details fetched:", details)

    cursor.close()
    conn.close()

    return jsonify(details)


def get_time_range(period_key):
    now = datetime.utcnow()
    if period_key == 'last_24_hours':
        return now - timedelta(hours=24)
    elif period_key == 'last_7_days':
        return now - timedelta(days=7)
    elif period_key == 'last_30_days':
        return now - timedelta(days=30)
    else:
        return None



def log_action(cursor, action, part_number):
    user = session.get('username')  
    if not user:
        raise Exception("No logged-in user found")

    timestamp = datetime.now().strftime('%m/%d/%Y')
    query = "INSERT INTO change_log (user, action, part_number, timestamp) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (user, action, part_number, timestamp))



@app.route('/lead_report')
def lead_report():
    if 'username' not in session or session.get('role') != 'Lead':
        flash("You need to login to access this page.", "error")
        return redirect(url_for('login'))

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM change_log ORDER BY timestamp DESC"
    cursor.execute(query)
    logs = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('lead_report.html', logs=logs)



if __name__ == "__main__":
    app.run(debug=True)
