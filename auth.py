import json
import os
import hashlib

USERS_FILE = "data/users.json"

def _hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
            # Handle old format (username -> hash string) by upgrading to dict format
            for username, value in users.items():
                if isinstance(value, str):
                    users[username] = {"password": value, "role": "Student"}
            return users
    return {}

def save_users(users):
    os.makedirs("data", exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def signup_user(username, password, role):
    username = username.strip()
    if not username or not password:
        return False, "Username and password cannot be empty"

    users = load_users()
    if username in users:
        return False, "Username already exists"

    users[username] = {"password": _hash_password(password), "role": role}
    save_users(users)
    return True, "Account created successfully. Please log in."

def login_user(username, password):
    username = username.strip()
    users = load_users()

    if username not in users:
        return False, "Username not found"
    if users[username]["password"] != _hash_password(password):
        return False, "Incorrect password"

    return True, users[username]["role"]

def get_all_users():
    users = load_users()
    return [{"username": u, "role": v["role"]} for u, v in users.items()]