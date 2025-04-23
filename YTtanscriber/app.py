# ##Final code
# import streamlit as st
# from dotenv import load_dotenv
# import re
# from fpdf import FPDF
# import base64
# from textblob import TextBlob
# from gtts import gTTS
# from io import BytesIO
# from bs4 import BeautifulSoup
# load_dotenv() ##load all the nevironment variables
# import os
# import google.generativeai as genai

# from youtube_transcript_api import YouTubeTranscriptApi

# genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# base_prompt="""You are Yotube video summarizer. You will be taking the transcript text
# and summarizing the entire video and providing the important summary in points
# within 250 words. Please provide the summary of the text given here:  """


# ## getting the transcript data from yt videos
# def extract_transcript_details(youtube_video_url):
#     try:
#         video_id = youtube_video_url.split("=")[1]
#         transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
#         transcript = " ".join([item["text"] for item in transcript_data])
#         return transcript
#     except Exception as e:
#         raise e

    
# # Function to generate content using Google Gemini
# def generate_gemini_content(transcript_text, prompt, length):
#     model = genai.GenerativeModel("gemini-pro")
#     prompt_with_length = prompt.format(length=length)
#     response = model.generate_content(prompt_with_length + transcript_text)
#     return response.text

# # Function to highlight user-defined words
# def highlight_words(text, words_to_highlight):
#     highlighted_text = text
#     for word in words_to_highlight:
#         highlighted_text = re.sub(
#             re.escape(word),
#             lambda match: f'<span style="color: red; font-weight: bold;">{match.group(0)}</span>',
#             highlighted_text,
#             flags=re.IGNORECASE
#         )
#     return highlighted_text


# # Function to determine summary length
# def determine_summary_length(transcript_text, length_choice):
#     word_count = len(transcript_text.split())
#     if length_choice == "Short":
#         return max(50, word_count // 10)
#     elif length_choice == "Medium":
#         return max(100, word_count // 5)
#     elif length_choice == "Long":
#         return max(200, word_count // 2)

# # Function to analyze sentiment
# def analyze_sentiment(text):
#     sentiment = TextBlob(text).sentiment
#     polarity = sentiment.polarity
#     subjectivity = sentiment.subjectivity
#     if -0.1 <= polarity <= 0.1:
#         sentiment_label = "Neutral"
#     elif polarity > 0.1:
#         sentiment_label = "Positive"
#     else:
#         sentiment_label = "Negative"
#     return sentiment_label, polarity, subjectivity

# # Function to generate text-to-speech audio
# def text_to_speech(summary_text):
#     # Remove HTML tags and extract only text
#     cleaned_text = BeautifulSoup(summary_text, "html.parser").get_text()
    
#     # Remove non-alphanumeric characters except spaces
#     cleaned_text = re.sub(r'[^A-Za-z0-9\s]', '', cleaned_text)

#     # Convert text to speech
#     tts = gTTS(cleaned_text)
#     audio_buffer = BytesIO()
#     tts.write_to_fp(audio_buffer)
#     audio_buffer.seek(0)
#     return audio_buffer

# # Function to process multiple videos
# def process_videos(video_links, summary_length, highlight_words_input):
#     video_links = [link.strip() for link in video_links.split(",")]
#     results = []
#     for link in video_links:
#         try:
#             transcript_text = extract_transcript_details(link)
#             desired_words = determine_summary_length(transcript_text, summary_length)
#             summary = generate_gemini_content(transcript_text, base_prompt, desired_words)
#             if highlight_words_input:
#                 words_to_highlight = [word.strip() for word in highlight_words_input.split(",")]
#                 summary = highlight_words(summary, words_to_highlight)
#             sentiment_label, polarity, subjectivity = analyze_sentiment(summary)
#             audio_file = text_to_speech(summary)
           
#             results.append({
#                 "link": link,
#                 "summary": summary,
#                 "sentiment": (sentiment_label, polarity, subjectivity),
#                  "audio_file": audio_file
#             })
#         except Exception as e:
#             results.append({"link": link, "error": str(e)})
#     return results

# # Streamlit interface
# st.title("🎥Video Transcript Condenser System")
# youtube_links = st.text_input("Enter YouTube Video Links (comma separated):")
# summary_length = st.selectbox("Select Summary Length:", ["Short", "Medium", "Long"])
# highlight_words_input = st.text_input("Enter words to highlight (comma separated):")

# if st.button("🔍Get Notes for All Videos"):
#     try:
#         results = process_videos(youtube_links, summary_length, highlight_words_input)
#         for result in results:
#             st.markdown("---")
           
#             if "error" in result:
#                 st.error(f"Error: {result['error']}")
#             else:
#                 st.markdown("## Notes:")
#                 st.markdown(result["summary"], unsafe_allow_html=True)
#                 sentiment_label, polarity, subjectivity = result["sentiment"]
#                 st.markdown(f"### 📊Sentiment Analysis: {sentiment_label} (Polarity: {polarity:.2f}, Subjectivity: {subjectivity:.2f})")
#                 st.markdown("### 🎧Listen to the Summary:")
#                 st.audio(result["audio_file"], format="audio/mp3", start_time=0)
#                 audio_base64 = base64.b64encode(result["audio_file"].read()).decode()
#                 st.markdown(
#                     f'<a href="data:audio/mp3;base64,{audio_base64}" download="summary.mp3">Download Audio</a>',
#                     unsafe_allow_html=True
#                 )
#     except Exception as e:
#         st.error(f"An error occurred: {str(e)}")


import streamlit as st
from dotenv import load_dotenv
import re
import base64
from textblob import TextBlob
from gtts import gTTS
from io import BytesIO
from bs4 import BeautifulSoup
import os
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

