import streamlit as st
import pdfplumber
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import base64

st.set_page_config(page_title="Reg Card Generator", layout="wide")
st.title("📋 Guest Registration Card Generator")

uploaded_file = st.file_uploader("Upload CRM Guest Report (PDF)", type=["pdf"])

TEMPLATE_PATH = "Reg Card Palacio copy.pdf"

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
                    guests.append({
                        "display_name": name,
                        "name": name.split(",")[-1].strip(),
                        "last_name": name.split(",")[0].strip(),
                        "city": city_line,
                        "check_in": checkin_date,
                        "nights": "3",
                        "phone": "N/A"
                    })
                except Exception:
                    continue
    return guests

def fill_pdf(template_path, guest_data):
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    # Adjusted vertical coordinates
    can.drawString(130, 700, guest_data['last_name'])
    can.drawString(130, 680, guest_data['name'])
    can.drawString(130, 660, guest_data['phone'])
    can.drawString(130, 640, "00901")
    can.drawString(130, 620, "United States - US")
    can.drawString(130, 600, guest_data['name'].lower() + "@email.com")
    can.drawString(130, 580, guest_data['check_in'])
    can.drawString(250, 580, "06/08/25")
    can.drawString(130, 560, guest_data['nights'])

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

def render_pdf_buttons(guest_pdf, filename):
    b64_pdf = base64.b64encode(guest_pdf.read()).decode('utf-8')
    guest_pdf.seek(0)
    return f"""
    <a href="data:application/pdf;base64,{b64_pdf}" download="{filename}">
        <button style='margin-right:10px;'>📥 Download</button>
    </a>
    <iframe id="{filename}" src="data:application/pdf;base64,{b64_pdf}" width="0" height="0"></iframe>
    <button onclick="document.getElementById('{filename}').contentWindow.print()">🖨️ Print</button>
    """

def render_bulk_print_button(all_pdfs):
    merger = PdfMerger()
    for pdf in all_pdfs:
        merger.append(pdf)
    output = BytesIO()
    merger.write(output)
    output.seek(0)
    b64_merged = base64.b64encode(output.read()).decode('utf-8')
    return f"""
    <iframe id="bulkPrintFrame" src="data:application/pdf;base64,{b64_merged}" width="0" height="0"></iframe>
    <button onclick="document.getElementById('bulkPrintFrame').contentWindow.print()">🖨️ Bulk Print All</button>
    """

if uploaded_file:
    guests = extract_guests(uploaded_file)
    if not guests:
        st.warning("No guests found in the uploaded file.")
    else:
        st.success(f"Found {len(guests)} guests. Generating registration cards...")
        all_pdfs = []
        for guest in guests:
            pdf_bytes = fill_pdf(TEMPLATE_PATH, guest)
            all_pdfs.append(BytesIO(pdf_bytes.read()))
            with st.expander(f"🧾 {guest['display_name']}"):
                st.markdown(render_pdf_buttons(pdf_bytes, f"RegCard_{guest['last_name']}.pdf"), unsafe_allow_html=True)

        # Bulk print button at the end
        st.markdown("---")
        st.markdown(render_bulk_print_button(all_pdfs), unsafe_allow_html=True)
