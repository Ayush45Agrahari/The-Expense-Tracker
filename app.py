from flask import Flask, render_template, request, redirect, jsonify
import json
import os
from flask import Response


app = Flask(__name__)

DATA_FILE = "data/expenses.json"

# Ensure the data directory exists
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)




@app.route('/')
def index():
    return render_template('index.html')

app.jinja_env.auto_reload = True  # Ensure templates are reloaded
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Enable template auto-reload



@app.after_request
def add_header(response):
    response.cache_control.no_cache = True
    return response





# Create the file if it doesn't exist
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        f.write("[]")


def read_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def write_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/view')
def view_expenses():
    data = read_data()  # Load expenses from the JSON file
    # Calculate summary here
    total_expense = sum(expense['amount'] for expense in data)
    paid_amount = sum(expense.get('paid', 0) for expense in data)  # Example: expenses might have a 'paid' field
    remaining_amount = total_expense - paid_amount

    summary = {
        'total': total_expense,
        'paid': paid_amount,
        'remaining': remaining_amount
    }
    return render_template('view_expenses.html', expenses=data, summary=summary)





def calculate_summary():
    data = read_data()
    paid = sum(expense["amount"] for expense in data if expense["is_paid"])
    total = sum(expense["amount"] for expense in data)
    remaining = total - paid
    return {"paid": paid, "remaining": remaining, "total": total}


@app.route('/mark_paid/<int:expense_id>')
def mark_as_paid(expense_id):
    data = read_data()
    if 0 <= expense_id < len(data):
        data[expense_id]["is_paid"] = True
        write_data(data)
    return redirect("/view")


@app.route('/add', methods=["GET", "POST"])
def add_expense():
    if request.method == "POST":
        expense = {
            "date": request.form["date"],
            "category": request.form["category"],
            "amount": float(request.form["amount"]),
            "description": request.form["description"],
            "is_paid": request.form.get("is_paid") == "on"  # New field for payment status
        }
        data = read_data()
        data.append(expense)
        write_data(data)
        return redirect("/")
    return render_template('add_expense.html')




@app.route('/api/summary')
def summary():
    data = read_data()
    summary = {}
    for item in data:
        category = item["category"]
        summary[category] = summary.get(category, 0) + item["amount"]
    return jsonify(summary)

@app.route('/delete/<int:expense_id>', methods=['POST'])

def delete_expense(expense_id):
    data = read_data()
    if 0 <= expense_id < len(data):
        del data[expense_id]
        write_data(data)
    return redirect('/view')


@app.route('/update/<int:expense_id>', methods=['GET', 'POST'])
def update_expense(expense_id):
    data = read_data()  # Load existing expenses
    expense = data[expense_id]  # Get the expense to be updated

    if request.method == 'POST':
        # Update the expense details
        
        expense['amount'] = float(request.form['amount'])
        expense['new_description'] = request.form['new_description']
        expense['paid'] = float(request.form['paid'])  # Amount paid input
        expense['remaining'] = expense['amount'] - expense['paid']  # Calculate remaining

        # Save updated data
        data[expense_id] = expense
        write_data(data)

        return redirect('/view')

    return render_template('update_expense.html', expense=expense, expense_id=expense_id)






if __name__ == "__main__":
    app.run(debug=True)