base_prompt = """You are a YouTube video summarizer. You will take the transcript text
and summarize the entire video, providing important points within {} words.
Please provide the summary of the text given here: """

# Function to extract transcript from YouTube videos
def extract_transcript_details(youtube_video_url):
    try:
        video_id = youtube_video_url.split("=")[1]
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([item["text"] for item in transcript_data])
        return transcript
    except Exception as e:
        return None

# Function to generate content using Google Gemini
def generate_gemini_content(transcript_text, length):
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
    prompt = base_prompt.format(length)
    response = model.generate_content(prompt + transcript_text)
    return response.text if response.text else None

# Function to determine summary length
def determine_summary_length(transcript_text, length_choice):
    word_count = len(transcript_text.split())
    if length_choice == "Short":
        return max(50, word_count // 10)
    elif length_choice == "Medium":
        return max(100, word_count // 5)
    elif length_choice == "Long":
        return max(200, word_count // 2)
    return 100  # Default

# Function to highlight user-defined words
def highlight_words(text, words_to_highlight):
    highlighted_text = text
    for word in words_to_highlight:
        highlighted_text = re.sub(
            re.escape(word),
            lambda match: f'<span style="color: red; font-weight: bold;">{match.group(0)}</span>',
            highlighted_text,
            flags=re.IGNORECASE
        )
    return highlighted_text

# Function to analyze sentiment
def analyze_sentiment(text):
    sentiment = TextBlob(text).sentiment
    polarity = sentiment.polarity
    subjectivity = sentiment.subjectivity
    if -0.1 <= polarity <= 0.1:
        sentiment_label = "Neutral"
    elif polarity > 0.1:
        sentiment_label = "Positive"
    else:
        sentiment_label = "Negative"
    return sentiment_label, polarity, subjectivity

# Function to generate text-to-speech audio
def text_to_speech(summary_text):
    cleaned_text = BeautifulSoup(summary_text, "html.parser").get_text()
    cleaned_text = re.sub(r'[^A-Za-z0-9\s]', '', cleaned_text)
    tts = gTTS(cleaned_text)
    audio_buffer = BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer

# Function to generate a PDF file
def generate_pdf(summary_text):
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(180, 750, "YouTube Video Summary")
    
    c.setFont("Helvetica", 12)
    
    cleaned_text = BeautifulSoup(summary_text, "html.parser").get_text()
    lines = cleaned_text.split("\n")
    
    y_position = 720
    max_width = 500  

    for line in lines:
        if not line.strip():
            y_position -= 10
            continue

        if line.endswith(":"):  
            c.setFont("Helvetica-Bold", 12)
        else:
            c.setFont("Helvetica", 12)

        wrapped_lines = simpleSplit(line, "Helvetica", 12, max_width)

        for wrapped_line in wrapped_lines:
            if y_position < 50:  
                c.showPage()
                c.setFont("Helvetica", 12)
                y_position = 750
            c.drawString(50, y_position, wrapped_line)
            y_position -= 20  

    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer

# Function to process multiple videos
def process_videos(video_links, summary_length, highlight_words_input):
    video_links = [link.strip() for link in video_links.split(",") if link.strip()]
    results = []
    for link in video_links:
        transcript_text = extract_transcript_details(link)
        if not transcript_text:
            results.append({"link": link, "error": "Transcript could not be extracted."})
            continue
        
        desired_words = determine_summary_length(transcript_text, summary_length)
        summary = generate_gemini_content(transcript_text, desired_words)
        
        if not summary:
            results.append({"link": link, "error": "Failed to generate summary."})
            continue

        # Highlight words if specified
        if highlight_words_input:
            words_to_highlight = [word.strip() for word in highlight_words_input.split(",")]
            summary = highlight_words(summary, words_to_highlight)

        sentiment_label, polarity, subjectivity = analyze_sentiment(summary)
        audio_file = text_to_speech(summary)
        pdf_file = generate_pdf(summary)
        
        results.append({
            "link": link,
            "summary": summary,
            "sentiment": (sentiment_label, polarity, subjectivity),
            "audio_file": audio_file,
            "pdf_file": pdf_file
        })
    return results

# Streamlit interface
st.title("🎥 Video Transcript Condenser System")

# User inputs
youtube_links = st.text_area("Enter YouTube Video Links (comma separated):")
summary_length = st.selectbox("Select Summary Length:", ["Short", "Medium", "Long"])
highlight_words_input = st.text_input("Enter words to highlight (comma separated):")

# Process button
if st.button("🔍 Get Notes for All Videos"):
    st.session_state.results = process_videos(youtube_links, summary_length, highlight_words_input)

# Display results if available
if "results" in st.session_state:
    for idx, result in enumerate(st.session_state.results):
        st.markdown("---")
        
        if "error" in result:
            st.error(f"Error: {result['error']}")
        else:
            st.markdown("## Notes:")
            st.markdown(result["summary"], unsafe_allow_html=True)

            sentiment_label, polarity, subjectivity = result["sentiment"]
            st.markdown(f"### 📊 Sentiment Analysis: {sentiment_label} (Polarity: {polarity:.2f}, Subjectivity: {subjectivity:.2f})")

            st.markdown("### 🎧 Listen to the Summary:")
            st.audio(result["audio_file"], format="audio/mp3", start_time=0)

            pdf_file = result["pdf_file"]
            unique_filename = f"summary_{idx}.pdf"

            st.markdown("### 📄 Download Summary as PDF:")
            st.download_button(
                label="📥 Download Summary PDF",
                data=pdf_file,
                file_name=unique_filename,
                mime="application/pdf",
                key=f"pdf_{idx}"
            )