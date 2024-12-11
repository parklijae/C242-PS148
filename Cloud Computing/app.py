import flask
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from google.cloud.sql.connector import Connector
from google.cloud import storage
import pymysql
import os
import uuid
import shutil
from io import BytesIO
from werkzeug.security import generate_password_hash, check_password_hash
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from PIL import Image
import numpy as np
import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

load_dotenv()

# Flask setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mE1rYpH35gXfzsxuiJc1'

app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'  # Ganti dengan secret key yang aman
jwt = JWTManager(app)


# Inisialisasi Storage
storage_client = storage.Client()
BUCKET_NAME = os.getenv("BUCKET_NAME")

# Load models
model_absen_path = os.getenv('MODEL_ABSEN_PATH')
model_dasi_path = os.getenv('MODEL_DASI_PATH')
model_mood_path = os.getenv('MODEL_MOOD_PATH')

class_labels = ['liza', 'nabila', 'noface', 'zain']
class_names = ['angry', 'happy', 'neutral', 'sad']

IMAGE_UPLOAD_DIR = 'storage/attendance_images'
IMAGE_PUBLIC_URL_BASE = 'https://checkmate-506488875993.asia-southeast2.run.app/storage/attendance_images/'  # Base URL untuk akses frontend


# Pastikan direktori sudah ada
os.makedirs(IMAGE_UPLOAD_DIR, exist_ok=True)

def connect_db():
    connector = Connector()
    # Connection to Cloud SQL instance
    connection = connector.connect(
        os.getenv("CLOUD_SQL_CONNECTION_NAME"),  # Ganti dengan Connection Name dari Cloud SQL
        "pymysql",
        user=os.getenv("DB_USER"),  # Username MySQL
        password=os.getenv("DB_PASSWORD"),  # Password MySQL
        db=os.getenv("DB_NAME")  # Nama Database
    )
    return connection

def load_model_from_url(model_url, temp_file_name):
    try:
        # Ambil file model dari URL
        response = requests.get(model_url)
        response.raise_for_status()
        with open(temp_file_name, "wb") as f:
            f.write(response.content)
        print(f"Model {temp_file_name} downloaded successfully from URL.")
        return load_model(temp_file_name)
    except Exception as e:
        print(f"Error loading model from URL: {e}")
        raise e


model_absen = load_model_from_url(model_absen_path, "temp_TF100.keras")
model_dasi = load_model_from_url(model_dasi_path, "temp_dasidasi.keras")
model_mood = load_model_from_url(model_mood_path, "temp_ekspresi.h5")


