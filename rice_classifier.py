import streamlit as st
from fpdf import FPDF
import google.generativeai as genai
from PIL import Image
import io
import sqlite3
import tempfile
import pandas as pd
import os
import pyttsx3
# === CONFIGURE GEMINI ===
genai.configure(api_key="AIzaSyCg14GiB2Q7KcgZMpvZkIncHwxbW1lQt3A")

model = genai.GenerativeModel("gemini-1.5-flash")
tamil_labels = {
    "Rice Type": "அரிசி வகை",
    "Calories": "கலோரி",
    "Protein": "(புரதம்)",
    "Description": "விவரம்"
}

#===============DB Config

#===============DB Config END

# === Nutritional Info (converted from JS) ===
nutritional_data = {
    "arborio": {"calories": 356, "protein": 7.1, "description": "Arborio rice... creamy texture, perfect for risotto."},
    "basmati": {"calories": 350, "protein": 8.8, "description": "Basmati... fragrance and delicate flavor."},
    "dehraduni": {"calories": 345, "protein": 8.5, "description": "Dehraduni rice... famous for aroma."},
    "ipsala": {"calories": 360, "protein": 7.5, "description": "Ipsala... versatile, used in pilafs and soups."},
    "jasmine": {"calories": 355, "protein": 7.0, "description": "Jasmine... aromatic, pandan/popcorn scent."},
    "karacadag": {"calories": 345, "protein": 8.2, "description": "Karacadag... nutty flavor, firm texture."},
    "sonamasuri": {"calories": 362, "protein": 7.8, "description": "Sona Masuri... lightweight, daily meals in South India."},
    "ponni": {"calories": 358, "protein": 7.2, "description": "Ponni... soft texture, South Indian dishes."},
    "mattarice": {"calories": 340, "protein": 8.0, "description": "Matta Rice... earthy flavor, reddish-brown color."},
    "ambemohar": {"calories": 355, "protein": 7.5, "description": "Ambemohar... aroma of mango blossoms."},
    "kitchadi samba": {"calories": 360, "protein": 7.6, "description": "Kitchadi Samba is a traditional rice in Tamil Nadu used for biryani and meals."},
     "samba": {"calories": 406, "protein": 9.1, "description": " Samba is a short-grain aromatic rice used in Tamil Nadu ."},
    "seeraga samba": {"calories": 356, "protein": 8.1, "description": "Seeraga Samba is a short-grain aromatic rice used in Tamil Nadu biryanis."},
}


def generate_detailed_pdf_text(rice_type):
    prompt = f"""
    Provide a detailed report (at least 30 unique points) about the rice type "{rice_type}".
    Include history, geography, health benefits, cooking methods, variations, nutritional benefits, agriculture facts, and common misconceptions.
    Make the output suitable for PDF layout.
    """
    response = st.session_state["gemini"].generate_content(prompt)
    return response.text.strip()

def get_nutritional_info(rice_type: str):
    key = rice_type.lower().replace(" ", "").replace("-", "")
    if key in nutritional_data:
        return nutritional_data[key]
    for k in nutritional_data:
        if key in k or k in key:
            return nutritional_data[k]
    return {"calories": 350, "protein": 8, "description": "General nutritional information. Exact values may vary."}

# === Gemini image detection ===
def detect_rice_type(image: Image.Image) -> str:
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    byte_data = buffered.getvalue()

    prompt = """
    You are a rice grain classifier. Based on the image, identify the rice grain type. If it is not a rice grain, respond with:
    'Unclassified: It looks like [object name]'
    """
    response = model.generate_content([prompt, image])
    return response.text.strip()

# === PDF Generation ===
def generate_pdf(rice_type, info):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt="Rice Grain Analysis Report", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Rice Type: {rice_type}", ln=True)
    pdf.cell(200, 10, txt=f"Calories: {info['calories']} kcal", ln=True)
    pdf.cell(200, 10, txt=f"Protein: {info['protein']} g", ln=True)
    pdf.multi_cell(0, 10, txt=f"Description: {info['description']}")
    

    # Use temporary file that works on all OSes
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_file.name)
    return temp_file.name

# === STREAMLIT UI ===
#st.title("🍚 AI-Powered Rice Grain Classifier")
st.set_page_config(page_title="Smart Rice Analyzer", page_icon="🍚", layout="centered")

