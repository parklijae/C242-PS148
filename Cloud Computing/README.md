Dokumentasi API's

Endpoint Register Metode POST: https://checkmate-506488875993.asia-southeast2.run.app/api/register
Request Body:
{
  "username": "zain",
  "email": "zain@gmail.com",
  "student_number": "",
  "password": "password123",
  "role": "siswa"
}
Response:
201 Created
{
  "status": "success",
  "message": "User registered successfully"
}
400 Bad Request
{
  "status": "error",
  "message": "Email already exists"
}
500 Internal Server Error
{
  "status": "error",
  "message": "<Error message>"
}

Endpoint Login Metode POST: https://checkmate-506488875993.asia-southeast2.run.app/api/login
Headers
![bearer](https://github.com/user-attachments/assets/0fe08654-5ef0-4605-956c-a198e7a259c8)

Request Body:
{
  "email": "zain",
  "password": "password123"
}


Respons 201 Create:
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTczMzgzNjQzOCwianRpIjoiNDNhMzA4ZTYtNmIyZS00MWQ2LWE0NTAtODUyZWVkMmM0MmVhIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6InphaW4iLCJuYmYiOjE3MzM4MzY0MzgsImNzcmYiOiJkYjRkYzAzNC1iMDMzLTQ4ZmYtYWViZi0wOWJmMWNlZWFmMzgiLCJleHAiOjE3MzM4NDM2Mzh9.0OXNrJbzKcLRqHBJRnwVRVH91PCjjUNd9UKuj9_B9m4",
    "message": "Login successful",
    "status": "success",
    "user": {
        "email": "zain@gmail.com",
        "role": "siswa",
        "student_number": null,
        "username": "zain"
    }
}
Response
200 OK
{
  "status": "success",
  "message": "Login successful",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTczMzgzNjQzOCwianRpIjoiNDNhMzA4ZTYtNmIyZS00MWQ2LWE0NTAtODUyZWVkMmM0MmVhIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6InphaW4iLCJuYmYiOjE3MzM4MzY0MzgsImNzcmYiOiJkYjRkYzAzNC1iMDMzLTQ4ZmYtYWViZi0wOWJmMWNlZWFmMzgiLCJleHAiOjE3MzM4NDM2Mzh9.0OXNrJbzKcLRqHBJRnwVRVH91PCjjUNd9UKuj9_B9m4",
  "user": {
    "email": "<email>",
    "username": "<username>",
    "student_number": "<student_number>",
    "role": "<role>"
  }
}


401 Unauthorized
{
  "status": "error",
  "message": "Invalid credentials"
}


500 Internal Server Error
{
  "status": "error",
  "message": "<Error message>"
}



