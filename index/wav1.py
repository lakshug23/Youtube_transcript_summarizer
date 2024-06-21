# import speech_recognition as sr
# from pydub import AudioSegment
# import os


# def convert_mp3_to_wav(mp3_file_path, wav_file_path):
#     # Load the mp3 file
#     audio = AudioSegment.from_mp3(mp3_file_path)

#     # Export as wav
#     audio.export(wav_file_path, format="wav")
#     print(f"Conversion complete: {wav_file_path}")



# def convert_wav_to_text(wav_file):
#     recognizer = sr.Recognizer()

#     try:
#         with sr.AudioFile(wav_file) as source:
#             audio_text = recognizer.record(source)
#         try:
#             text = recognizer.recognize_google(audio_text)
#             print("Converted text:", text)
#             return text
#         except sr.UnknownValueError:
#             print("Could not recognize audio.")
#             return ""
#         except sr.RequestError as e:
#             print(f"Could not request results from Google Speech Recognition service; {e}")
#             return ""
#     finally:
#         print("Transcript generation completed!")
#         if os.path.exists(wav_file):
#             os.remove(wav_file)

# # Example usage
# mp3_file_path = "C:\\Users\\M S Geetha Devasena\\Downloads\\Intro to Programming Loops.mp3"
# wav_file_path = "output.wav"
# convert_mp3_to_wav(mp3_file_path, wav_file_path)
# convert_wav_to_text(wav_file_path)




import speech_recognition as sr
from pydub import AudioSegment
from pydub.silence import split_on_silence
import os


def convert_mp3_to_wav(mp3_file_path, wav_file_path):
  """
  Converts an MP3 file to WAV format.

  Args:
    mp3_file_path: Path to the MP3 file.
    wav_file_path: Path to save the converted WAV file.
  """
  # Load the mp3 file
  audio = AudioSegment.from_mp3(mp3_file_path)

  # Export as wav
  audio.export(wav_file_path, format="wav")
  print(f"Conversion complete: {wav_file_path}")


def split_audio(audio, min_silence_len=1000, silence_thresh=-16, keep_silence=500):
  """
  Splits an audio file into chunks based on silence.

  Args:
    audio: The AudioSegment object representing the audio file.
    min_silence_len: Minimum silence length in milliseconds for splitting.
    silence_thresh: Silence threshold in dB.
    keep_silence: Amount of silence (in milliseconds) to include on the beginning and end of chunks.

  Returns:
    A list of AudioSegment objects representing the split audio chunks.
  """
  # Split the audio file into chunks based on silence
  chunks = split_on_silence(audio,
                            min_silence_len=min_silence_len,
                            silence_thresh=silence_thresh,
                            keep_silence=keep_silence)
  return chunks


def convert_wav_to_text(wav_file, transcript_file):
  """
  Converts a WAV file to text using Google Speech Recognition.

  Args:
    wav_file: Path to the WAV file.
    transcript_file: Path to save the transcribed text.
  """
  recognizer = sr.Recognizer()

  try:
    audio = AudioSegment.from_wav(wav_file)
    chunks = split_audio(audio)

    full_text = []

    for i, chunk in enumerate(chunks):
      chunk_wav = f"chunk{i}.wav"
      chunk.export(chunk_wav, format="wav")
      try:
        with sr.AudioFile(chunk_wav) as source:
          audio_text = recognizer.record(source)
          try:
            text = recognizer.recognize_google(audio_text)
            full_text.append(text)
          except sr.UnknownValueError:
            print(f"Could not recognize audio in chunk {i}.")
          except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service for chunk {i}; {e}")
      except Exception as e:
        print(f"Error processing chunk {i}: {e}")

    final_text = " ".join(full_text)
    print("Converted text:", final_text)

    # Write final text to transcript file even if exceptions occur during chunk processing
    with open(transcript_file, 'w') as file:
      file.write(final_text)

  finally:
    print("Transcript generation completed!")
    if os.path.exists(wav_file):
      os.remove(wav_file)


# Example usage
mp3_file_path = "C:\\Users\\M S Geetha Devasena\\Downloads\\Intro to Programming Loops.mp3"
wav_file_path = "output.wav"
transcript_file = "transcript.txt"
convert_mp3_to_wav(mp3_file_path, wav_file_path)
convert_wav_to_text(wav_file_path, transcript_file)


