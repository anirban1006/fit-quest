from flask import send_from_directory, Flask, request, jsonify
from flask_cors import CORS
from flask_mysqldb import MySQL
import os
from dotenv import load_dotenv
import pymysql.cursors  # Used by flask-mysqldb for DictCursor

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- MySQL configurations ---
app.config['MYSQL_HOST'] = os.environ.get('DB_HOST', 'sql12.freesqldatabase.com')
app.config['MYSQL_PORT'] = int(os.environ.get('DB_PORT', '3306'))
app.config['MYSQL_DB'] = os.environ.get('DB_NAME', 'sql12804493')
app.config['MYSQL_USER'] = os.environ.get('DB_USER', 'sql12804493')
app.config['MYSQL_PASSWORD'] = os.environ.get('DB_PASSWORD', 'nBmLGyzpMb')
app.config['MYSQL_CHARSET'] = 'utf8mb4'
app.config['MYSQL_CONNECT_TIMEOUT'] = 10
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'  # For dictionary-based results

# Initialize MySQL
mysql = MySQL(app)

# --- Goal Endpoints ---

@app.route('/api/goals', methods=['GET'])
def get_goals():
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM goals ORDER BY created_at DESC')
        goals = cursor.fetchall()
        return jsonify(goals)
    except Exception as e:
        print(f"Query error: {e}")
        return jsonify({'error': 'Failed to load goals'}), 500
    finally:
        if cursor:
            cursor.close()

@app.route('/api/goals', methods=['POST'])
def add_goal():
    cursor = None
    try:
        data = request.json
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO goals (goal_type, target_value, unit, deadline, status) VALUES (%s, %s, %s, %s, %s)',
                       (data['goal_type'], data['target_value'], data.get('unit'),
                        data.get('deadline'), data.get('status', 'Pending')))
        mysql.connection.commit()
        return jsonify({'id': cursor.lastrowid, 'message': 'Goal added successfully'}), 201
    except (KeyError, TypeError) as e:
        print(f"Error adding goal: {e}")
        return jsonify({'error': 'Invalid or missing data in request'}), 400
    except Exception as e:
        print(f"Database error adding goal: {e}")
        return jsonify({'error': 'Database error'}), 500
    finally:
        if cursor:
            cursor.close()

@app.route('/api/goals/<int:goal_id>', methods=['DELETE'])
def delete_goal(goal_id):
    """DELETES a specific goal."""
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('DELETE FROM goals WHERE id = %s', (goal_id,))
        mysql.connection.commit()
        return jsonify({'message': 'Goal deleted successfully'})
    except Exception as e:
        print(f"Error deleting goal: {e}")
        return jsonify({'error': 'Failed to delete goal'}), 500
    finally:
        if cursor:
            cursor.close()

# --- Workout Endpoints ---

@app.route('/api/workouts', methods=['GET'])
def get_workouts():
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM workouts ORDER BY created_at DESC')
        workouts = cursor.fetchall()
        return jsonify(workouts)
    except Exception as e:
        print(f"Query error: {e}")
        return jsonify({'error': 'Failed to load workouts'}), 500
    finally:
        if cursor:
            cursor.close()

@app.route('/api/workouts', methods=['POST'])
def add_workout():
    cursor = None
    try:
        data = request.json
        if not all(key in data for key in ['date', 'type', 'duration', 'calories']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO workouts (date, type, duration, calories, intensity, distance, notes) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                       (data['date'], data['type'], data['duration'], data['calories'],
                        data.get('intensity'), data.get('distance'), data.get('notes')))
        mysql.connection.commit()
        return jsonify({'id': cursor.lastrowid, 'message': 'Workout added successfully'}), 201
    except (KeyError, TypeError) as data_error:
        app.logger.error(f"Data error: {data_error}")
        return jsonify({'error': 'Invalid or missing data in request'}), 400
    except Exception as db_error:
        app.logger.error(f"Database error: {db_error}")
        return jsonify({'error': f'Database error: {db_error}'}), 500
    finally:
        if cursor:
            cursor.close()

@app.route('/api/workouts/<int:workout_id>', methods=['DELETE'])
def delete_workout(workout_id):
    """DELETES a specific workout."""
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('DELETE FROM workouts WHERE id = %s', (workout_id,))
        mysql.connection.commit()
        return jsonify({'message': 'Workout deleted successfully'})
    except Exception as e:
        print(f"Error deleting workout: {e}")
        return jsonify({'error': 'Failed to delete workout'}), 500
    finally:
        if cursor:
            cursor.close()

# --- Meal Endpoints ---

