# Introduction
This set of mini applications was designed because of a need to synthesize a large
repository of video recordings from LexDAO's recent event in Denver in Q1 2024.
After the session, very limited information about what was discussed during the panels was received and there was strong recorded content that was produced.  This experiment is an attempt to speed the process of getting context on large amounts of spoken material in an efficient way.

## Important Notes
Any of the scripts will require the definition of variables within them.  Just a word of caution as you start trying to deploy them in your environment.

# Design
This application set works in three phases.  All of these phases are initially seeded by the recorded video and audio from live sessions.  It is worth noting that I have included the iterations of these scripts so that it is clear how they have been calibrated and what changed over time.

## Phase 1
**Separate the Channels**: 
In order to minimize the amount of language processing, the first step is to split the file channels into video and audio.  In testing the ffmpeg package, a program designed for this type of parsing, it became clear that it was more efficient to only keep the audio file and ignore the video components for the purposes of this output.  Knowing there might be situations where both were necessary, the script "audio-video-filesplit-plus-diagnostics" asks a user what they want to do with the AV processing.

## Phase 2
**Transcribe the Audio**:
Open source transcription is showing to be incredibly accurate in the ability to take english audio and output text.  It is worth noting that it is less effective at translation, but still impressive.  

The main issue with most AI applications is that you are sending your data to someone else's server.  So this next step was about finding a local LLM deployment which could be called and processed on a local machine.  The package used for these purposes was whisper-ai.

This was a preliminary test of the application and it was effective.  However, it is yet to be seen how to properly incorporate time stamp markers as well as separation of speakers.  It appears that having more audio channels would allow this to be calibrated, but it is a current deficiency of the model.

## Phase 3
**Meaning Extraction**
The goal here was to take a strong set of seed data (viz. the accurate transcript) and ask open-at's gpt-4 model to deliver a summary and some structured notes.  The model was quite good at getting the content to at least 80% finality and seems to have identified the speakers in many cases.  It is worth noting here that there are two key shortcomings.  
1. The model does seem to hallucinate which calls some of the speaker identification for example into question.  The firm example of hallucination was its attempt to infer a date of the panels.  This was certainly incorrect in the output files.
2.  THe model cannot get a standard format for responding and outputting variables.  Therefore, wherever these files go next, will require additional data cleaning and processing.  While the structure of the outputs seems relatively clean and is certainly readable, it is interesting that it seems to respond from different areas of its "conciousness", if there was such a thing.
