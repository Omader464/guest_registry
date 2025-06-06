import streamlit as st
import pdfplumber
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import base64
import re

st.set_page_config(page_title="Reg Card Generator", layout="wide")
st.title("📋 Guest Registration Card Generator")

uploaded_file = st.file_uploader("Upload CRM Guest Report (PDF)", type=["pdf"])

TEMPLATE_PATH = "Reg Card Palacio copy.pdf"

# Extract guest blocks using regex
def extract_guests(file):
    guests = []
    with pdfplumber.open(file) as pdf:
        text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
        entries = re.findall(r"([A-Z\\-']+,\\s[A-Z\\s]+)\\s+Not Arrived.*?\\n(.*?)\\n(\\d{2}/\\d{2}/\\d{4})", text)
        for entry in entries:
            full_name, city, checkin = entry
            last, first = map(str.strip, full_name.split(","))
            guests.append({
                "display_name": f"{last}, {first}",
                "last_name": last,
                "name": first,
                "city": city.strip(),
                "check_in": checkin,
                "nights": "3",
                "phone": "N/A"
            })
    return guests

# Create filled registration card PDF
def fill_pdf(template_path, guest_data):
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

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
    template_pdf = PdfReader(open(template_path, "rb"))
    output = PdfWriter()
    page = template_pdf.pages[0]
    page.merge_page(new_pdf.pages[0])
    output.add_page(page)

    result = BytesIO()
    output.write(result)
    result.seek(0)
    return result

# Download button (individual)
def render_pdf_buttons(pdf_bytes, filename):
    b64 = base64.b64encode(pdf_bytes.read()).decode('utf-8')
    pdf_bytes.seek(0)
    return f"""
    <a href="data:application/pdf;base64,{b64}" download="{filename}">
        <button style='margin-right:10px;'>📥 Download</button>
    </a>
    """

# Merge all PDFs into one
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

# === MAIN APP LOGIC ===
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

        # Merged PDF output section
        # Merged PDF output section
        if all_pdfs:
            st.markdown("### 🗂️ Merged Registration Cards PDF")
        
            # Generate and read merged PDF once
            merged_pdf = generate_merged_pdf(all_pdfs)
            merged_bytes = merged_pdf.read()
        
            # Download
            st.download_button(
                "📄 Download All as Single PDF",
                data=merged_bytes,
                file_name="All_RegCards.pdf",
                mime="application/pdf"
            )
        
            # Preview
            b64_preview = base64.b64encode(merged_bytes).decode("utf-8")
            st.markdown(
                f'<iframe src="data:applicat
        
                    
                                
