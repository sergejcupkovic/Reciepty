import os
import webbrowser
from threading import Timer
from flask import Flask, render_template, request, redirect, url_for
from app.database import get_all_expenses, get_expense_by_id, init_db
from app.scraper import scrape_and_save
init_db()

app = Flask(__name__, template_folder="app/templates")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        if url:
            try:
          
                scrape_and_save(url)
            except Exception as e:
                print(f"Error saving receipt: {e}")
  
        return redirect(url_for("index"))

 
    all_receipts = get_all_expenses()
    

    months = sorted(list(set([r['invoice_date'][:7] for r in all_receipts if r['invoice_date']])), reverse=True)
    

    selected_month = request.args.get("month")
    if not selected_month and months:
        selected_month = months[0]
        

    filtered_receipts = [r for r in all_receipts if r['invoice_date'] and r['invoice_date'].startswith(selected_month)]
    

    total_spent = sum(r['total_amount'] for r in filtered_receipts)
    
    return render_template("index.html", 
                           receipts=filtered_receipts, 
                           months=months, 
                           selected_month=selected_month, 
                           total_spent=total_spent)

@app.route("/receipt/<int:receipt_id>")
def view_receipt(receipt_id):
    receipt = get_expense_by_id(receipt_id)
    if not receipt:
        return "Receipt not found", 404
        
    return render_template("receipt.html", receipt=receipt)

def open_browser():
    webbrowser.open("http://127.0.0.1:5000/")

if __name__ == "__main__":
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        Timer(1, open_browser).start()
    app.run(debug=True)
