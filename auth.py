import json
import os
import hashlib

USERS_FILE = "data/users.json"

def _hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    os.makedirs("data", exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def signup_user(username, password):
    username = username.strip()
    if not username or not password:
        return False, "Username and password cannot be empty"

    users = load_users()
    if username in users:
        return False, "Username already exists"

    users[username] = _hash_password(password)
    save_users(users)
    return True, "Account created successfully. Please log in."

def login_user(username, password):
    username = username.strip()
    users = load_users()

    if username not in users:
        return False, "Username not found"
    if users[username] != _hash_password(password):
        return False, "Incorrect password"

    return True, "Login successful"