Endpoint Update Profile Metode PUT: https://checkmate-506488875993.asia-southeast2.run.app/api/update_profile
Headers:
![bearer](https://github.com/user-attachments/assets/d0e272c4-9a6f-4f87-915e-056cadec2197)

Request: 
![request](https://github.com/user-attachments/assets/56b1b9db-29e2-4d83-99b0-83bc179ac3eb)


Response
200 OK
{
  "status": "success",
  "message": "Profile updated successfully"
}
422 Unprocessable Entity
{
  "status": "error",
  "message": "Missing required fields: <field_name>"
}


500 Internal Server Error
{
  "status": "error",
  "message": "<Error message>"
}


Endpoint Get Profile Metode GET: https://checkmate-506488875993.asia-southeast2.run.app/api/get_profile
Headers:
![bearer](https://github.com/user-attachments/assets/5a7847be-8a3f-41c4-80b7-7e0d38457c61)


Response
200 OK
{
  "status": "success",
  "data": {
    "id": "<user_id>",
    "username": "<username>",
    "email": "<email>",
    "student_number": "<student_number>",
    "role": "<role>",
    "class": "<class>",
    "grade": "<grade>"
  }
}


401 Unauthorized
{
  "status": "error",
  "message": "User not authenticated"
}


500 Internal Server Error
{
  "status": "error",
  "message": "<Error message>"
}

Page Siswa
Endpoint Leaderboard Tertinggi GET: (hanya siswa yang bisa) https://checkmate-506488875993.asia-southeast2.run.app/api/leaderboard
Headers:
![bearer](https://github.com/user-attachments/assets/92f64f06-3117-412e-8ce7-16f709db5108)

Response:
{
    "leaderboard": [
        {
            "image_url": "https://checkmate-506488875993.asia-southeast2.run.app/storage/attendance_images/210e96a4-2ae6-42bf-b7a5-6628568f18d9.jpg",
            "semester_total_point": 10,
            "student_id": 3,
            "student_name": "liza"
        },
        {
            "image_url": "https://checkmate-506488875993.asia-southeast2.run.app/storage/attendance_images/08bdd73a-0ba2-4638-af28-4d7f99233095.jpg",
            "semester_total_point": 0,
            "student_id": 5,
            "student_name": "zain"
        },
        {
            "image_url": "https://checkmate-506488875993.asia-southeast2.run.app/storage/attendance_images/9d6ea3df-6a0f-4a53-ae82-b188ab91f748.jpg",
            "semester_total_point": 0,
            "student_id": 4,
            "student_name": "nabila"
        }
    ],
    "status": "success"
}


Endpoint Leaderboard Terendah GET: (hanya siswa yang bisa) https://checkmate-506488875993.asia-southeast2.run.app/api/leaderboard?sort_order=asc
Headers:
![bearer](https://github.com/user-attachments/assets/f6df71d0-64b7-4593-94c5-5a55f8096a94)

Response:
{
    "leaderboard": [
        {
            "image_url": "https://checkmate-506488875993.asia-southeast2.run.app/storage/attendance_images/08bdd73a-0ba2-4638-af28-4d7f99233095.jpg",
            "semester_total_point": 0,
            "student_id": 5,
            "student_name": "zain"
        },
        {
            "image_url": "https://checkmate-506488875993.asia-southeast2.run.app/storage/attendance_images/9d6ea3df-6a0f-4a53-ae82-b188ab91f748.jpg",
            "semester_total_point": 0,
            "student_id": 4,
            "student_name": "nabila"
        },
        {
            "image_url": "https://checkmate-506488875993.asia-southeast2.run.app/storage/attendance_images/210e96a4-2ae6-42bf-b7a5-6628568f18d9.jpg",
            "semester_total_point": 10,
            "student_id": 3,
            "student_name": "liza"
        }
    ],
    "status": "success"
}

Endpoint Student Recap all model per tanggal GET: (hanya siswa yang bisa & siapa yang login) https://checkmate-506488875993.asia-southeast2.run.app/api/student-recap?date=2024-12-10
Headers:
![bearer](https://github.com/user-attachments/assets/c75054d8-f355-45f0-a989-4d29b2735469)

Response:
{
    "recap_data": {
        "attendance_status": "Terlambat",
        "date": "2024-12-10 14:35:10",
        "image_url": "https://checkmate-506488875993.asia-southeast2.run.app/storage/attendance_images/08bdd73a-0ba2-4638-af28-4d7f99233095.jpg",
        "mood_status": "sad",
        "student_id": 5,
        "tie_status": "Tidak Ada Dasi",
        "username": "zain"
    },
    "status": "success"
}

Endpoint Student Recap Model Absen per tanggal GET: (hanya siswa yang bisa & siapa yang login) https://checkmate-506488875993.asia-southeast2.run.app/api/student-recap/attendance-status?date=2024-12-10
Headers:
![bearer](https://github.com/user-attachments/assets/24856361-9ae0-4f4a-b783-00d2805ae179)

Response:
{
    "attendance_data": {
        "date": "2024-12-10 14:35:10",
        "image_url": "https://checkmate-506488875993.asia-southeast2.run.app/storage/attendance_images/08bdd73a-0ba2-4638-af28-4d7f99233095.jpg",
        "status_absen": "Terlambat",
        "student_id": 5,
        "username": "zain"
    },
    "status": "success"
}

Endpoint Student Recap Model Mood per tanggal GET: (hanya siswa yang bisa & siapa yang login) https://checkmate-506488875993.asia-southeast2.run.app/api/student-recap/mood-status?date=2024-12-10
Headers:
![bearer](https://github.com/user-attachments/assets/5c85b2d9-1bd7-4223-81f7-386dcac193d5)

Response:
{
    "mood_data": {
        "date": "2024-12-10 14:35:10",
        "image_url": "https://checkmate-506488875993.asia-southeast2.run.app/storage/attendance_images/08bdd73a-0ba2-4638-af28-4d7f99233095.jpg",
        "status_mood": "sad",
        "student_id": 5,
        "username": "zain"
    },
    "status": "success"
}

Endpoint Student Recap Model Atribut per tanggal GET: (hanya siswa yang bisa & siapa yang login) https://checkmate-506488875993.asia-southeast2.run.app/api/student-recap/tie-status?date=2024-12-10
Headers:
![bearer](https://github.com/user-attachments/assets/3150239c-0d8e-4db6-a4fb-943a5360ed36)

Response:
{
    "status": "success",
    "tie_data": {
        "date": "2024-12-10 14:35:10",
        "image_url": "https://checkmate-506488875993.asia-southeast2.run.app/storage/attendance_images/08bdd73a-0ba2-4638-af28-4d7f99233095.jpg",
        "status_dasi": "Tidak Ada Dasi",
        "student_id": 5,
        "username": "zain"
    }
}

Page Guru
Endpoint Guru Recap Absen Siswa GET: (hanya guru yang bisa) 
https://checkmate-506488875993.asia-southeast2.run.app/api/attendance-status
Headers:
![bearer](https://github.com/user-attachments/assets/a7e94293-fe86-4431-9718-43bdc38be077)

Response:
{
    "attendance_status_data": [
        {
            "date": "2024-12-10 20:55:43",
            "image_url": "https://checkmate-506488875993.asia-southeast2.run.app/storage/attendance_images/07180d83-0aab-4468-969b-c28823484640.jpg",
            "status_absen": "Terlambat",
            "student_id": 4,
            "username": "nabila"
        },
        {
            "date": "2024-12-10 20:55:33",
            "image_url": "https://checkmate-506488875993.asia-southeast2.run.app/storage/attendance_images/ca86eb39-9002-47c8-858e-5994d607e210.jpg",
            "status_absen": "Terlambat",
            "student_id": 5,
            "username": "zain"
        },
        {
            "date": "2024-12-10 20:55:13",
            "image_url": "https://checkmate-506488875993.asia-southeast2.run.app/storage/attendance_images/67139251-a253-4395-9997-f1faeea93e25.jpg",
            "status_absen": "Terlambat",
            "student_id": 3,
            "username": "liza"
        }
    ],
    "debug_info": {
        "queried_date": "All dates",
        "total_records": 3
    },
    "status": "success"
}

Endpoint Guru Recap Mood Siswa GET: (hanya guru yang bisa) 
https://checkmate-506488875993.asia-southeast2.run.app/api/mood-status
Headers:
![bearer](https://github.com/user-attachments/assets/a0990330-f9d9-4bda-ab1c-385db87911de)

Response:
{
    "debug_info": {
        "queried_date": "All dates",
        "total_records": 3
    },
    "mood_status_data": [
        {
            "date": "2024-12-10 20:55:43",
            "image_url": "https://checkmate-506488875993.asia-southeast2.run.app/storage/attendance_images/07180d83-0aab-4468-969b-c28823484640.jpg",
            "status_mood": "sad",
            "student_id": 4,
            "username": "nabila"
        },
        {
            "date": "2024-12-10 20:55:33",
            "image_url": "https://checkmate-506488875993.asia-southeast2.run.app/storage/attendance_images/ca86eb39-9002-47c8-858e-5994d607e210.jpg",
            "status_mood": "sad",
            "student_id": 5,
            "username": "zain"
        },
        {
            "date": "2024-12-10 20:55:13",
            "image_url": "https://checkmate-506488875993.asia-southeast2.run.app/storage/attendance_images/67139251-a253-4395-9997-f1faeea93e25.jpg",
            "status_mood": "angry",
            "student_id": 3,
            "username": "liza"
        }
    ],
    "status": "success"
}

Endpoint Guru Recap Atribut Siswa GET: (hanya guru yang bisa) 
https://checkmate-506488875993.asia-southeast2.run.app/api/tie-status
Headers:
![bearer](https://github.com/user-attachments/assets/d174ffe8-b5b5-42ac-a8ee-82549d46dfbd)

Respons:
{
    "debug_info": {
        "queried_date": "All dates",
        "total_records": 3
    },
    "status": "success",
    "tie_status_data": [
        {
            "date": "2024-12-10 20:55:43",
            "image_url": "https://checkmate-506488875993.asia-southeast2.run.app/storage/attendance_images/07180d83-0aab-4468-969b-c28823484640.jpg",
            "status_dasi": "Tidak Ada Dasi",
            "student_id": 4,
            "username": "nabila"
        },
        {
            "date": "2024-12-10 20:55:33",
            "image_url": "https://checkmate-506488875993.asia-southeast2.run.app/storage/attendance_images/ca86eb39-9002-47c8-858e-5994d607e210.jpg",
            "status_dasi": "Tidak Ada Dasi",
            "student_id": 5,
            "username": "zain"
        },
        {
            "date": "2024-12-10 20:55:13",
            "image_url": "https://checkmate-506488875993.asia-southeast2.run.app/storage/attendance_images/67139251-a253-4395-9997-f1faeea93e25.jpg",
            "status_dasi": "Tidak Ada Dasi",
            "student_id": 3,
            "username": "liza"
        }
    ]
}

Endpoint Guru Recap Seluruh Model Siswa GET: (hanya guru yang bisa) 
https://checkmate-506488875993.asia-southeast2.run.app/api/teacher-recap
Headers:
![bearer](https://github.com/user-attachments/assets/e4d743ce-38de-40c3-a1fb-37f41738fa25)

Response:
{
    "attendance_data": [
        {
            "date": "2024-12-10 20:55:43",
            "image_url": "https://checkmate-506488875993.asia-southeast2.run.app/storage/attendance_images/07180d83-0aab-4468-969b-c28823484640.jpg",
            "status_absen": "Terlambat",
            "status_dasi": "Tidak Ada Dasi",
            "status_mood": "sad",
            "student_id": 4,
            "username": "nabila"
        },
        {
            "date": "2024-12-10 20:55:33",
            "image_url": "https://checkmate-506488875993.asia-southeast2.run.app/storage/attendance_images/ca86eb39-9002-47c8-858e-5994d607e210.jpg",
            "status_absen": "Terlambat",
            "status_dasi": "Tidak Ada Dasi",
            "status_mood": "sad",
            "student_id": 5,
            "username": "zain"
        },
        {
            "date": "2024-12-10 20:55:13",
            "image_url": "https://checkmate-506488875993.asia-southeast2.run.app/storage/attendance_images/67139251-a253-4395-9997-f1faeea93e25.jpg",
            "status_absen": "Terlambat",
            "status_dasi": "Tidak Ada Dasi",
            "status_mood": "angry",
            "student_id": 3,
            "username": "liza"
        }
    ],
    "debug_info": {
        "queried_date": "All dates",
        "total_records": 3
    },
    "status": "success"
}

Endpoint Predict All Metode POST: (hanya guru yang bisa) https://checkmate-506488875993.asia-southeast2.run.app/api/predict-all
Headers:
![bearer](https://github.com/user-attachments/assets/045dbacf-b8af-4295-b2a7-786e253c3877)

Request: 
Body form-data:
Content-Type: multipart/form-data
Body:
{ 
"file": "<image_file>" 
}
Response:
{
    "results": {
        "predict_absen": {
            "attendance_count": 0,
            "confidence": 0.9589236974716187,
            "datetime": "2024-12-10 20:55:42 +0700",
            "image_url": "https://checkmate-506488875993.asia-southeast2.run.app/storage/attendance_images/07180d83-0aab-4468-969b-c28823484640.jpg",
            "predicted_name": "nabila",
            "send_message": [
                "Siswa Nabila Terlambat dan (Tidak Ada Dasi) pada 2024-12-10 20:55:42 +0700."
            ],
            "status_absen": "Terlambat"
        },
        "predict_dasi": {
            "confidence": 1.0,
            "predicted_class": "Tidak Ada Dasi"
        },
        "predict_mood": {
            "class_probabilities": {
                "angry": 0.25641950964927673,
                "happy": 0.17951296269893646,
                "neutral": 0.1502477526664734,
                "sad": 0.4138197898864746
            },
            "confidence": 0.4138197898864746,
            "predicted_class_name": "sad"
        }
    },
    "status": "success"
}


Akun Guru Terdaftar:
Bisa menggunakan email atau username
"email": "joel@gmail.com" 	atau	"email": "joel"
"password": "password123"		"password": "password123"


"email": "yoga@gmail.com"	atau	"email": "yoga"
"password": "password123"		"password": "password123"


"email": "krisna@gmail.com"	atau	"email": "krisna"
"password": "password123"		"password": "password123"


"email": "mike@gmail.com"	atau	"email": "mike"
"password": "password123"		"password": "password123"


Akun Siswa Terdaftar:
Bisa menggunakan email atau username
"email": "liza"
"password": "password123"


"email": "zain"
"password": "password123"


"email": "nabila"
"password": "password123"
