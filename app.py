import streamlit as st
import pdfplumber
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import base64

st.set_page_config(page_title="Reg Card Generator", layout="wide")
st.title("📋 Guest Registration Card Generator")

# Upload CRM report
uploaded_file = st.file_uploader("Upload CRM Guest Report (PDF)", type=["pdf"])

TEMPLATE_PATH = "Reg Card Palacio copy.pdf"

# Helper: Extract guests
def extract_guests(file):
    guests = []
    with pdfplumber.open(file) as pdf:
        text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if "Not Arrived" in line:
                try:
                    name = line.split(" Not Arrived")[0].strip()
                    city_line = lines[i+1].strip()
                    checkin_date = lines[i+2].strip()
                    phone = line.split()[-1].strip()
                    guests.append({
                        "display_name": name,
                        "name": name.split(",")[-1].strip(),
                        "last_name": name.split(",")[0].strip(),
                        "city": city_line,
                        "check_in": checkin_date,
                        "nights": "3",
                        "phone": phone
                    })
                except Exception:
                    continue
    return guests

# Helper: Fill reg card
def fill_pdf(template_path, guest_data):
    packet = BytesIO()
    can.drawString(130, 680, guest_data['last_name'])        # Last Name
    can.drawString(130, 660, guest_data['name'])             # Name
    can.drawString(130, 640, guest_data['phone'])            # Tel.
    can.drawString(130, 620, "00901")                        # Zip Code
    can.drawString(130, 600, "United States - US")           # Country
    can.drawString(130, 580, guest_data['name'].lower() + "@email.com")  # Email
    can.drawString(130, 560, guest_data['check_in'])         # Check In
    can.drawString(250, 560, "06/08/25")                     # Check Out
    can.drawString(130, 540, guest_data['nights'])           # N Nights
    can.save()
    packet.seek(0)
    new_pdf = PdfReader(packet)
    existing_pdf = PdfReader(open(template_path, "rb"))
    output = PdfWriter()
    page = existing_pdf.pages[0]
    page.merge_page(new_pdf.pages[0])
    output.add_page(page)
    result = BytesIO()
    output.write(result)
    result.seek(0)
    return result

# Helper: Make download + print button
def render_pdf_download_button(guest_pdf, filename):
    b64_pdf = base64.b64encode(guest_pdf.read()).decode('utf-8')
    guest_pdf.seek(0)
    download_button = f"""
    <a href="data:application/pdf;base64,{b64_pdf}" download="{filename}" target="_blank">
        <button style='margin-right:10px;'>📥 Download</button>
    </a>
    <a href="data:application/pdf;base64,{b64_pdf}" target="_blank" onclick="window.print();">
        <button>🖨️ Print</button>
    </a>
    """
    return download_button

if uploaded_file:
    guests = extract_guests(uploaded_file)
    if not guests:
        st.warning("No guests found in the uploaded file.")
    else:
        st.success(f"Found {len(guests)} guests. Generating registration cards...")
        for guest in guests:
            pdf_bytes = fill_pdf(TEMPLATE_PATH, guest)
            with st.expander(f"🧾 {guest['display_name']}"):
                st.markdown(render_pdf_download_button(pdf_bytes, f"RegCard_{guest['last_name']}.pdf"), unsafe_allow_html=True)
