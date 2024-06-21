from concurrent.futures import ThreadPoolExecutor
import math
import os
from pytube import YouTube
from datetime import datetime
import moviepy.editor as mp
import speech_recognition as sr
from flask import Flask, request, render_template, send_from_directory, jsonify
import textwrap
from groq import Groq

app = Flask(__name__)

api_key = "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"
client = Groq(api_key=api_key)

# Function to download audio from YouTube URL
def download_audio(youtube_url):
    try:
        yt = YouTube(youtube_url)
        stream = yt.streams.filter(only_audio=True).first()

        if stream is None:
            return None

        output_file = stream.download(filename='audio.webm')
        return output_file

    except Exception as e:
        print(f"An error occurred during download: {e}")
        return None

# Function for parallel transcription of audio chunks
def transcribe_chunk(audio_data):
    try:
        recognizer = sr.Recognizer()
        text = recognizer.recognize_google(audio_data)
        return text
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return None

# Function to transcribe audio file
def transcribe_audio(audio_file, chunk_length=30, num_threads=4):
    try:
        audio = mp.AudioFileClip(audio_file)
        wav_file = audio_file.replace(".webm", ".wav")
        audio.write_audiofile(wav_file)

        recognizer = sr.Recognizer()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        transcript_filename = f'transcript_{timestamp}.txt'

        with open(transcript_filename, 'a') as file:
            audio_duration = audio.duration
            chunk_count = math.ceil(audio_duration / chunk_length)

            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = []
                for i in range(chunk_count):
                    start = i * chunk_length
                    end = min(audio_duration, (i + 1) * chunk_length)
                    with sr.AudioFile(wav_file) as source:
                        audio_data = recognizer.record(source, offset=start, duration=end - start)
                        futures.append(executor.submit(transcribe_chunk, audio_data))

                for future in futures:
                    text = future.result()
                    if text:
                        file.write(text + '\n')

        return transcript_filename

    except Exception as e:
        print(f"An error occurred during transcription: {e}")
        return None

# Function to summarize the transcript
def summarize_transcript(transcript_filename):
    try:
        with open(transcript_filename, 'r') as file:
            content = file.read()

        paragraph = " ".join(content.split('\n'))
        wrapped_text = textwrap.fill(paragraph, width=80)

        summary_filename = transcript_filename.replace("transcript", "summary")
        with open(summary_filename, 'w') as file:
            file.write(wrapped_text)


        return (summary_filename, wrapped_text)

    except Exception as e:
        print(f"An error occurred during summarization: {e}")
        return None

def format_with_groq(text):
    try:

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Punctuate and format the following: " + text,
                }
            ],
            model="llama3-8b-8192",
        )

        formatted_text = chat_completion.choices[0].message.content

        return formatted_text

    except Exception as e:
        print(f"An error occurred during formatting with Groq: {e}")
        return None

@app.route('/keywords', methods=['POST'])
def get_keywords():
    try:
        data = request.get_json()
        summary_text = data['summary_text']
        print(summary_text)
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Extract atleast 15 keywords from the following text:" + summary_text,
                }
            ],
            model="llama3-8b-8192",
        )

        keywords = chat_completion.choices[0].message.content
        print(keywords)
        return jsonify({'keywords': keywords})

    except Exception as e:
        print(f"An error occurred during extracting keywords with Groq: {e}")
        return None

@app.route('/summarytext', methods=['POST'])
def get_summary():
    try:
        data = request.get_json()
        summary_text = data['summary_text']
        print(summary_text)
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Give summary of the following text with different subtitles like title, content, conclusion etc." + summary_text,
                }
            ],
            model="llama3-8b-8192",
        )

        summary = chat_completion.choices[0].message.content
        print(summary)
        return jsonify({'summary': summary})

    except Exception as e:
        print(f"An error occurred during extracting keywords with Groq: {e}")
        return None


# Route to serve the homepage
@app.route('/')
def home():
    return render_template('index.html')

# Route to handle form submission
@app.route('/transcribe', methods=['POST'])
def transcribe():
    youtube_url = request.form['youtube_url']
    audio_file = download_audio(youtube_url)
    if audio_file:
        transcript_file = transcribe_audio(audio_file)
        if transcript_file:
            (summary_file, summary_text) = summarize_transcript(transcript_file)
            formatted_text = format_with_groq(summary_text)
            if summary_file:
                return render_template('output.html', transcript_text=formatted_text)
                # return send_from_directory('.', summary_file, as_attachment=True)
            else:
                return "Transcription succeeded but summarization failed."
        else:
            return "Transcription failed."
    else:
        return "Audio download failed."

if __name__ == "__main__":
    app.run(debug=True)
