from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- FILE PATHS ----------------
DATA_FILE = "data/expenses.json"
USERS_FILE = "data/users.json"

os.makedirs("data", exist_ok=True)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump([], f)

# ---------------- HELPERS ----------------
def read_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def write_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def read_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def write_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def calculate_summary(data):
    total = sum(e.get("amount", 0) for e in data)
    paid = sum(e.get("amount", 0) for e in data if e.get("is_paid"))
    remaining = total - paid
    return {"total": total, "paid": paid, "remaining": remaining}

# ---------------- AUTH ROUTES ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        users = read_users()
        for u in users:
            if u["username"] == username:
                flash("Username already exists", "error")
                return redirect("/signup")

        users.append({
            "username": username,
            "password": generate_password_hash(password)
        })
        write_users(users)

        flash("Account created successfully! Please login.", "success")
        return redirect("/login")

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        users = read_users()
        for u in users:
            if u["username"] == username and check_password_hash(u["password"], password):
                session["user"] = username
                flash("Login successful!", "success")
                return redirect("/")

        flash("Invalid username or password", "error")
        return redirect("/login")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out successfully", "success")
    return redirect("/login")

# ---------------- PAGES ----------------
@app.route("/")
def index():
    if "user" not in session:
        return redirect("/login")
    return render_template("index.html")

@app.route("/add", methods=["GET", "POST"])
def add_expense():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        expense = {
            "user": session["user"],
            "date": request.form["date"],
            "category": request.form["category"],
            "amount": float(request.form["amount"]),
            "description": request.form["description"],
            "is_paid": request.form.get("is_paid") == "on"
        }

        data = read_data()
        data.append(expense)
        write_data(data)

        flash("Expense added successfully!", "success")
        return redirect("/view")

    return render_template("add_expense.html")

@app.route("/view")
def view_expenses():
    if "user" not in session:
        return redirect("/login")

    selected_category = request.args.get("category", "All")
    data = read_data()

    # user-wise filter (safe)
    user_expenses = [
        e for e in data
        if e.get("user") == session["user"]
    ]

    # category filter (case-insensitive)
    if selected_category != "All":
        user_expenses = [
            e for e in user_expenses
            if e.get("category", "").lower() == selected_category.lower()
        ]

    summary = calculate_summary(user_expenses)

    return render_template(
        "view_expenses.html",
        expenses=user_expenses,
        summary=summary,
        selected_category=selected_category
    )

@app.route("/update/<int:expense_id>", methods=["GET", "POST"])
def update_expense(expense_id):
    if "user" not in session:
        return redirect("/login")

    data = read_data()
    user_expenses = [e for e in data if e.get("user") == session["user"]]

    if not (0 <= expense_id < len(user_expenses)):
        return redirect("/view")

    expense = user_expenses[expense_id]

    if request.method == "POST":
        expense["date"] = request.form["date"]
        expense["category"] = request.form["category"]
        expense["amount"] = float(request.form["amount"])
        expense["description"] = request.form["description"]
        expense["is_paid"] = request.form.get("is_paid") == "on"

        write_data(data)
        flash("Expense updated successfully!", "success")
        return redirect("/view")

    return render_template("update_expense.html", expense=expense)

@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    if "user" not in session:
        return redirect("/login")

    data = read_data()
    user_expenses = [e for e in data if e.get("user") == session["user"]]

    if 0 <= expense_id < len(user_expenses):
        data.remove(user_expenses[expense_id])
        write_data(data)
        flash("Expense deleted successfully!", "success")

    return redirect("/view")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
