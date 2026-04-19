from flask import Flask, jsonify, request, Response
import json
import os
import time
import requests
import pymysql
from jose import jwt

app = Flask(__name__)

ISSUER = os.getenv("OIDC_ISSUER", "http://localhost:8081/realms/realm_final_cloud")
AUDIENCE = os.getenv("OIDC_AUDIENCE", "flask-app")
JWKS_URL = os.getenv(
    "OIDC_JWKS_URL",
    "http://authentication-identity-server:8080/realms/realm_final_cloud/protocol/openid-connect/certs"
)
DB_HOST = os.getenv("DB_HOST", "relational-database-server")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
DB_NAME = os.getenv("DB_NAME", "studentdb")

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

_JWKS = None
_TS = 0


def get_jwks():
    global _JWKS, _TS
    now = time.time()
    if not _JWKS or now - _TS > 600:
        r = requests.get(JWKS_URL, timeout=5)
        print("JWKS_URL =", JWKS_URL)
        print("Status =", r.status_code)
        print("Body =", r.text)
        _JWKS = r.json()
        _TS = now
    return _JWKS


@app.get("/")
def home():
    return jsonify({
        "message": "Application Backend Server is running",
        "project": "final-cloud",
        "service": "application-backend-server"
    })


@app.get("/hello")
def hello():
    return jsonify({
        "message": "Hello from Application Backend Server!",
        "project": "final-cloud",
        "service": "application-backend-server",
        "status": "success"
    })


@app.get("/student")
def student():
    try:
        with open("students.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        accept = request.headers.get("Accept", "")

        # Nếu là browser thì trả HTML giống hình minh họa
        if "text/html" in accept and "application/json" not in accept:
            rows = ""
            for s in data:
                rows += f"""
                <tr>
                    <td>{s['id']}</td>
                    <td>{s['name']}</td>
                    <td>{s['major']}</td>
                    <td>{s['gpa']}</td>
                </tr>
                """

            html = f"""
            <!DOCTYPE html>
            <html lang="vi">
            <head>
                <meta charset="UTF-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <title>Danh sách sinh viên (JSON)</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background: #f4f6f8;
                        margin: 0;
                        padding: 18px;
                        color: #222;
                    }}

                    .container {{
                        max-width: 980px;
                        margin: 0 auto;
                    }}

                    h1 {{
                        font-size: 20px;
                        color: #2d63da;
                        margin-bottom: 16px;
                    }}

                    .table-wrap {{
                        background: white;
                        border-radius: 10px;
                        overflow: hidden;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
                    }}

                    table {{
                        width: 100%;
                        border-collapse: collapse;
                    }}

                    thead {{
                        background: #2d63da;
                        color: white;
                    }}

                    th, td {{
                        text-align: left;
                        padding: 14px 12px;
                        font-size: 14px;
                    }}

                    tbody tr {{
                        border-top: 1px solid #e5e7eb;
                    }}

                    tbody tr:hover {{
                        background: #f9fafb;
                    }}

                    .note {{
                        margin-top: 14px;
                        font-size: 13px;
                        color: #666;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Danh sách sinh viên (JSON)</h1>

                    <div class="table-wrap">
                        <table>
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Name</th>
                                    <th>Major</th>
                                    <th>GPA</th>
                                </tr>
                            </thead>
                            <tbody>
                                {rows}
                            </tbody>
                        </table>
                    </div>

                    <div class="note">
                        Dữ liệu được đọc từ file <strong>students.json</strong>.
                    </div>
                </div>
            </body>
            </html>
            """
            return Response(html, mimetype="text/html")

        # Mặc định trả JSON đúng yêu cầu API
        return jsonify(data)

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Cannot read students.json",
            "error": str(e)
        }), 500

