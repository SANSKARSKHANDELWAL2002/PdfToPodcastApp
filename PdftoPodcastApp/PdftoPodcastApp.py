import fitz #PyMuPDF
import os
from gtts import gTTS
import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv

# Configure Gemini
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

#1. Extract text from PDF

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += doc.get_text()
    doc.close()
    return text

# 2. Summarize using Gemini with duration prompt only
def summarize_text_gemini(text, duration):
    if duration == "Short":
        duration_prompt = "short, podcast-friendly format in less than 400 words"
    elif duration == "Medium":
        duration_prompt = "medium-length, engaging podcast format in less than 600 words"
    else:
        duration_prompt = "detailed, podcast-friendly narrative in around 1000 words"

    prompt = f"Summarize this research paper in a {duration_prompt} spoken by a single narrator. It should be suitable for text-to-speech. Only include the spoken content by the narrator"

    # Chunk text if too big
    chunk_size = 12000
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    summaries = []
    for chunk in chunks:
        response = model.generate_content(f"{prompt}\n\n{chunk}")
        summaries.append(response.text.strip())
    return "\n\n".join(summaries)


# 3. Convert summary to speech using gTTS single audio file
def text_to_speech(text, output_path="podcast_output.mp3"):
    text = text.replace("*", "")  # remove special characters if needed
    tts = gTTS(text=text, lang='en', tld='com')
    tts.save(output_path)


# 4. Run everything
def generate_podcast_from_pdf(pdf_path, output_audio_path, duration):
    with st.spinner("Extracting text from PDF..."):
        text = extract_text_from_pdf(pdf_path)
    with st.spinner("Summarizing..."):
        summary = summarize_text_gemini(text, duration)
    with st.spinner("Generating podcast audio..."):
        text_to_speech(summary, output_audio_path)
    st.success(f"Podcast saved as {output_audio_path}")
    return output_audio_path, summary


# Streamlit app
st.title("PDF to Podcast Generator")

uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
duration_option = st.radio("Select podcast duration:", ["Short", "Medium", "Long"])

if uploaded_file is not None:
    temp_pdf_path = "temp_uploaded.pdf"
    with open(temp_pdf_path, "wb") as f:
        f.write(uploaded_file.read())

    if st.button("Generate Podcast"):
        output_audio_file = "generated_podcast.mp3"
        output_audio_path, transcript = generate_podcast_from_pdf(
            temp_pdf_path, output_audio_file, duration_option
        )

        with open(output_audio_path, "rb") as audio_file:
            st.audio(audio_file.read(), format="audio/mp3")

        st.subheader("Transcript")
        st.text_area("Here's the podcast transcript:", transcript, height=300)
