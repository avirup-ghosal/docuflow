import os
import datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text  
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError

# 1. Load Environment Variables
load_dotenv()

# 2. Configuration
app = Flask(__name__)

db_host = os.environ.get('DB_HOST', 'localhost')
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://auth_user:auth_password@{db_host}:5432/auth_db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'super-secret-key')

# 3. Initialize Extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# 4. SQL Table Definition (Raw SQL)
CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# 5. Routes

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "running"}), 200

@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        # 1. Hash the password
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # 'RETURNING id' to return id
        sql = text("""
            INSERT INTO users (email, password_hash, created_at) 
            VALUES (:email, :pwd, :created) 
            RETURNING id
        """)
        
        # 3. Execute the query
        result = db.session.execute(sql, {
            "email": email,
            "pwd": hashed_pw,
            "created": datetime.datetime.utcnow()
        })
        
        db.session.commit()
        
        # 4. Fetch the returned ID
        new_user_id = result.fetchone()[0]

        return jsonify({"message": "User created successfully", "user_id": new_user_id}), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "User already exists"}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # 1. Raw SQL Select
    sql = text("SELECT id, email, password_hash FROM users WHERE email = :email")
    
    # 2. Execute and mapping() allows us to access columns by name (row['email'])
    result = db.session.execute(sql, {"email": email})
    user = result.mappings().first()

    # 3. Verify
    if user and bcrypt.check_password_hash(user['password_hash'], password):
        # Generate JWT
        access_token = create_access_token(identity=str(user['id']))
        return jsonify({"access_token": access_token}), 200
    
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    
    sql = text("SELECT id, email, created_at FROM users WHERE id = :id")
    result = db.session.execute(sql, {"id": current_user_id})
    user = result.mappings().first()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    return jsonify({
        "id": user['id'],
        "email": user['email'],
        "created_at": user['created_at']
    }), 200

if __name__ == '__main__':
    with app.app_context():
        # Create table on startup
        db.session.execute(text(CREATE_USERS_TABLE))
        db.session.commit()
    
    app.run(host='0.0.0.0', port=5000, debug=True)