@app.get("/students-db")
def students_db():
    try:
        conn = get_db_connection()

        with conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, student_id, fullname, dob, major
                    FROM students
                    ORDER BY id
                """)
                rows = cursor.fetchall()

        accept = request.headers.get("Accept", "")

        # Nếu gọi từ API/curl thì trả JSON
        if "application/json" in accept or request.args.get("format") == "json":
            return jsonify(rows)

        # Nếu mở bằng trình duyệt thì trả UI HTML
        html = """
        <!DOCTYPE html>
        <html lang="vi">
        <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>Danh sách sinh viên (MariaDB)</title>
            <style>
                * {
                    box-sizing: border-box;
                }

                body {
                    font-family: Arial, sans-serif;
                    background: #f4f6f8;
                    margin: 0;
                    padding: 16px;
                    color: #222;
                }

                .container {
                    max-width: 1100px;
                    margin: 0 auto;
                }

                .header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    gap: 12px;
                    margin-bottom: 18px;
                    flex-wrap: wrap;
                }

                h1 {
                    font-size: 20px;
                    color: #2ea043;
                    margin: 0;
                }

                .toolbar {
                    display: flex;
                    gap: 10px;
                    flex-wrap: wrap;
                }

                .btn {
                    border: none;
                    border-radius: 8px;
                    padding: 10px 14px;
                    font-size: 14px;
                    font-weight: bold;
                    cursor: pointer;
                }

                .btn-primary {
                    background: #2ea043;
                    color: white;
                }

                .btn-secondary {
                    background: #2563eb;
                    color: white;
                }

                .btn-danger {
                    background: #dc2626;
                    color: white;
                }

                .btn-light {
                    background: #e5e7eb;
                    color: #111827;
                }

                .layout {
                    display: grid;
                    grid-template-columns: 1.4fr 1fr;
                    gap: 18px;
                }

                .card {
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
                    overflow: hidden;
                }

                .card-body {
                    padding: 16px;
                }

                .table-wrap {
                    overflow-x: auto;
                }

                table {
                    width: 100%;
                    border-collapse: collapse;
                }

                thead {
                    background: #2ea043;
                    color: white;
                }

                th, td {
                    text-align: left;
                    padding: 14px 12px;
                    font-size: 14px;
                    border-bottom: 1px solid #e5e7eb;
                }

                tbody tr:hover {
                    background: #f9fafb;
                }

                tbody tr.active {
                    background: #ecfdf5;
                }

                .actions {
                    display: flex;
                    gap: 8px;
                    flex-wrap: wrap;
                }

                label {
                    display: block;
                    font-size: 13px;
                    font-weight: bold;
                    margin-bottom: 6px;
                    color: #374151;
                }

                input {
                    width: 100%;
                    padding: 10px 12px;
                    border: 1px solid #d1d5db;
                    border-radius: 8px;
                    margin-bottom: 14px;
                    font-size: 14px;
                }

                .status {
                    margin-bottom: 12px;
                    padding: 10px 12px;
                    border-radius: 8px;
                    display: none;
                    font-size: 14px;
                }

                .status.success {
                    display: block;
                    background: #dcfce7;
                    color: #166534;
                }

                .status.error {
                    display: block;
                    background: #fee2e2;
                    color: #991b1b;
                }

                .note {
                    margin-top: 14px;
                    font-size: 13px;
                    color: #666;
                }

                @media (max-width: 900px) {
                    .layout {
                        grid-template-columns: 1fr;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Danh sách sinh viên (MariaDB)</h1>
                    <div class="toolbar">
                        <button class="btn btn-primary" onclick="setCreateMode()">Thêm sinh viên</button>
                        <a class="btn btn-light" href="/" style="text-decoration:none;display:inline-flex;align-items:center;">Trang chủ</a>
                    </div>
                </div>

                <div class="layout">
                    <div class="card">
                        <div class="table-wrap">
                            <table>
                                <thead>
                                    <tr>
                                        <th>#</th>
                                        <th>Student ID</th>
                                        <th>Fullname</th>
                                        <th>DOB</th>
                                        <th>Major</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="studentTableBody"></tbody>
                            </table>
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-body">
                            <div id="statusBox" class="status"></div>

                            <h3 id="formTitle" style="margin-top:0; color:#2ea043;">Thêm sinh viên</h3>

                            <input type="hidden" id="studentDbId" />

                            <label for="student_id">Student ID</label>
                            <input type="text" id="student_id" placeholder="VD: SV004" />

                            <label for="fullname">Fullname</label>
                            <input type="text" id="fullname" placeholder="VD: Pham Van D" />

                            <label for="dob">DOB</label>
                            <input type="date" id="dob" />

                            <label for="major">Major</label>
                            <input type="text" id="major" placeholder="VD: Information Technology" />

                            <div class="actions">
                                <button class="btn btn-primary" id="saveBtn" onclick="saveStudent()">Lưu</button>
                                <button class="btn btn-light" onclick="resetForm()">Làm mới</button>
                            </div>

                            <div class="note">
                                Trang này thao tác trực tiếp với bảng <strong>students</strong> trong database <strong>studentdb</strong>.
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                let selectedId = null;
                let students = [];

                async function loadStudents() {
                    try {
                        const res = await fetch('/api/students-db?format=json', {
                            headers: { 'Accept': 'application/json' }
                        });
                        students = await res.json();

                        const tbody = document.getElementById('studentTableBody');
                        tbody.innerHTML = students.map(s => `
                            <tr class="${selectedId === s.id ? 'active' : ''}">
                                <td>${s.id}</td>
                                <td>${s.student_id}</td>
                                <td>${s.fullname}</td>
                                <td>${s.dob}</td>
                                <td>${s.major}</td>
                                <td>
                                    <div class="actions">
                                        <button class="btn btn-secondary" onclick="editStudent(${s.id})">Sửa</button>
                                        <button class="btn btn-danger" onclick="deleteStudent(${s.id})">Xóa</button>
                                    </div>
                                </td>
                            </tr>
                        `).join('');
                    } catch (err) {
                        showStatus('Không tải được dữ liệu sinh viên.', 'error');
                    }
                }

                function showStatus(message, type) {
                    const box = document.getElementById('statusBox');
                    box.className = 'status ' + type;
                    box.textContent = message;
                }

                function resetForm() {
                    selectedId = null;
                    document.getElementById('studentDbId').value = '';
                    document.getElementById('student_id').value = '';
                    document.getElementById('fullname').value = '';
                    document.getElementById('dob').value = '';
                    document.getElementById('major').value = '';
                    document.getElementById('formTitle').textContent = 'Thêm sinh viên';
                    document.getElementById('saveBtn').textContent = 'Lưu';
                    document.getElementById('statusBox').className = 'status';
                    document.getElementById('statusBox').textContent = '';
                    loadStudents();
                }

                function setCreateMode() {
                    resetForm();
                }

                function editStudent(id) {
                    const student = students.find(s => s.id === id);
                    if (!student) return;

                    selectedId = id;
                    document.getElementById('studentDbId').value = student.id;
                    document.getElementById('student_id').value = student.student_id;
                    document.getElementById('fullname').value = student.fullname;
                    document.getElementById('dob').value = student.dob;
                    document.getElementById('major').value = student.major;
                    document.getElementById('formTitle').textContent = 'Cập nhật sinh viên';
                    document.getElementById('saveBtn').textContent = 'Cập nhật';
                    loadStudents();
                }

                async function saveStudent() {
                    const id = document.getElementById('studentDbId').value;
                    const payload = {
                        student_id: document.getElementById('student_id').value.trim(),
                        fullname: document.getElementById('fullname').value.trim(),
                        dob: document.getElementById('dob').value,
                        major: document.getElementById('major').value.trim()
                    };

                    if (!payload.student_id || !payload.fullname || !payload.dob || !payload.major) {
                        showStatus('Vui lòng nhập đầy đủ thông tin.', 'error');
                        return;
                    }

                    try {
                        let res;
                        if (id) {
                            res = await fetch(`/api/students-db/${id}`, {
                                method: 'PUT',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify(payload)
                            });
                        } else {
                            res = await fetch('/api/students-db', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify(payload)
                            });
                        }

                        const data = await res.json();

                        if (!res.ok) {
                            showStatus(data.message || 'Thao tác thất bại.', 'error');
                            return;
                        }

                        showStatus(data.message || 'Thao tác thành công.', 'success');
                        resetForm();
                    } catch (err) {
                        showStatus('Không thể lưu dữ liệu.', 'error');
                    }
                }

                async function deleteStudent(id) {
                    const ok = confirm('Bạn có chắc muốn xóa sinh viên này không?');
                    if (!ok) return;

                    try {
                        const res = await fetch(`/api/students-db/${id}`, {
                            method: 'DELETE'
                        });

                        const data = await res.json();

                        if (!res.ok) {
                            showStatus(data.message || 'Xóa thất bại.', 'error');
                            return;
                        }

                        showStatus(data.message || 'Xóa thành công.', 'success');
                        resetForm();
                    } catch (err) {
                        showStatus('Không thể xóa dữ liệu.', 'error');
                    }
                }

                loadStudents();
            </script>
        </body>
        </html>
        """
        return Response(html, mimetype="text/html")

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Cannot read data from database",
            "error": str(e)
        }), 500


@app.post("/students-db")
def create_student_db():
    try:
        data = request.get_json()

        student_id = data.get("student_id")
        fullname = data.get("fullname")
        dob = data.get("dob")
        major = data.get("major")

        if not all([student_id, fullname, dob, major]):
            return jsonify({
                "status": "error",
                "message": "Missing required fields"
            }), 400

        conn = get_db_connection()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO students (student_id, fullname, dob, major)
                    VALUES (%s, %s, %s, %s)
                """, (student_id, fullname, dob, major))
                new_id = cursor.lastrowid

        return jsonify({
            "status": "success",
            "message": "Thêm sinh viên thành công",
            "id": new_id
        }), 201

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Cannot create student",
            "error": str(e)
        }), 500


