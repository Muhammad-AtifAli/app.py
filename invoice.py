import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import date, datetime
from io import BytesIO
import json
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Advanced Invoice App",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_FILE = "invoice_records.json"

# =========================
# CSS DESIGN
# =========================
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #f7f9fc 0%, #eef3ff 100%);
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    .hero-box {
        background: linear-gradient(135deg, #1f4fd8 0%, #00a6ff 100%);
        padding: 28px;
        border-radius: 22px;
        color: white;
        box-shadow: 0 12px 35px rgba(31,79,216,0.25);
        margin-bottom: 20px;
    }

    .hero-title {
        font-size: 38px;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .hero-subtitle {
        font-size: 16px;
        opacity: 0.95;
    }

    .metric-card {
        background: white;
        padding: 18px;
        border-radius: 18px;
        border: 1px solid #e8eefc;
        box-shadow: 0 6px 20px rgba(0,0,0,0.04);
        text-align: center;
    }

    .metric-title {
        color: #64748b;
        font-size: 14px;
        font-weight: 600;
    }

    .metric-value {
        color: #0f172a;
        font-size: 26px;
        font-weight: 800;
    }

    .section-card {
        background: white;
        padding: 22px;
        border-radius: 20px;
        border: 1px solid #e8eefc;
        box-shadow: 0 6px 22px rgba(0,0,0,0.04);
        margin-bottom: 18px;
    }

    .warning-box {
        background: #fff7ed;
        color: #9a3412;
        padding: 14px;
        border-radius: 14px;
        border: 1px solid #fed7aa;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# =========================
# DATA FUNCTIONS
# =========================
def load_records():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_records(records):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=4, ensure_ascii=False)


def generate_invoice_number():
    records = load_records()
    current_year = datetime.now().year
    next_no = len(records) + 1
    return f"INV-{current_year}-{next_no:04d}"


def money(value):
    try:
        return f"{value:,.2f}"
    except Exception:
        return "0.00"


# =========================
# PDF GENERATION
# =========================
def create_pdf(invoice_data):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=35,
        leftMargin=35,
        topMargin=35,
        bottomMargin=35
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontSize=24,
        textColor=colors.HexColor("#1f4fd8"),
        spaceAfter=12
    )

    normal_style = styles["Normal"]

    heading_style = ParagraphStyle(
        "HeadingStyle",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#0f172a"),
        fontSize=13,
        spaceBefore=8,
        spaceAfter=6
    )

    story = []

    story.append(Paragraph("INVOICE", title_style))

    header_table = Table([
        [
            Paragraph(
                f"<b>{invoice_data['business_name']}</b><br/>"
                f"{invoice_data['business_address']}<br/>"
                f"Phone: {invoice_data['business_phone']}<br/>"
                f"Email: {invoice_data['business_email']}",
                normal_style
            ),
            Paragraph(
                f"<b>Invoice No:</b> {invoice_data['invoice_no']}<br/>"
                f"<b>Date:</b> {invoice_data['invoice_date']}<br/>"
                f"<b>Due Date:</b> {invoice_data['due_date']}<br/>"
                f"<b>Status:</b> {invoice_data['status']}",
                normal_style
            )
        ]
    ], colWidths=[3.7 * inch, 2.5 * inch])

    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fbff")),
        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#dbeafe")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 10),
    ]))

    story.append(header_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Bill To", heading_style))

    customer_table = Table([
        [
            Paragraph(
                f"<b>{invoice_data['customer_name']}</b><br/>"
                f"{invoice_data['customer_address']}<br/>"
                f"Phone: {invoice_data['customer_phone']}<br/>"
                f"Email: {invoice_data['customer_email']}",
                normal_style
            )
        ]
    ], colWidths=[6.2 * inch])

    customer_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ffffff")),
        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#e5e7eb")),
        ("PADDING", (0, 0), (-1, -1), 10),
    ]))

    story.append(customer_table)
    story.append(Spacer(1, 16))

    item_rows = [["#", "Item", "Qty", "Rate", "Amount"]]

    for i, item in enumerate(invoice_data["items"], start=1):
        item_rows.append([
            str(i),
            str(item["item_name"]),
            str(item["quantity"]),
            money(float(item["rate"])),
            money(float(item["amount"]))
        ])

    items_table = Table(
        item_rows,
        colWidths=[
            0.35 * inch,
            2.8 * inch,
            0.65 * inch,
            1.0 * inch,
            1.2 * inch
        ]
    )

    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4fd8")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    story.append(items_table)
    story.append(Spacer(1, 14))

    totals_table = Table([
        ["Subtotal", money(invoice_data["subtotal"])],
        [f"Discount ({invoice_data['discount_percent']}%)", f"- {money(invoice_data['discount_amount'])}"],
        [f"Tax ({invoice_data['tax_percent']}%)", money(invoice_data["tax_amount"])],
        ["Grand Total", money(invoice_data["grand_total"])],
        ["Paid Amount", money(invoice_data["paid_amount"])],
        ["Balance Due", money(invoice_data["balance_due"])],
    ], colWidths=[4.6 * inch, 1.6 * inch])

    totals_table.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
        ("FONTNAME", (0, 5), (-1, 5), "Helvetica-Bold"),
        ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#dbeafe")),
        ("BACKGROUND", (0, 5), (-1, 5), colors.HexColor("#fee2e2")),
        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#e5e7eb")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e5e7eb")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    story.append(totals_table)
    story.append(Spacer(1, 16))

    if invoice_data["notes"]:
        story.append(Paragraph("Notes", heading_style))
        story.append(Paragraph(invoice_data["notes"], normal_style))
        story.append(Spacer(1, 10))

    story.append(Paragraph("Thank you for your business!", normal_style))

    doc.build(story)
    buffer.seek(0)

    return buffer


