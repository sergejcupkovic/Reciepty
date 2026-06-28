import os
import webbrowser
import uuid
import datetime
from threading import Timer
from flask import Flask, render_template, request, redirect, url_for, jsonify
from app.database import get_all_expenses, get_expense_by_id, init_db, insert_expense, get_all_tags, add_tag, update_expense, toggle_tag
from app.scraper import scrape_and_save
init_db()

app = Flask(__name__, template_folder="app/templates")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "manual_entry" in request.form:
            store_name = request.form.get("store_name", "Nepoznato")
            total_amount = float(request.form.get("total_amount", 0.0) or 0.0)
            tags_list = request.form.getlist("tags")
            tags = ",".join([t for t in tags_list if t.strip()])
            important = request.form.get("important") == "on"
            
            item_names = request.form.getlist("item_name[]")
            item_quantities = request.form.getlist("item_quantity[]")
            item_prices = request.form.getlist("item_price[]")
            item_totals = request.form.getlist("item_total[]")
            
            items = []
            for i in range(len(item_names)):
                if item_names[i].strip():
                    items.append({
                        "name": item_names[i],
                        "quantity": float(item_quantities[i]) if i < len(item_quantities) and item_quantities[i] else 1.0,
                        "price": float(item_prices[i]) if i < len(item_prices) and item_prices[i] else 0.0,
                        "total_price": float(item_totals[i]) if i < len(item_totals) and item_totals[i] else 0.0
                    })
            
            invoice_number = f"MANUAL_{uuid.uuid4().hex[:8].upper()}"
            invoice_date = datetime.date.today().isoformat()
            
            invoice_text_lines = [
                f"=== {store_name} ===",
                f"Datum: {invoice_date}",
                "--------------------------------",
                "Stavke:"
            ]
            
            for item in items:
                line = f"{item['name']}\n    {item['quantity']} x {item['price']:.2f} = {item['total_price']:.2f} RSD"
                invoice_text_lines.append(line)
                
            if not items:
                invoice_text_lines.append("Nema unetih stavki.")
                
            invoice_text_lines.append("--------------------------------")
            invoice_text_lines.append(f"UKUPNO: {total_amount:.2f} RSD")
            
            invoice_text = "\n".join(invoice_text_lines)
            
            try:
                insert_expense(
                    company_name=store_name,
                    invoice_number=invoice_number,
                    invoice_date=invoice_date,
                    total_amount=total_amount,
                    items=items,
                    invoice_text=invoice_text,
                    tags=tags,
                    important=important
                )
            except Exception as e:
                print(f"Error saving manual entry: {e}")
            
            return redirect(url_for("index"))

        url = request.form.get("url")
        if url:
            try:
          
                scrape_and_save(url)
            except Exception as e:
                print(f"Error saving receipt: {e}")
  
        return redirect(url_for("index"))

 
    search_query = request.args.get("search", "")
    tag_filter = request.args.get("tag_filter", "")
    all_receipts = get_all_expenses(search_query=search_query)
    
    if tag_filter:
        filtered_by_tag = []
        for r in all_receipts:
            r_tags = [t.strip() for t in (r['tags'] or "").split(',') if t.strip()]
            if tag_filter in r_tags:
                filtered_by_tag.append(r)
        all_receipts = filtered_by_tag
    
    all_tags = get_all_tags()
    tag_colors = {t['name']: t['color'] for t in all_tags}

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
                           total_spent=total_spent,
                           search_query=search_query,
                           tag_filter=tag_filter,
                           all_tags=all_tags,
                           tag_colors=tag_colors)

@app.route("/update/<int:receipt_id>", methods=["POST"])
def update_receipt(receipt_id):
    data = request.get_json()
    important = data.get("important", False)
    update_expense(receipt_id, important)
    return jsonify({"success": True})

@app.route("/toggle_tag/<int:receipt_id>", methods=["POST"])
def api_toggle_tag(receipt_id):
    data = request.get_json()
    tag = data.get("tag", "")
    if tag:
        toggle_tag(receipt_id, tag)
    return jsonify({"success": True})

@app.route("/add_tag", methods=["POST"])
def add_new_tag():
    name = request.form.get("name", "").strip()
    color = request.form.get("color", "#6c757d") # default secondary
    if name:
        add_tag(name, color)
    return redirect(url_for("index"))

@app.route("/receipt/<int:receipt_id>")
def view_receipt(receipt_id):
    receipt = get_expense_by_id(receipt_id)
    if not receipt:
        return "Receipt not found", 404
        
    all_tags = get_all_tags()
    tag_colors = {t['name']: t['color'] for t in all_tags}
    
    return render_template("receipt.html", receipt=receipt, tag_colors=tag_colors)

def open_browser():
    webbrowser.open("http://127.0.0.1:5000/")

if __name__ == "__main__":
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        Timer(1, open_browser).start()
    app.run(debug=False, port=5000)