# Register user
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username, email, student_number, password, role = (
        data['username'], data['email'], data['student_number'], 
        data['password'], data['role']
    )
    hashed_password = generate_password_hash(password)
    
    connection = connect_db()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Check if email already exists
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return jsonify({"status": "error", "message": "Email already exists"}), 400

            # Insert user
            cursor.execute(
                "INSERT INTO users (username, email, student_number, password, role) VALUES (%s, %s, %s, %s, %s)",
                (username, email, student_number, hashed_password, role)
            )
            user_id = cursor.lastrowid
            
            # Insert into specific tables based on role
            if role == 'siswa':
                cursor.execute("INSERT INTO siswa (user_id) VALUES (%s)", (user_id,))
            elif role == 'guru':
                cursor.execute("INSERT INTO guru (user_id) VALUES (%s)", (user_id,))
            elif role == 'orang_tua':
                cursor.execute("INSERT INTO orang_tua (user_id, student_id) VALUES (%s, NULL)", (user_id,))
                
        connection.commit()
        return jsonify({"status": "success", "message": "User registered successfully"}), 201
    except Exception as e:
        connection.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        connection.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    identifier, password = data['email'], data['password']
    
    connection = connect_db()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Cek apakah identifier adalah email atau username
            if '@' in identifier:
                cursor.execute(
                    "SELECT id, password, role, email, username, student_number FROM users WHERE email=%s", 
                    (identifier,)
                )
            else:
                cursor.execute(
                    "SELECT id, password, role, email, username, student_number FROM users WHERE username=%s", 
                    (identifier,)
                )

            user = cursor.fetchone()

            if user and check_password_hash(user['password'], password):
                # Buat access token dengan waktu kedaluwarsa 2 jam
                access_token = create_access_token(
                    identity=str(user['username']), 
                    expires_delta=timedelta(hours=2)
                )
                return jsonify({
                    "status": "success",
                    "message": "Login successful",
                    "access_token": access_token,
                    "user": {
                        "email": user['email'],
                        "username": user['username'],
                        "student_number": user['student_number'],
                        "role": user['role']
                    }
                })
            
            return jsonify({"status": "error", "message": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        connection.close()

def get_current_user():
    identity = get_jwt_identity()  # Identity di sini adalah username
    if not identity:
        return None
    connection = connect_db()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, username, email, student_number, role FROM users WHERE username=%s", (identity,))
            user = cursor.fetchone()
        return user
    except Exception:
        return None
    finally:
        connection.close()

# Update profile
@app.route('/api/update_profile', methods=['PUT'])
@jwt_required()
def update_profile():
    # Get current user details
    current_user = get_current_user()
    role = current_user['role']
    
    # Data yang dikirimkan oleh client
    data = request.get_json()
    
    # Validasi data berdasarkan role
    required_fields = {
        'siswa': ['class', 'grade'],
        'guru': ['subject', 'qualification'],
        'orang_tua': ['phone_number', 'address', 'student_id']
    }
    
    if role not in required_fields:
        return jsonify({"status": "error", "message": "Invalid role"}), 400
    
    missing_fields = [field for field in required_fields[role] if field not in data]
    if missing_fields:
        return jsonify({
            "status": "error",
            "message": f"Missing required fields: {', '.join(missing_fields)}"
        }), 422
    
    # Koneksi ke database
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            if role == 'siswa':
                cursor.execute("""
                    UPDATE siswa SET class=%s, grade=%s WHERE user_id=%s
                """, (data.get('class'), data.get('grade'), current_user['id']))
            elif role == 'guru':
                cursor.execute("""
                    UPDATE guru SET subject=%s, qualification=%s WHERE user_id=%s
                """, (data.get('subject'), data.get('qualification'), current_user['id']))
            elif role == 'orang_tua':
                cursor.execute("""
                    UPDATE orang_tua SET phone_number=%s, address=%s, student_id=%s WHERE user_id=%s
                """, (data.get('phone_number'), data.get('address'), data.get('student_id'), current_user['id']))
        
        # Simpan perubahan ke database
        connection.commit()
        return jsonify({"status": "success", "message": "Profile updated successfully"}), 200
    except Exception as e:
        connection.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        connection.close()


@app.route('/api/get_profile', methods=['GET'])
@jwt_required()
def get_profile():
    # Dapatkan data pengguna saat ini
    current_user = get_current_user()
    
    if not current_user:
        return jsonify({"status": "error", "message": "User not authenticated"}), 401
    
    user_id = current_user['id']
    role = current_user['role']

    connection = connect_db()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Ambil data spesifik berdasarkan role
            if role == 'siswa':
                cursor.execute("SELECT class, grade FROM siswa WHERE user_id=%s", (user_id,))
                specific_data = cursor.fetchone()
            elif role == 'guru':
                cursor.execute("SELECT subject, qualification FROM guru WHERE user_id=%s", (user_id,))
                specific_data = cursor.fetchone()
            else:
                return jsonify({"status": "error", "message": "Invalid role"}), 400

            # Gabungkan data umum dan spesifik
            profile_data = {**current_user, **(specific_data or {})}
            return jsonify({"status": "success", "data": profile_data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        connection.close()

@app.route('/api/student-recap', methods=['GET'])
@jwt_required()
def get_student_recap_status():
    """Mengambil status rekap siswa berdasarkan token pengguna."""
    current_user = get_current_user()  # Mengambil pengguna saat ini dari token
    if not current_user:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    student_name = current_user['username']
    target_date = request.args.get('date')

    connection = connect_db()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            if target_date:
                try:
                    datetime.strptime(target_date, '%Y-%m-%d')
                except ValueError:
                    return jsonify({"status": "error", "message": "Invalid date format. Use YYYY-MM-DD"}), 400

                query = """
                    SELECT a.student_id, u.username, a.status_absen, a.status_mood, a.status_dasi, a.image_url, a.date
                    FROM attendance a
                    JOIN siswa s ON a.student_id = s.id
                    JOIN users u ON s.user_id = u.id
                    WHERE u.username = %s AND DATE(a.date) = %s
                    ORDER BY a.date DESC LIMIT 1
                """
                cursor.execute(query, (student_name, target_date))
            else:
                query = """
                    SELECT a.student_id, u.username, a.status_absen, a.status_mood, a.status_dasi, a.image_url, a.date
                    FROM attendance a
                    JOIN siswa s ON a.student_id = s.id
                    JOIN users u ON s.user_id = u.id
                    WHERE u.username = %s
                    ORDER BY a.date DESC LIMIT 1
                """
                cursor.execute(query, (student_name,))

            record = cursor.fetchone()
            if record:
                return jsonify({
                    "status": "success",
                    "recap_data": {
                        "student_id": record['student_id'],
                        "username": record['username'],
                        "attendance_status": record['status_absen'] or "Unknown",
                        "mood_status": record['status_mood'] or "Unknown",
                        "tie_status": record['status_dasi'] or "Unknown",
                        "image_url": record['image_url'] or "No Image Available",
                        "date": record['date'].strftime('%Y-%m-%d %H:%M:%S')
                    }
                }), 200
            else:
                return jsonify({"status": "error", "message": "No record found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        connection.close()


@app.route('/api/student-recap/attendance-status', methods=['GET'])
@jwt_required()
def get_student_attendance_status():
    current_user = get_current_user()  # Mengambil pengguna saat ini dari token
    if not current_user:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    student_name = current_user['username']  # Mengambil name dari current_user
    target_date = request.args.get('date')  # Optional parameter date

    # Koneksi ke database
    connection = connect_db()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            if target_date:
                # Validasi format tanggal
                try:
                    datetime.strptime(target_date, '%Y-%m-%d')
                except ValueError:
                    return jsonify({
                        "status": "error",
                        "message": "Invalid date format. Use YYYY-MM-DD"
                    }), 400

                # Query berdasarkan nama siswa dan tanggal
                cursor.execute("""
                    SELECT a.student_id, u.username, a.status_absen, a.image_url, a.date
                    FROM attendance a
                    JOIN siswa s ON a.student_id = s.id
                    JOIN users u ON s.user_id = u.id
                    WHERE u.username = %s AND DATE(a.date) = %s
                    ORDER BY a.date DESC LIMIT 1
                """, (student_name, target_date))
            else:
                # Query jika tidak ada tanggal, ambil data terbaru
                cursor.execute("""
                    SELECT a.student_id, u.username, a.status_absen, a.image_url, a.date
                    FROM attendance a
                    JOIN siswa s ON a.student_id = s.id
                    JOIN users u ON s.user_id = u.id
                    WHERE u.username = %s
                    ORDER BY a.date DESC LIMIT 1
                """, (student_name,))

            record = cursor.fetchone()

            if record:
                return jsonify({
                    "status": "success",
                    "attendance_data": {
                        "student_id": record['student_id'],
                        "username": record['username'],
                        "status_absen": record['status_absen'],
                        "image_url": record['image_url'] if record['image_url'] else "No Image Available",
                        "date": record['date'].strftime('%Y-%m-%d %H:%M:%S')
                    }
                }), 200
            else:
                return jsonify({
                    "status": "error",
                    "message": "No attendance record found"
                }), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        connection.close()


@app.route('/api/student-recap/mood-status', methods=['GET'])
@jwt_required()
def get_student_mood_status():
    current_user = get_current_user()  # Mengambil pengguna saat ini dari token
    if not current_user:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    student_name = current_user['username']  # Mengambil name dari current_user
    target_date = request.args.get('date')  # Optional parameter date

    # Koneksi ke database
    connection = connect_db()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            if target_date:
                # Validasi format tanggal
                try:
                    datetime.strptime(target_date, '%Y-%m-%d')
                except ValueError:
                    return jsonify({
                        "status": "error",
                        "message": "Invalid date format. Use YYYY-MM-DD"
                    }), 400

                # Query berdasarkan nama siswa dan tanggal
                cursor.execute("""
                    SELECT a.student_id, u.username, a.status_mood, a.image_url, a.date
                    FROM attendance a
                    JOIN siswa s ON a.student_id = s.id
                    JOIN users u ON s.user_id = u.id
                    WHERE u.username = %s AND DATE(a.date) = %s
                    ORDER BY a.date DESC LIMIT 1
                """, (student_name, target_date))
            else:
                # Query jika tidak ada tanggal, ambil data terbaru
                cursor.execute("""
                    SELECT a.student_id, u.username, a.status_mood, a.image_url, a.date
                    FROM attendance a
                    JOIN siswa s ON a.student_id = s.id
                    JOIN users u ON s.user_id = u.id
                    WHERE u.username = %s
                    ORDER BY a.date DESC LIMIT 1
                """, (student_name,))

            record = cursor.fetchone()

            if record:
                return jsonify({
                    "status": "success",
                    "mood_data": {
                        "student_id": record['student_id'],
                        "username": record['username'],
                        "status_mood": record['status_mood'] if record['status_mood'] else "Unknown",
                        "image_url": record['image_url'] if record['image_url'] else "No Image Available",
                        "date": record['date'].strftime('%Y-%m-%d %H:%M:%S')
                    }
                }), 200
            else:
                return jsonify({
                    "status": "error",
                    "message": "No mood record found"
                }), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        connection.close()


@app.route('/api/student-recap/tie-status', methods=['GET'])
@jwt_required()
def get_student_tie_status():
    current_user = get_current_user()  # Mengambil pengguna saat ini dari token
    if not current_user:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    student_name = current_user['username']  # Mengambil name dari current_user
    target_date = request.args.get('date')  # Optional parameter date

    # Koneksi ke database
    connection = connect_db()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            if target_date:
                # Validasi format tanggal
                try:
                    datetime.strptime(target_date, '%Y-%m-%d')
                except ValueError:
                    return jsonify({
                        "status": "error",
                        "message": "Invalid date format. Use YYYY-MM-DD"
                    }), 400

                # Query berdasarkan nama siswa dan tanggal
                cursor.execute("""
                    SELECT a.student_id, u.username, a.status_dasi, a.image_url, a.date
                    FROM attendance a
                    JOIN siswa s ON a.student_id = s.id
                    JOIN users u ON s.user_id = u.id
                    WHERE u.username = %s AND DATE(a.date) = %s
                    ORDER BY a.date DESC LIMIT 1
                """, (student_name, target_date))
            else:
                # Query jika tidak ada tanggal, ambil data terbaru
                cursor.execute("""
                    SELECT a.student_id, u.username, a.status_dasi, a.image_url, a.date
                    FROM attendance a
                    JOIN siswa s ON a.student_id = s.id
                    JOIN users u ON s.user_id = u.id
                    WHERE u.username = %s
                    ORDER BY a.date DESC LIMIT 1
                """, (student_name,))

            record = cursor.fetchone()

            if record:
                return jsonify({
                    "status": "success",
                    "tie_data": {
                        "student_id": record['student_id'],
                        "username": record['username'],
                        "status_dasi": record['status_dasi'] if record['status_dasi'] else "Unknown",
                        "image_url": record['image_url'] if record['image_url'] else "No Image Available",
                        "date": record['date'].strftime('%Y-%m-%d %H:%M:%S')
                    }
                }), 200
            else:
                return jsonify({
                    "status": "error",
                    "message": "No tie record found"
                }), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        connection.close()


@app.route('/api/teacher-recap', methods=['GET'])
@jwt_required()
def get_attendance_by_date_or_all():
    # Check if user is authenticated and is a guru
    current_user = get_current_user()  # Mengambil pengguna saat ini dari token
    if not current_user:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # Ambil parameter tanggal dari query string
    target_date = request.args.get('date')

    # Koneksi ke database
    connection = connect_db()
    debug_info = {}
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            if target_date:
                try:
                    # Validasi format tanggal
                    datetime.strptime(target_date, '%Y-%m-%d')
                except ValueError:
                    return jsonify({
                        "status": "error",
                        "message": "Invalid date format. Use YYYY-MM-DD"
                    }), 400

                # Query berdasarkan tanggal tertentu
                cursor.execute("""
                    SELECT a.student_id, u.username, a.status_absen, a.status_mood, a.status_dasi, a.image_url, a.date
                    FROM attendance a
                    JOIN siswa s ON a.student_id = s.id
                    JOIN users u ON s.user_id = u.id
                    WHERE DATE(a.date) = %s
                    ORDER BY a.date DESC
                """, (target_date,))
            else:
                # Query untuk seluruh data
                cursor.execute("""
                    SELECT a.student_id, u.username, a.status_absen, a.status_mood, a.status_dasi, a.image_url, a.date
                    FROM attendance a
                    JOIN siswa s ON a.student_id = s.id
                    JOIN users u ON s.user_id = u.id
                    ORDER BY a.date DESC
                """)

            # Ambil hasil query
            attendance_data = cursor.fetchall()

            # Debug info
            debug_info = {
                "queried_date": target_date if target_date else "All dates",
                "total_records": len(attendance_data)
            }

            # Jika tidak ada data
            if not attendance_data:
                return jsonify({
                    "status": "success",
                    "message": "No attendance records found.",
                    "debug_info": debug_info
                }), 200

            # Proses hasil query menjadi list of dictionaries
            attendance_list = [
                {
                    "student_id": record['student_id'],
                    "username": record['username'],
                    "status_absen": record['status_absen'],
                    "status_mood": record['status_mood'] if record['status_mood'] else "Unknown",
                    "status_dasi": record['status_dasi'] if record['status_dasi'] else "Unknown",
                    "image_url": record['image_url'] if record['image_url'] else "No Image Available",
                    "date": record['date'].strftime('%Y-%m-%d %H:%M:%S')
                }
                for record in attendance_data
            ]

            return jsonify({
                "status": "success",
                "attendance_data": attendance_list,
                "debug_info": debug_info
            }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "debug_info": debug_info
        }), 500
    finally:
        connection.close()

@app.route('/api/attendance-status', methods=['GET'])
@jwt_required()
def get_attendance_status():
    # Check if user is authenticated and is a guru
    current_user = get_current_user()  # Mengambil pengguna saat ini dari token
    if not current_user:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # Ambil parameter tanggal dari query string
    target_date = request.args.get('date')

    # Koneksi ke database
    connection = connect_db()
    debug_info = {}
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            if target_date:
                try:
                    # Validasi format tanggal
                    datetime.strptime(target_date, '%Y-%m-%d')
                except ValueError:
                    return jsonify({
                        "status": "error",
                        "message": "Invalid date format. Use YYYY-MM-DD"
                    }), 400

                # Query berdasarkan tanggal tertentu
                cursor.execute("""
                    SELECT a.student_id, u.username, a.status_absen, a.image_url, a.date
                    FROM attendance a
                    JOIN siswa s ON a.student_id = s.id
                    JOIN users u ON s.user_id = u.id
                    WHERE DATE(a.date) = %s
                    ORDER BY a.date DESC
                """, (target_date,))
            else:
                # Query untuk seluruh data
                cursor.execute("""
                    SELECT a.student_id, u.username, a.status_absen, a.image_url, a.date
                    FROM attendance a
                    JOIN siswa s ON a.student_id = s.id
                    JOIN users u ON s.user_id = u.id
                    ORDER BY a.date DESC
                """)

            # Ambil hasil query
            attendance_data = cursor.fetchall()

            # Debug info
            debug_info = {
                "queried_date": target_date if target_date else "All dates",
                "total_records": len(attendance_data)
            }

            # Jika tidak ada data
            if not attendance_data:
                return jsonify({
                    "status": "success",
                    "message": "No attendance records found.",
                    "debug_info": debug_info
                }), 200

            # Proses hasil query menjadi list of dictionaries
            attendance_list = [
                {
                    "student_id": record['student_id'],
                    "username": record['username'],
                    "status_absen": record['status_absen'],
                    "image_url": record['image_url'] if record['image_url'] else "No Image Available",
                    "date": record['date'].strftime('%Y-%m-%d %H:%M:%S')
                }
                for record in attendance_data
            ]

            return jsonify({
                "status": "success",
                "attendance_status_data": attendance_list,
                "debug_info": debug_info
            }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "debug_info": debug_info
        }), 500
    finally:
        connection.close()

@app.route('/api/mood-status', methods=['GET'])
@jwt_required()
def get_mood_status():
    # Check if user is authenticated and is a guru
    current_user = get_current_user()  # Mengambil pengguna saat ini dari token
    if not current_user:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # Ambil parameter tanggal dari query string
    target_date = request.args.get('date')

    # Koneksi ke database
    connection = connect_db()
    debug_info = {}
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            if target_date:
                try:
                    # Validasi format tanggal
                    datetime.strptime(target_date, '%Y-%m-%d')
                except ValueError:
                    return jsonify({
                        "status": "error",
                        "message": "Invalid date format. Use YYYY-MM-DD"
                    }), 400

                # Query berdasarkan tanggal tertentu
                cursor.execute("""
                    SELECT a.student_id, u.username, a.status_mood, a.image_url, a.date
                    FROM attendance a
                    JOIN siswa s ON a.student_id = s.id
                    JOIN users u ON s.user_id = u.id
                    WHERE DATE(a.date) = %s
                    ORDER BY a.date DESC
                """, (target_date,))
            else:
                # Query untuk seluruh data
                cursor.execute("""
                    SELECT a.student_id, u.username, a.status_mood, a.image_url, a.date
                    FROM attendance a
                    JOIN siswa s ON a.student_id = s.id
                    JOIN users u ON s.user_id = u.id
                    ORDER BY a.date DESC
                """)

            # Ambil hasil query
            mood_data = cursor.fetchall()

            # Debug info
            debug_info = {
                "queried_date": target_date if target_date else "All dates",
                "total_records": len(mood_data)
            }

            # Jika tidak ada data
            if not mood_data:
                return jsonify({
                    "status": "success",
                    "message": "No mood records found.",
                    "debug_info": debug_info
                }), 200

            # Proses hasil query menjadi list of dictionaries
            mood_list = [
                {
                    "student_id": record['student_id'],
                    "username": record['username'],
                    "status_mood": record['status_mood'] if record['status_mood'] else "Unknown",
                    "image_url": record['image_url'] if record['image_url'] else "No Image Available",
                    "date": record['date'].strftime('%Y-%m-%d %H:%M:%S')
                }
                for record in mood_data
            ]

            return jsonify({
                "status": "success",
                "mood_status_data": mood_list,
                "debug_info": debug_info
            }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "debug_info": debug_info
        }), 500
    finally:
        connection.close()

@app.route('/api/tie-status', methods=['GET'])
@jwt_required()
def get_tie_status():
    # Check if user is authenticated and is a guru
    current_user = get_current_user()  # Mengambil pengguna saat ini dari token
    if not current_user:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # Ambil parameter tanggal dari query string
    target_date = request.args.get('date')

    # Koneksi ke database
    connection = connect_db()
    debug_info = {}
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            if target_date:
                try:
                    # Validasi format tanggal
                    datetime.strptime(target_date, '%Y-%m-%d')
                except ValueError:
                    return jsonify({
                        "status": "error",
                        "message": "Invalid date format. Use YYYY-MM-DD"
                    }), 400

                # Query berdasarkan tanggal tertentu
                cursor.execute("""
                    SELECT a.student_id, u.username, a.status_dasi, a.image_url, a.date
                    FROM attendance a
                    JOIN siswa s ON a.student_id = s.id
                    JOIN users u ON s.user_id = u.id
                    WHERE DATE(a.date) = %s
                    ORDER BY a.date DESC
                """, (target_date,))
            else:
                # Query untuk seluruh data
                cursor.execute("""
                    SELECT a.student_id, u.username, a.status_dasi, a.image_url, a.date
                    FROM attendance a
                    JOIN siswa s ON a.student_id = s.id
                    JOIN users u ON s.user_id = u.id
                    ORDER BY a.date DESC
                """)

            # Ambil hasil query
            tie_data = cursor.fetchall()

            # Debug info
            debug_info = {
                "queried_date": target_date if target_date else "All dates",
                "total_records": len(tie_data)
            }

            # Jika tidak ada data
            if not tie_data:
                return jsonify({
                    "status": "success",
                    "message": "No tie status records found.",
                    "debug_info": debug_info
                }), 200

            # Proses hasil query menjadi list of dictionaries
            tie_list = [
                {
                    "student_id": record['student_id'],
                    "username": record['username'],
                    "status_dasi": record['status_dasi'] if record['status_dasi'] else "Unknown",
                    "image_url": record['image_url'] if record['image_url'] else "No Image Available",
                    "date": record['date'].strftime('%Y-%m-%d %H:%M:%S')
                }
                for record in tie_data
            ]

            return jsonify({
                "status": "success",
                "tie_status_data": tie_list,
                "debug_info": debug_info
            }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "debug_info": debug_info
        }), 500
    finally:
        connection.close()

@app.route('/storage/attendance_images/<filename>')
def serve_image(filename):
    """
    Endpoint untuk melayani gambar secara publik
    """
    return send_from_directory(IMAGE_UPLOAD_DIR, filename)

@app.route('/api/predict-all', methods=['POST'])
@jwt_required()
def predict_all():
    # Check if user is authenticated and is a guru
    current_user = get_current_user()  # Mengambil pengguna saat ini dari token
    if not current_user:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # Periksa file dalam request
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "File not found"}), 400

    file = request.files['file']
    
    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename)
    temp_path = os.path.join("temp", unique_filename)
    os.makedirs("temp", exist_ok=True)
    file.save(temp_path)

    connection = None  # Inisialisasi koneksi database
    try:
        # Preprocess untuk masing-masing model
        results = {}
        connection = connect_db()  # Koneksi ke database

        # --- Predict Absen ---
        try:
            # Pindahkan file ke direktori penyimpanan
            storage_path = os.path.join(IMAGE_UPLOAD_DIR, unique_filename)
            shutil.move(temp_path, storage_path)
            
            # Buat URL publik untuk gambar
            public_image_url = f"{IMAGE_PUBLIC_URL_BASE}{unique_filename}"

            img_absen = image.load_img(storage_path, target_size=(224, 224))
            img_array_absen = image.img_to_array(img_absen)
            img_array_absen = np.expand_dims(img_array_absen, axis=0) / 255.0

            prediction_absen = model_absen.predict(img_array_absen)
            predicted_index_absen = np.argmax(prediction_absen)
            predicted_label_absen = class_labels[predicted_index_absen]
            confidence_absen = float(prediction_absen[0][predicted_index_absen])

            # Simpan hasil prediksi absen ke database
            with connection.cursor() as cursor:
                send_message = []
                attendance_count = 0

                # Ambil data siswa berdasarkan prediksi nama
                cursor.execute("""
                    SELECT s.id, u.username 
                    FROM siswa s
                    JOIN users u ON s.user_id = u.id
                    WHERE LOWER(u.username) LIKE %s
                """, (f"%{predicted_label_absen.lower()}%",))
                
                matching_student = cursor.fetchone()

                if matching_student:
                    timezone = pytz.timezone("Asia/Jakarta")
                    current_time_wib = datetime.now(timezone)
                    current_date = current_time_wib.date()
                    current_time = current_time_wib.time()

                    student_id, student_name = matching_student[0], matching_student[1]

                    # Hitung status_absen dan poin
                    cutoff_time = datetime.strptime('08:00', '%H:%M').time()
                    status_absen = 'Hadir' if current_time <= cutoff_time else 'Terlambat'
                    point_absen = 10 if status_absen == 'Hadir' else 0

                    # --- Predict Dasi ---
                    img_dasi = image.load_img(storage_path, target_size=(100, 100))
                    img_array_dasi = image.img_to_array(img_dasi)
                    img_array_dasi = np.expand_dims(img_array_dasi, axis=0) / 255.0

                    prediction_dasi = model_dasi.predict(img_array_dasi)
                    predicted_class_dasi = "Tidak Ada Dasi" if prediction_dasi[0] > 0.5 else "Ada Dasi"
                    confidence_dasi = float(prediction_dasi[0]) if predicted_class_dasi == "Tidak Ada Dasi" else float(1 - prediction_dasi[0])

                    # Status dasi dan poin dasi
                    status_dasi = predicted_class_dasi
                    point_dasi = 10 if status_dasi == "Ada Dasi" else 0

                    # Total poin hari ini
                    total_point = point_absen + point_dasi

                    # --- Predict Mood ---
                    img_mood = Image.open(storage_path).convert('L').resize((100, 100))
                    img_array_mood = np.expand_dims(np.array(img_mood) / 255.0, axis=(0, -1))

                    prediction_mood = model_mood.predict(img_array_mood)
                    probabilities_mood = prediction_mood[0]
                    predicted_index_mood = np.argmax(probabilities_mood)
                    predicted_class_mood = class_names[predicted_index_mood]
                    confidence_mood = np.max(probabilities_mood)

                    status_mood = predicted_class_mood  # This line ensures that 'status_mood' is defined

                    # Periksa kehadiran terakhir siswa
                    cursor.execute("""
                        SELECT id, DATE(date) as attendance_date, semester_total_point
                        FROM attendance
                        WHERE student_id = %s
                        ORDER BY date DESC
                        LIMIT 1
                    """, (student_id,))

                    last_attendance = cursor.fetchone()

                    if last_attendance and last_attendance[1] == current_date:
                        # Update kehadiran jika di hari yang sama
                        cursor.execute("""
                            UPDATE attendance
                            SET status_absen = %s, status_mood = %s, status_dasi = %s, point = %s, 
                                semester_total_point = semester_total_point + %s, 
                                date = %s, image_url = %s
                            WHERE id = %s
                        """, (status_absen, status_mood, status_dasi, total_point, total_point, current_time_wib, public_image_url, last_attendance[0]))
                    else:
                        # Insert baru jika hari berbeda
                        semester_total_point = last_attendance[2] + total_point if last_attendance else total_point
                        cursor.execute("""
                            INSERT INTO attendance (student_id, status_absen, status_mood, status_dasi, point, semester_total_point, date, image_url) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (student_id, status_absen, status_mood, status_dasi, total_point, semester_total_point, current_time_wib, public_image_url))
                        attendance_count += 1

                    # Update pesan terakhir orang tua
                    message = f"Siswa {student_name.title()} {status_absen} dan ({status_dasi}) pada {current_time_wib.strftime('%Y-%m-%d %H:%M:%S %z')}."
                    cursor.execute("""
                        UPDATE orang_tua 
                        SET last_message = %s 
                        WHERE student_id = %s
                    """, (message, student_id))
                    send_message.append(message)

                    results["predict_absen"] = {
                        "predicted_name": predicted_label_absen,
                        "confidence": confidence_absen,
                        "send_message": send_message,
                        "datetime": current_time_wib.strftime('%Y-%m-%d %H:%M:%S %z'),
                        "status_absen": status_absen,
                        "attendance_count": attendance_count,
                        "image_url": public_image_url
                    }

                    results["predict_dasi"] = {
                        "predicted_class": predicted_class_dasi,
                        "confidence": confidence_dasi
                    }

                    results["predict_mood"] = {
                        "predicted_class_name": predicted_class_mood,
                        "confidence": float(confidence_mood),
                        "class_probabilities": {
                            class_names[i]: float(probabilities_mood[i])
                            for i in range(len(class_names))
                        }
                    }

        except Exception as e:
            results["predict_absen"] = {"error": str(e)}
            results["predict_dasi"] = {"error": str(e)}
            results["predict_mood"] = {"error": str(e)}

        # Commit database setelah semua selesai
        connection.commit()

        return jsonify({"status": "success", "results": results}), 200
    except Exception as e:
        if connection:
            connection.rollback()  # Rollback jika terjadi error
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if connection:
            connection.close()  # Tutup koneksi database
        # Tidak perlu hapus file karena sudah dipindahkan ke storage

def generate_unique_filename(original_filename):
    """
    Generate unique filename dengan format: 
    {uuid}_{original_filename}
    """
    ext = os.path.splitext(original_filename)[1]
    unique_filename = f"{uuid.uuid4()}{ext}"
    return unique_filename


@app.route('/api/leaderboard', methods=['GET'])
@jwt_required()
def leaderboard():
    current_user = get_current_user()  # Mengambil pengguna saat ini dari token
    if not current_user:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # Dapatkan parameter untuk sorting
    sort_order = request.args.get('sort_order', 'desc')  # Default 'desc' (dari terbesar ke terkecil)
    if sort_order not in ['asc', 'desc']:
        return jsonify({"status": "error", "message": "Invalid sort_order. Choose 'asc' or 'desc'."}), 400

    connection = None
    try:
        connection = connect_db()

        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Query untuk mendapatkan leaderboard berdasarkan semester_total_point
            query = """
                SELECT s.id AS student_id, u.username AS student_name, a.semester_total_point, a.image_url
                FROM siswa s
                JOIN users u ON s.user_id = u.id
                JOIN attendance a ON s.id = a.student_id
                WHERE DATE(a.date) = CURRENT_DATE
                ORDER BY a.semester_total_point {}
            """.format("DESC" if sort_order == "desc" else "ASC")

            cursor.execute(query)
            leaderboard_data = cursor.fetchall()

            if not leaderboard_data:
                return jsonify({"status": "error", "message": "No attendance data for today."}), 404

            # Bangun data leaderboard
            leaderboard = [
                {
                    "student_id": row["student_id"],
                    "student_name": row["student_name"],
                    "semester_total_point": row["semester_total_point"],
                    "image_url": row["image_url"]
                }
                for row in leaderboard_data
            ]

        return jsonify({"status": "success", "leaderboard": leaderboard}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    app.run(debug=True)