# =========================
# PRINT RECEIPT HTML
# =========================
def create_print_receipt_html(invoice_data):
    items_html = ""

    for item in invoice_data["items"]:
        items_html += f"""
        <tr>
            <td>{item['item_name']}</td>
            <td>{item['quantity']}</td>
            <td>{money(float(item['rate']))}</td>
            <td>{money(float(item['amount']))}</td>
        </tr>
        """

    receipt_html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                padding: 30px;
                color: #111827;
                background: #ffffff;
            }}

            .receipt-box {{
                max-width: 850px;
                margin: auto;
                border: 1px solid #e5e7eb;
                padding: 30px;
                border-radius: 12px;
            }}

            .header {{
                text-align: center;
                border-bottom: 2px solid #1f4fd8;
                padding-bottom: 15px;
                margin-bottom: 20px;
            }}

            .header h1 {{
                color: #1f4fd8;
                margin: 0;
                font-size: 30px;
            }}

            .header p {{
                margin: 4px 0;
                font-size: 14px;
            }}

            .info {{
                display: flex;
                justify-content: space-between;
                gap: 30px;
                margin-bottom: 20px;
                font-size: 14px;
            }}

            .info-box {{
                width: 48%;
                background: #f8fafc;
                padding: 15px;
                border-radius: 10px;
                border: 1px solid #e5e7eb;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                font-size: 14px;
            }}

            th {{
                background: #1f4fd8;
                color: white;
                padding: 10px;
                text-align: left;
            }}

            td {{
                padding: 10px;
                border-bottom: 1px solid #e5e7eb;
            }}

            .totals {{
                margin-top: 25px;
                width: 330px;
                margin-left: auto;
                font-size: 14px;
            }}

            .totals div {{
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid #e5e7eb;
            }}

            .grand {{
                font-weight: bold;
                font-size: 18px;
                color: #1f4fd8;
            }}

            .due {{
                font-weight: bold;
                color: #dc2626;
            }}

            .notes {{
                margin-top: 25px;
                background: #f8fafc;
                padding: 15px;
                border-radius: 10px;
                border: 1px solid #e5e7eb;
                font-size: 14px;
            }}

            .thanks {{
                text-align: center;
                margin-top: 35px;
                font-weight: bold;
                color: #1f4fd8;
            }}

            .print-btn {{
                margin-bottom: 20px;
                padding: 12px 25px;
                background: #1f4fd8;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                cursor: pointer;
            }}

            @media print {{
                .print-btn {{
                    display: none;
                }}

                body {{
                    padding: 0;
                    background: white;
                }}

                .receipt-box {{
                    border: none;
                    padding: 10px;
                }}
            }}
        </style>
    </head>

    <body>
        <button class="print-btn" onclick="window.print()">🖨️ Print Receipt</button>

        <div class="receipt-box">
            <div class="header">
                <h1>RECEIPT / INVOICE</h1>
                <p><strong>{invoice_data['business_name']}</strong></p>
                <p>{invoice_data['business_address']}</p>
                <p>Phone: {invoice_data['business_phone']} | Email: {invoice_data['business_email']}</p>
            </div>

            <div class="info">
                <div class="info-box">
                    <strong>Bill To:</strong><br><br>
                    {invoice_data['customer_name']}<br>
                    {invoice_data['customer_phone']}<br>
                    {invoice_data['customer_email']}<br>
                    {invoice_data['customer_address']}
                </div>

                <div class="info-box">
                    <strong>Invoice Details:</strong><br><br>
                    <strong>Invoice No:</strong> {invoice_data['invoice_no']}<br>
                    <strong>Date:</strong> {invoice_data['invoice_date']}<br>
                    <strong>Due Date:</strong> {invoice_data['due_date']}<br>
                    <strong>Status:</strong> {invoice_data['status']}
                </div>
            </div>

            <table>
                <tr>
                    <th>Item / Service</th>
                    <th>Qty</th>
                    <th>Rate</th>
                    <th>Amount</th>
                </tr>
                {items_html}
            </table>

            <div class="totals">
                <div><span>Subtotal:</span><span>{money(invoice_data['subtotal'])}</span></div>
                <div><span>Discount:</span><span>{money(invoice_data['discount_amount'])}</span></div>
                <div><span>Tax:</span><span>{money(invoice_data['tax_amount'])}</span></div>
                <div class="grand"><span>Grand Total:</span><span>{money(invoice_data['grand_total'])}</span></div>
                <div><span>Paid:</span><span>{money(invoice_data['paid_amount'])}</span></div>
                <div class="due"><span>Balance Due:</span><span>{money(invoice_data['balance_due'])}</span></div>
            </div>

            <div class="notes">
                <strong>Notes:</strong><br>
                {invoice_data['notes']}
            </div>

            <div class="thanks">
                Thank you for your business!
            </div>
        </div>
    </body>
    </html>
    """

    return receipt_html


# =========================
# SIDEBAR
# =========================
st.sidebar.title("🧾 Invoice Menu")

page = st.sidebar.radio(
    "Select Page",
    ["Create Invoice", "Invoice History", "Dashboard", "How to Use"]
)

st.sidebar.markdown("---")
st.sidebar.info(
    "Install required libraries first:\n\n"
    "pip install streamlit pandas reportlab openpyxl"
)

# =========================
# HERO SECTION
# =========================
st.markdown("""
<div class="hero-box">
    <div class="hero-title">Advanced Invoice App</div>
    <div class="hero-subtitle">
        Create beautiful invoices, calculate totals automatically, save records, print receipts, and download PDF/Excel files.
    </div>
