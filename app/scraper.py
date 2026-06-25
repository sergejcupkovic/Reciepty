from sr_invoice_parser import InvoiceParser
from app.database import insert_expense

def scrape_and_save(url: str):
    print("Scraping URL...")
    parser = InvoiceParser(url=url)
    parser.data()
    
   
    company_name = parser.get_company_name()
    invoice_number = parser.get_invoice_number() 
    invoice_date = parser.get_dt()
    total_amount = parser.get_total_amount()
    items = parser.get_items()
    invoice_text = parser.get_invoice_text()
    
    print(f"Successfully Scraped: {company_name} | {invoice_date} | {total_amount} RSD")
    
 
    expense_id = insert_expense(
        company_name=company_name,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        total_amount=total_amount,
        items=items,
        invoice_text=invoice_text
    )
    
    print(f"Success! Saved to database as expense ID: {expense_id}")
    return expense_id


