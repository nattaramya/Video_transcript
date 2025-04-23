
import streamlit as st
from dotenv import load_dotenv
import os
from youtube_transcript_api import YouTubeTranscriptApi
import re
from fpdf import FPDF
import base64
from textblob import TextBlob
from gtts import gTTS
from io import BytesIO
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk


nltk.download('punkt')


load_dotenv()


base_prompt = """
You are a YouTube video summarizer. You will take the transcript text
and summarize the entire video, providing the important summary in points.
Please provide the summary of the text given here in approximately {length} words:
"""



def extract_transcript_details(youtube_video_url):
    try:
        video_id = youtube_video_url.split("=")[1]
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([item["text"] for item in transcript_data])
        return transcript
    except Exception as e:
        raise e



def generate_tfidf_summary(transcript_text, summary_length):
    sentences = nltk.sent_tokenize(transcript_text)
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(sentences)
    scores = tfidf_matrix.sum(axis=1).A1
    ranked_sentences = [sentences[i] for i in scores.argsort()[-summary_length:]]
    return " ".join(ranked_sentences)



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



def determine_summary_length(transcript_text, length_choice):
    word_count = len(transcript_text.split())
    if length_choice == "Short":
        return max(50, word_count // 10)
    elif length_choice == "Medium":
        return max(100, word_count // 5)
    elif length_choice == "Long":
        return max(200, word_count // 2)



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


def generate_pdf(text, filename="transcript_summary.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    lines = text.split("\n")
    for line in lines:
        if '<span style="color: red;' in line:
            pdf.set_text_color(255, 0, 0)
            pdf.set_font("Arial", 'B', 12)
            line = re.sub(r'<span.*?>|</span>', '', line)
        else:
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, line)
    pdf_output = pdf.output(dest="S").encode("latin1")
    return base64.b64encode(pdf_output).decode("utf-8")



def download_pdf_file(pdf_base64, filename="transcript_summary.pdf"):
    download_link = f'<a href="data:application/pdf;base64,{pdf_base64}" download="{filename}">Download the Transcript Summary (PDF)</a>'
    st.markdown(download_link, unsafe_allow_html=True)


def text_to_speech(summary_text):
    cleaned_text = re.sub(r'[^A-Za-z0-9\s]', '', summary_text)
    tts = gTTS(cleaned_text)
    audio_buffer = BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer


def process_videos(video_links, summary_length, highlight_words_input):
    video_links = [link.strip() for link in video_links.split(",")]
    results = []
    for link in video_links:
        try:
            transcript_text = extract_transcript_details(link)
            desired_words = determine_summary_length(transcript_text, summary_length)
            summary = generate_tfidf_summary(transcript_text, desired_words)
            if highlight_words_input:
                words_to_highlight = [word.strip() for word in highlight_words_input.split(",")]
                summary = highlight_words(summary, words_to_highlight)
            sentiment_label, polarity, subjectivity = analyze_sentiment(summary)
            pdf_base64 = generate_pdf(summary)
            audio_file = text_to_speech(summary)
            results.append({
                "link": link,
                "summary": summary,
                "sentiment": (sentiment_label, polarity, subjectivity),
                "pdf_base64": pdf_base64,
                "audio_file": audio_file
            })
        except Exception as e:
            results.append({"link": link, "error": str(e)})
    return results


st.title("🎥Video Transcript Condenser System (Multiple Videos)")

youtube_links = st.text_input("Enter YouTube Video Links (comma separated):")
summary_length = st.selectbox("Select Summary Length:", ["Short", "Medium", "Long"])
highlight_words_input = st.text_input("Enter words to highlight (comma separated):")

if st.button("🔍Get Notes for All Videos"):
    try:
        results = process_videos(youtube_links, summary_length, highlight_words_input)
        for result in results:
            st.markdown("---")
           
            if "error" in result:
                st.error(f"Error: {result['error']}")
            else:
                st.markdown("## Notes:")
                st.markdown(result["summary"], unsafe_allow_html=True)
                sentiment_label, polarity, subjectivity = result["sentiment"]
                st.markdown(f"###📊 Sentiment Analysis: {sentiment_label} (Polarity: {polarity:.2f}, Subjectivity: {subjectivity:.2f})")
                download_pdf_file(result["📄pdf_base64"])
                st.markdown("###🎧 Listen to the Summary:")
                st.audio(result["audio_file"], format="audio/mp3", start_time=0)
                audio_base64 = base64.b64encode(result["audio_file"].read()).decode()
                st.markdown(
                    f'<a href="data:audio/mp3;base64,{audio_base64}" download="summary.mp3">Download Audio</a>',
                    unsafe_allow_html=True
                )
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
