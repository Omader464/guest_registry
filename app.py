import streamlit as st
import pdfplumber
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import base64
from datetime import datetime, timedelta
import re

st.set_page_config(page_title="Reg Card Generator", layout="wide")
st.title("📋 Guest Registration Card Generator")

uploaded_file = st.file_uploader("Upload CRM Guest Report (PDF)", type=["pdf"])
TEMPLATE_PATH = "Reg Card Palacio copy.pdf"

# 🧠 Extract guests using structure matching
def extract_guests(file):
    guests = []
    with pdfplumber.open(file) as pdf:
        lines = []
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines += text.splitlines()

    for i, line in enumerate(lines):
        if "Not Arrived" in line and "," in line:
            try:
                name_raw = line.split("Not Arrived")[0].strip()
                last_name, first_name = map(str.strip, name_raw.split(",", 1))
                city = lines[i + 1].strip()
                checkin = lines[i + 2].strip()
                email_line = next((l for l in lines[i:i+8] if "@" in l), None)

                guests.append({
                    "display_name": f"{last_name}, {first_name}",
                    "last_name": last_name,
                    "name": first_name,
                    "city": city,
                    "check_in": checkin,
                    "email": email_line.strip() if email_line else f"{first_name.lower()}@email.com",
                    "nights": "3",
                    "phone": "N/A"
                })
            except Exception:
                continue
    return guests

# ✍️ Fill a single reg card
def fill_pdf(template_path, guest_data):
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    # Correct vertical alignment (recalibrated for better appearance)
    can.drawString(130, 700, guest_data['last_name'])                     # Last Name
    can.drawString(130, 680, guest_data['name'])                          # First Name
    can.drawString(130, 660, guest_data['phone'])                         # Tel.
    can.drawString(130, 640, "00901")                                     # Zip
    can.drawString(130, 620, "United States - US")                        # Country
    can.drawString(130, 600, guest_data['email'])                         # Email

    # Dates
    try:
        checkin = datetime.strptime(guest_data['check_in'], "%m/%d/%Y")
        checkout = checkin + timedelta(days=int(guest_data['nights']))
        can.drawString(130, 580, checkin.strftime("%m/%d/%y"))            # Check In
        can.drawString(250, 580, checkout.strftime("%m/%d/%y"))           # Check Out
    except:
        can.drawString(130, 580, "00/00/25")
        can.drawString(250, 580, "00/00/00")

    can.drawString(130, 560, guest_data['nights'])                        # Nights

    can.save()
    packet.seek(0)

    new_pdf = PdfReader(packet)
    template_pdf = PdfReader(open(template_path, "rb"))
    output = PdfWriter()
    page = template_pdf.pages[0]
    page.merge_page(new_pdf.pages[0])
    output.add_page(page)

    result = BytesIO()
    output.write(result)
    result.seek(0)
    return result

# 🧾 Individual button
def render_pdf_buttons(pdf_bytes, filename):
    b64 = base64.b64encode(pdf_bytes.read()).decode('utf-8')
    pdf_bytes.seek(0)
    return f"""
    <a href="data:application/pdf;base64,{b64}" download="{filename}">
        <button style='margin-right:10px;'>📥 Download</button>
    </a>
    """

# 📎 Merge PDF pages
def generate_merged_pdf(pdf_list):
    merger = PdfMerger()
    for pdf in pdf_list:
        pdf.seek(0)
        merger.append(pdf)
    output = BytesIO()
    merger.write(output)
    merger.close()
    output.seek(0)
    return output

# 🚀 Main
if uploaded_file:
    guests = extract_guests(uploaded_file)

    if not guests:
        st.warning("No valid guests found.")
    else:
        st.success(f"Found {len(guests)} guests. Generating cards...")
        all_pdfs = []

        for guest in guests:
            pdf = fill_pdf(TEMPLATE_PATH, guest)
            all_pdfs.append(BytesIO(pdf.read()))
            with st.expander(f"🧾 {guest['display_name']}"):
                st.markdown(render_pdf_buttons(pdf, f"RegCard_{guest['last_name']}.pdf"), unsafe_allow_html=True)

        # 🗂️ Merged Output
        if all_pdfs:
            st.markdown("### 🗂️ Merged Registration Cards PDF")
            merged_pdf = generate_merged_pdf(all_pdfs)
            merged_bytes = merged_pdf.read()

            st.download_button(
                "📄 Download All as Single PDF",
                data=merged_bytes,
                file_name="All_RegCards.pdf",
                mime="application/pdf"
            )

            # Preview
            b64_preview = base64.b64encode(merged_bytes).decode("utf-8")
            st.markdown(
                f'<iframe src="data:application/pdf;base64,{b64_preview}" width="100%" height="600px"></iframe>',
                unsafe_allow_html=True
            )