@app.put("/students-db/<int:id>")
def update_student_db(id):
    try:
        data = request.get_json()

        student_id = data.get("student_id")
        fullname = data.get("fullname")
        dob = data.get("dob")
        major = data.get("major")

        conn = get_db_connection()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE students
                    SET student_id=%s, fullname=%s, dob=%s, major=%s
                    WHERE id=%s
                """, (student_id, fullname, dob, major, id))

                if cursor.rowcount == 0:
                    return jsonify({
                        "status": "error",
                        "message": "Student not found"
                    }), 404

        return jsonify({
            "status": "success",
            "message": "Cập nhật sinh viên thành công"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Cannot update student",
            "error": str(e)
        }), 500


@app.delete("/students-db/<int:id>")
def delete_student_db(id):
    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM students WHERE id=%s", (id,))

                if cursor.rowcount == 0:
                    return jsonify({
                        "status": "error",
                        "message": "Student not found"
                    }), 404

        return jsonify({
            "status": "success",
            "message": "Xóa sinh viên thành công"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Cannot delete student",
            "error": str(e)
        }), 500


@app.get("/secure")
def secure():
    auth = request.headers.get("Authorization", "")

    if not auth.startswith("Bearer "):
        return jsonify({
            "status": "error",
            "message": "Missing Bearer token"
        }), 401

    token = auth.split(" ", 1)[1]

    try:
        payload = jwt.decode(
            token,
            get_jwks(),
            algorithms=["RS256"],
            issuer=ISSUER,
            options={"verify_aud": False}
        )

        return jsonify({
            "status": "success",
            "message": "Secure resource accessed successfully",
            "preferred_username": payload.get("preferred_username"),
            "issuer": ISSUER
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Invalid or expired token",
            "error": str(e)
        }), 401


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)