with st.container():
    st.markdown("<h1 style='text-align: center; color: #4CAF50;'>🍚 AI-Powered Rice Classifier</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Upload a rice grain image to identify the variety and get nutritional insights instantly</p>", unsafe_allow_html=True)

    uploaded = st.file_uploader("📷 Upload Rice Image", type=["jpg", "jpeg", "png"])

if uploaded:
    image = Image.open(uploaded)

    # Dark Mode CSS
    dark_style = """
    <style>
    body {
        background-color: #0f1116;
        color: #f0f0f0;
    }
    h1, h2, h3, h4, h5, h6, p, div {
        color: #f0f0f0 !important;
    }
    .reportview-container {
        background: #0f1116;
    }
    .sidebar .sidebar-content {
        background: #1e1e1e;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
    }
    .stDownloadButton>button {
        background-color: #2e8b57;
        color: white;
    }
    .stTabs [role="tab"] {
        background-color: #1e1e1e;
        color: #ddd;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4CAF50;
        color: white;
    }
    </style>
    """
    st.markdown(dark_style, unsafe_allow_html=True)

    #st.image(image, caption="Uploaded Rice Image", use_column_width=True)
    st.image(image, caption="Uploaded Rice Image", use_container_width=True)

    if st.button("Analyze"):
        with st.spinner("Analyzing image..."):
            rice_type = detect_rice_type(image)

        if rice_type.lower().startswith("unclassified"):
            st.error(f"❌ I don't classify this. {rice_type}")
        else:
            info = get_nutritional_info(rice_type)
            st.markdown(f"✅ <b>Detected Rice Type:</b> {rice_type}", unsafe_allow_html=True)
            st.toast("🎉 Analysis completed and saved!", icon="🍀")

            # Nutritional Info Card
            st.markdown(f"""
            <div style="background-color: #1e1e1e; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 10px rgba(255,255,255,0.1); color: #f0f0f0;">
                <h4 style='color:#90EE90;'>🧪 Nutritional Details</h4>
                <b>Rice Type:</b> {rice_type}<br>
                <b>Calories:</b> {info['calories']} kcal<br>
                <b>Protein:</b> {info['protein']} g<br>
                <b>Description:</b> {info['description']}
            </div>
            """, unsafe_allow_html=True)

            # PDF Download
            pdf_path = generate_pdf(rice_type, info)
            with open(pdf_path, "rb") as file:
                st.download_button(label="📄 Download PDF Report", data=file, file_name="rice_report.pdf")

            # Presentation Mode with Tabs
            with st.expander("📽️ Presentation Mode"):
                tabs = st.tabs(["🌍 English", "🇮🇳 தமிழ்"])

                with tabs[0]:
                    st.subheader("🌾 Rice Grain Analysis Summary")
                    st.image(image, use_column_width=True)
                    st.markdown(f"**Rice Type**: {rice_type}")
                    st.markdown(f"**Calories**: {info['calories']} kcal")
                    st.markdown(f"**Protein**: {info['protein']} g")
                    st.markdown(f"**Description**: {info['description']}")

                with tabs[1]:
                    st.subheader("🌾 அரிசி வகை பகுப்பாய்வு")
                    st.image(image, use_column_width=True)
                    st.markdown(f"**{tamil_labels['Rice Type']}**: {rice_type}")
                    st.markdown(f"**{tamil_labels['Calories']}**: {info['calories']} கலோரி")
                    st.markdown(f"**{tamil_labels['Protein']}**: {info['protein']} கிராம்")
                    st.markdown(f"**{tamil_labels['Description']}**: {info['description']}")

            # Save Result to CSV
            results_file = "rice_analysis_results.csv"
            new_data = {
                "rice_type": rice_type,
                "calories": info['calories'],
                "protein": info['protein'],
                "description": info['description']
            }
            df = pd.DataFrame([new_data])
            if os.path.exists(results_file):
                df.to_csv(results_file, mode='a', index=False, header=False)
            else:
                df.to_csv(results_file, index=False)

            #Show Recent Results in Sidebar
            if os.path.exists(results_file):
                st.sidebar.title("📊 Previous Results")
                hist_df = pd.read_csv(results_file)
                st.sidebar.dataframe(hist_df.tail(5), use_container_width=True)