</div>
""", unsafe_allow_html=True)

records = load_records()

# =========================
# CREATE INVOICE PAGE
# =========================
if page == "Create Invoice":

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("1. Business Information")

    col1, col2 = st.columns(2)

    with col1:
        business_name = st.text_input("Business Name", "Service Giver")
        business_phone = st.text_input("Business Phone", "03061903944")

    with col2:
        business_email = st.text_input("Business Email", "atif.ali35@gmail.com")
        business_address = st.text_area("Business Address", "Pakistan", height=80)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("2. Invoice Details")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        invoice_no = st.text_input("Invoice Number", generate_invoice_number())

    with col2:
        invoice_date = st.date_input("Invoice Date", date.today())

    with col3:
        due_date = st.date_input("Due Date", date.today())

    with col4:
        status = st.selectbox("Status", ["Unpaid", "Paid", "Partially Paid"])

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("3. Customer Information")

    col1, col2 = st.columns(2)

    with col1:
        customer_name = st.text_input("Customer Name")
        customer_phone = st.text_input("Customer Phone")

    with col2:
        customer_email = st.text_input("Customer Email")
        customer_address = st.text_area("Customer Address", height=80)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("4. Invoice Items")

    st.write("Enter your products or services below. You can add or delete rows easily.")

    default_items = pd.DataFrame({
        "item_name": ["Website Design"],
        "quantity": [1],
        "rate": [15000.0]
    })

    items_df = st.data_editor(
        default_items,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "item_name": st.column_config.TextColumn(
                "Item / Service Name",
                required=True
            ),
            "quantity": st.column_config.NumberColumn(
                "Quantity",
                min_value=0.0,
                step=1.0,
                required=True
            ),
            "rate": st.column_config.NumberColumn(
                "Rate",
                min_value=0.0,
                step=100.0,
                required=True
            ),
        }
    )

    items_df = items_df.fillna({
        "item_name": "",
        "quantity": 0,
        "rate": 0
    })

    items_df["quantity"] = pd.to_numeric(items_df["quantity"], errors="coerce").fillna(0)
    items_df["rate"] = pd.to_numeric(items_df["rate"], errors="coerce").fillna(0)
    items_df["amount"] = items_df["quantity"] * items_df["rate"]

    st.dataframe(items_df, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("5. Tax, Discount and Payment")

    subtotal = float(items_df["amount"].sum())

    col1, col2, col3 = st.columns(3)

    with col1:
        discount_percent = st.number_input(
            "Discount %",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=0.5
        )

    with col2:
        tax_percent = st.number_input(
            "Tax %",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=0.5
        )

    with col3:
        paid_amount = st.number_input(
            "Paid Amount",
            min_value=0.0,
            value=0.0,
            step=500.0
        )

    discount_amount = subtotal * discount_percent / 100
    taxable_amount = subtotal - discount_amount
    tax_amount = taxable_amount * tax_percent / 100
    grand_total = taxable_amount + tax_amount
    balance_due = grand_total - paid_amount

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.markdown(
            f'''
            <div class="metric-card">
                <div class="metric-title">Subtotal</div>
                <div class="metric-value">{money(subtotal)}</div>
            </div>
            ''',
            unsafe_allow_html=True
        )

    with m2:
        st.markdown(
            f'''
            <div class="metric-card">
                <div class="metric-title">Discount</div>
                <div class="metric-value">{money(discount_amount)}</div>
            </div>
            ''',
            unsafe_allow_html=True
        )

    with m3:
        st.markdown(
            f'''
            <div class="metric-card">
                <div class="metric-title">Tax</div>
                <div class="metric-value">{money(tax_amount)}</div>
            </div>
            ''',
            unsafe_allow_html=True
        )

    with m4:
        st.markdown(
            f'''
            <div class="metric-card">
                <div class="metric-title">Balance Due</div>
                <div class="metric-value">{money(balance_due)}</div>
            </div>
            ''',
            unsafe_allow_html=True
        )

    notes = st.text_area(
        "Notes / Terms and Conditions",
        "Payment is due by the due date. Thank you for your business."
    )

    st.markdown('</div>', unsafe_allow_html=True)

    invoice_data = {
        "business_name": business_name,
        "business_phone": business_phone,
        "business_email": business_email,
        "business_address": business_address,
        "invoice_no": invoice_no,
        "invoice_date": str(invoice_date),
        "due_date": str(due_date),
        "status": status,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "customer_email": customer_email,
        "customer_address": customer_address,
        "items": items_df.to_dict(orient="records"),
        "subtotal": subtotal,
        "discount_percent": discount_percent,
        "discount_amount": discount_amount,
        "tax_percent": tax_percent,
        "tax_amount": tax_amount,
        "grand_total": grand_total,
        "paid_amount": paid_amount,
        "balance_due": balance_due,
        "notes": notes,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    pdf_file = create_pdf(invoice_data)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("💾 Save Invoice", use_container_width=True):
            if not customer_name.strip():
                st.error("Please enter customer name before saving.")

            elif len(items_df) == 0 or subtotal <= 0:
                st.error("Please enter at least one valid item.")

            else:
                records = load_records()
                existing_numbers = [r["invoice_no"] for r in records]

                if invoice_no in existing_numbers:
                    st.error("This invoice number already exists. Please use a different invoice number.")

                else:
                    records.append(invoice_data)
                    save_records(records)
                    st.success("Invoice saved successfully!")

    with col2:
        st.download_button(
            "📄 Download PDF",
            data=pdf_file,
            file_name=f"{invoice_no}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    with col3:
        excel_buffer = BytesIO()

        export_df = pd.DataFrame([{
            "Invoice No": invoice_no,
            "Date": str(invoice_date),
            "Due Date": str(due_date),
            "Customer": customer_name,
            "Subtotal": subtotal,
            "Discount": discount_amount,
            "Tax": tax_amount,
            "Grand Total": grand_total,
            "Paid": paid_amount,
            "Balance Due": balance_due,
            "Status": status
        }])

        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            export_df.to_excel(writer, index=False, sheet_name="Invoice Summary")
            items_df.to_excel(writer, index=False, sheet_name="Items")

        st.download_button(
            "📊 Download Excel",
            data=excel_buffer.getvalue(),
            file_name=f"{invoice_no}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with col4:
        if st.button("🖨️ Print Receipt", use_container_width=True):
            st.session_state["show_print_receipt"] = True

    if st.session_state.get("show_print_receipt", False):
        st.markdown("### Printable Receipt Preview")

        receipt_html = create_print_receipt_html(invoice_data)

        components.html(
            receipt_html,
            height=900,
            scrolling=True
        )


# =========================
# INVOICE HISTORY PAGE
# =========================
elif page == "Invoice History":

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Invoice History")

    if not records:
        st.markdown(
            '<div class="warning-box">No invoice record found yet.</div>',
            unsafe_allow_html=True
        )

    else:
        history_df = pd.DataFrame(records)

        display_df = history_df[[
            "invoice_no",
            "invoice_date",
            "due_date",
            "customer_name",
            "grand_total",
            "paid_amount",
            "balance_due",
            "status",
            "created_at"
        ]].copy()

        display_df.columns = [
            "Invoice No",
            "Invoice Date",
            "Due Date",
            "Customer",
            "Grand Total",
            "Paid Amount",
            "Balance Due",
            "Status",
            "Created At"
        ]

        search = st.text_input("Search by invoice number or customer name")

        if search:
            display_df = display_df[
                display_df["Invoice No"].astype(str).str.contains(search, case=False, na=False)
                |
                display_df["Customer"].astype(str).str.contains(search, case=False, na=False)
            ]

        st.dataframe(display_df, use_container_width=True)

        excel_buffer = BytesIO()
        display_df.to_excel(excel_buffer, index=False)

        st.download_button(
            "Download All Records as Excel",
            data=excel_buffer.getvalue(),
            file_name="all_invoice_records.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        invoice_options = [r["invoice_no"] for r in records]

        selected_invoice = st.selectbox(
            "Select Invoice to Download Again",
            invoice_options
        )

        selected_data = next(
            (r for r in records if r["invoice_no"] == selected_invoice),
            None
        )

        if selected_data:
            selected_pdf = create_pdf(selected_data)

            st.download_button(
                "Download Selected Invoice PDF",
                data=selected_pdf,
                file_name=f"{selected_invoice}.pdf",
                mime="application/pdf"
            )

            if st.button("🖨️ Print Selected Invoice"):
                selected_receipt_html = create_print_receipt_html(selected_data)

                components.html(
                    selected_receipt_html,
                    height=900,
                    scrolling=True
                )

        if st.button("Delete All Invoice Records"):
            save_records([])
            st.success("All records deleted. Refresh the app.")

    st.markdown('</div>', unsafe_allow_html=True)


# =========================
# DASHBOARD PAGE
# =========================
elif page == "Dashboard":

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Business Dashboard")

    if not records:
        st.warning("No data available. Create invoices first.")

    else:
        df = pd.DataFrame(records)

        total_invoices = len(df)
        total_sales = df["grand_total"].sum()
        total_paid = df["paid_amount"].sum()
        total_due = df["balance_due"].sum()

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Total Invoices", total_invoices)
        c2.metric("Total Sales", money(total_sales))
        c3.metric("Total Paid", money(total_paid))
        c4.metric("Total Due", money(total_due))

        st.markdown("### Status Summary")
        status_count = df["status"].value_counts()
        st.bar_chart(status_count)

        st.markdown("### Sales by Customer")
        customer_sales = (
            df.groupby("customer_name")["grand_total"]
            .sum()
            .sort_values(ascending=False)
        )
        st.bar_chart(customer_sales)

    st.markdown('</div>', unsafe_allow_html=True)


# =========================
# HOW TO USE PAGE
# =========================
elif page == "How to Use":

    st.markdown('<div class="section-card">', unsafe_allow_html=True)

    st.subheader("How to Use This Invoice App")

    st.markdown("""
    1. Open **Create Invoice** page.
    2. Enter your business information.
    3. Enter customer information.
    4. Add items/services in the editable table.
    5. Add tax, discount, and paid amount.
    6. Click **Save Invoice** to save the record.
    7. Click **Download PDF** to download the printable invoice.
    8. Click **Print Receipt** to print the receipt directly.
    9. Open **Invoice History** to view previous invoices.
    10. Open **Dashboard** to see total sales, paid amount, and remaining dues.
    """)

    st.markdown("### Required Libraries")

    st.code(
        "pip install streamlit pandas reportlab openpyxl",
        language="bash"
    )

    st.markdown("### Run Command")

    st.code(
        "streamlit run advanced_invoice_app.py",
        language="bash"
    )

    st.markdown('</div>', unsafe_allow_html=True)