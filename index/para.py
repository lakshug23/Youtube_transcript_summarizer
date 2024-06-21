from pytube import YouTube
import os
from datetime import datetime
from pydub import AudioSegment
import speech_recognition as sr
from concurrent.futures import ThreadPoolExecutor, as_completed
import math
import moviepy.editor as mp

def download_audio(youtube_url):
    try:
        yt = YouTube(youtube_url)
        stream = yt.streams.filter(only_audio=True).first()

        if stream is None:
            print("No audio streams available")
            return None

        output_file = stream.download(filename='audio.webm')
        return output_file

    except Exception as e:
        print(f"An error occurred during download: {e}")
        return None

def transcribe_chunks(audio_file, chunk_length=30):
    try:
        # Convert webm to wav
        audio = mp.AudioFileClip(audio_file)
        wav_file = audio_file.replace(".webm", ".wav")
        audio.write_audiofile(wav_file)

        # Load the wav file
        audio = AudioSegment.from_wav(wav_file)
        recognizer = sr.Recognizer()

        def transcribe_chunk(chunk, chunk_index):
            try:
                with sr.AudioFile(chunk) as source:
                    audio_data = recognizer.record(source)
                    text = recognizer.recognize_google(audio_data)
                    return chunk_index, text
            except sr.UnknownValueError:
                return chunk_index, f"Unable to transcribe chunk {chunk_index}"
            except sr.RequestError as e:
                return chunk_index, f"Error in transcription service for chunk {chunk_index}: {e}"

        with ThreadPoolExecutor() as executor:
            audio_duration = len(audio)
            num_chunks = math.ceil(audio_duration / (chunk_length * 1000))
            futures = []
            for i in range(num_chunks):
                start_time = i * chunk_length * 1000
                end_time = min((i + 1) * chunk_length * 1000, audio_duration)
                chunk = audio[start_time:end_time]
                chunk_filename = f"temp_chunk_{i}.wav"
                chunk.export(chunk_filename, format="wav")
                futures.append(executor.submit(transcribe_chunk, chunk_filename, i))

            transcripts = []
            for future in as_completed(futures):
                result = future.result()
                transcripts.append(result)

            transcripts.sort(key=lambda x: x[0])
            transcripts_text = [text for _, text in transcripts]

        # Write transcripts to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        transcript_filename = f'transcript_{timestamp}.txt'
        with open(transcript_filename, 'a') as file:
            for transcript in transcripts_text:
                file.write(transcript + ' ')

        return transcript_filename

    except Exception as e:
        print(f"An error occurred during transcription: {e}")
        return None

def read_and_print_file(filename):
    try:
        with open(filename, 'r') as file:
            content = file.read()
            print("Contents of the file:")
            print(content)
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")

# Example usage
youtube_url = 'https://www.youtube.com/watch?v=bgm7-ycdcDk'
audio_file = download_audio(youtube_url)
if audio_file:
    transcript_file = transcribe_chunks(audio_file)
    if transcript_file:
        read_and_print_file(transcript_file)
    else:
        print("Transcription failed.")