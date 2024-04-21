import whisper

model = whisper.load_model("small")
result = model.transcribe("file-path.mp3")

with open("file-output-path.txt", "w") as f:
    f.write(result["text"])