@app.route('/api/meals/daily/<date>', methods=['GET'])
def get_daily_meals(date):
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM meals WHERE date = %s ORDER BY created_at ASC', (date,))
        meals = cursor.fetchall()
        cursor.execute('SELECT SUM(calories) as calories, SUM(protein) as protein, SUM(carbs) as carbs, SUM(fats) as fats FROM meals WHERE date = %s', (date,))
        totals = cursor.fetchone()
        return jsonify({
            'meals': meals,
            'totals': {
                'calories': totals['calories'] or 0,
                'protein': totals['protein'] or 0,
                'carbs': totals['carbs'] or 0,
                'fats': totals['fats'] or 0
            }
        })
    except Exception as e:
        print(f"Query error: {e}")
        return jsonify({'error': 'Failed to load meals'}), 500
    finally:
        if cursor:
            cursor.close()

@app.route('/api/meals', methods=['POST'])
def add_meal():
    cursor = None
    try:
        data = request.json
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO meals (date, meal_type, food_name, calories, protein, carbs, fats, portion_size, notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                       (data['date'], data['meal_type'], data['food_name'], data['calories'],
                        data.get('protein', 0), data.get('carbs', 0), data.get('fats', 0),
                        data.get('portion_size'), data.get('notes')))
        mysql.connection.commit()
        return jsonify({'id': cursor.lastrowid, 'message': 'Meal added successfully'}), 201
    except (KeyError, TypeError) as e:
        print(f"Error adding meal: {e}")
        return jsonify({'error': 'Invalid or missing data in request'}), 400
    except Exception as e:
        print(f"Database error adding meal: {e}")
        return jsonify({'error': 'Database error'}), 500
    finally:
        if cursor:
            cursor.close()

@app.route('/api/meals/<int:meal_id>', methods=['DELETE'])
def delete_meal(meal_id):
    """DELETES a specific meal."""
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('DELETE FROM meals WHERE id = %s', (meal_id,))
        mysql.connection.commit()
        return jsonify({'message': 'Meal deleted successfully'})
    except Exception as e:
        print(f"Error deleting meal: {e}")
        return jsonify({'error': 'Failed to delete meal'}), 500
    finally:
        if cursor:
            cursor.close()

# --- Calorie Goal Endpoints ---

@app.route('/api/calorie-goals/<date>', methods=['GET'])
def get_calorie_goal(date):
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM calorie_goals WHERE date = %s', (date,))
        goal = cursor.fetchone()
        return jsonify(goal if goal else None)
    except Exception as e:
        print(f"Query error: {e}")
        return jsonify({'error': 'Failed to load calorie goal'}), 500
    finally:
        if cursor:
            cursor.close()

@app.route('/api/calorie-goals', methods=['POST'])
def set_calorie_goal():
    cursor = None
    try:
        data = request.json
        cursor = mysql.connection.cursor()
        # Use MySQL's ON DUPLICATE KEY UPDATE to insert or update
        cursor.execute('INSERT INTO calorie_goals (date, daily_goal, achieved) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE daily_goal = %s, achieved = %s',
                       (data['date'], data['daily_goal'], data.get('achieved', 0),
                        data['daily_goal'], data.get('achieved', 0)))
        mysql.connection.commit()
        return jsonify({'message': 'Calorie goal set successfully'}), 201
    except (KeyError, TypeError) as e:
        print(f"Error setting calorie goal: {e}")
        return jsonify({'error': 'Invalid or missing data in request'}), 400
    except Exception as e:
        print(f"Database error setting calorie goal: {e}")
        return jsonify({'error': 'Database error'}), 500
    finally:
        if cursor:
            cursor.close()

# --- Stats Endpoint ---

@app.route('/api/stats', methods=['GET'])
def get_stats():
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM workouts')
        total_workouts = cursor.fetchone()['count']
        
        cursor.execute('SELECT IFNULL(SUM(calories), 0) as total FROM workouts')
        total_calories_burned = cursor.fetchone()['total']
        
        cursor.execute('SELECT IFNULL(SUM(duration), 0) as total FROM workouts')
        total_duration = cursor.fetchone()['total']
        
        cursor.execute('SELECT IFNULL(SUM(calories), 0) as total FROM meals')
        total_calories_consumed = cursor.fetchone()['total']
        
        return jsonify({
            'total_workouts': total_workouts,
            'total_calories_burned': float(total_calories_burned), # Ensure it's a float/int
            'total_duration': float(total_duration), # Ensure it's a float/int
            'total_calories_consumed': float(total_calories_consumed), # Ensure it's a float/int
            'net_calories': float(total_calories_consumed) - float(total_calories_burned)
        })
    except Exception as e:
        print(f"Query error: {e}")
        return jsonify({'error': 'Failed to load stats'}), 500
    finally:
        if cursor:
            cursor.close()

# --- Serve Frontend ---

@app.route('/')
def serve_frontend():
    """Serves the index.html file."""
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)