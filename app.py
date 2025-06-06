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

# 🧠 Guest extraction logic based on your CRM format
def extract_guests(file):
    guests = []
    with pdfplumber.open(file) as pdf:
        all_lines = []
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_lines += text.splitlines()

    for i in range(len(all_lines)):
        line = all_lines[i]
        if "Not Arrived" in line and "," in line:
            try:
                name_raw = line.split("Not Arrived")[0].strip()
                if "," not in name_raw:
                    continue  # skip malformed names
                last_name, first_name = map(str.strip, name_raw.split(",", 1))

                # Get next non-empty lines for city and date
                city = next((l.strip() for l in all_lines[i+1:i+4] if l.strip()), "Unknown")
                check_in = next((l.strip() for l in all_lines[i+2:i+5] if "/" in l), "00/00/0000")

                guests.append({
                    "display_name": f"{last_name}, {first_name}",
                    "last_name": last_name,
                    "name": first_name,
                    "city": city,
                    "check_in": check_in,
                    "nights": "3",
                    "phone": "N/A"
                })
            except Exception as e:
                print(f"Error parsing guest at line {i}: {e}")
                continue

    return guests


# ✍️ Fill a registration card
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

# 💾 Individual download button
def render_pdf_buttons(pdf_bytes, filename):
    b64 = base64.b64encode(pdf_bytes.read()).decode('utf-8')
    pdf_bytes.seek(0)
    return f"""
    <a href="data:application/pdf;base64,{b64}" download="{filename}">
        <button style='margin-right:10px;'>📥 Download</button>
    </a>
    """

# 📄 Merge all guest PDFs
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

# 🚀 Main app logic
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

        # 📎 Merged PDF Section
        if all_pdfs:
            st.markdown("### 🗂️ Merged Registration Cards PDF")

            merged_pdf = generate_merged_pdf(all_pdfs)
            merged_bytes = merged_pdf.read()

            # 📥 Download merged
            st.download_button(
                "📄 Download All as Single PDF",
                data=merged_bytes,
                file_name="All_RegCards.pdf",
                mime="application/pdf"
            )

            # 👁️ Preview merged
            b64_preview = base64.b64encode(merged_bytes).decode("utf-8")
            st.markdown(
                f'<iframe src="data:application/pdf;base64,{b64_preview}" width="100%" height="600px"></iframe>',
                unsafe_allow_html=True
            )
