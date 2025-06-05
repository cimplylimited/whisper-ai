import whisper

model = whisper.load_model("large")
result = model.transcribe("/Users/johndoe/Downloads/KD_audio_message.m4a")

with open("file-output-path.txt", "w") as f:
    f.write(result["text"])


