import subprocess
import json
import os

# This script is designed to grab any compatible video file and to split out the audio
# as a separate track.  It allows the user to define the input file and output file.
# It also allows you to split out both the video and audio or just return the audio.


def get_audio_tracks_count(video_file):
    # Run ffprobe command to get JSON output with audio stream information
    ffprobe_command = ['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_entries', 'stream=index', '-of', 'json', video_file]
    process = subprocess.Popen(ffprobe_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if stderr:
        print("Error running ffprobe command:")
        print(stderr.decode())
        return None

    # Parse JSON output to extract audio tracks count
    try:
        ffprobe_output = json.loads(stdout.decode())
        audio_tracks_count = len(ffprobe_output['streams'])
        return audio_tracks_count
    except (json.JSONDecodeError, KeyError):
        print("Error parsing ffprobe output.")
        return None

def split_audio_only(video_file, output_directory):
    # Get the base name of the input video file
    base_name = os.path.splitext(os.path.basename(video_file))[0]

    # Get the number of audio tracks in the video file
    audio_tracks_count = get_audio_tracks_count(video_file)

    if audio_tracks_count is None:
        print("Failed to determine the number of audio tracks.")
        return

    # Run ffmpeg command to extract audio tracks only
    for track_index in range(audio_tracks_count):
        output_audio_file = os.path.join(output_directory, f"{base_name}_output_audio_track_{track_index + 1}.mp3")

        ffmpeg_command = ['ffmpeg', '-i', video_file, '-map', f'0:a:{track_index}', '-vn', output_audio_file]
        process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if stderr:
            print(f"Error splitting audio track {track_index + 1}:")
            print(stderr.decode())
        else:
            print(f"Audio track {track_index + 1} split successfully.")

def split_audio_and_video(video_file, output_directory):
    # Get the base name of the input video file
    base_name = os.path.splitext(os.path.basename(video_file))[0]

    # Get the number of audio tracks in the video file
    audio_tracks_count = get_audio_tracks_count(video_file)

    if audio_tracks_count is None:
        print("Failed to determine the number of audio tracks.")
        return

    # Run ffmpeg command to split audio and video tracks
    for track_index in range(audio_tracks_count):
        output_video_file = os.path.join(output_directory, f"{base_name}_output_video_track_{track_index + 1}.mp4")
        output_audio_file = os.path.join(output_directory, f"{base_name}_output_audio_track_{track_index + 1}.mp3")

        ffmpeg_command = ['ffmpeg', '-i', video_file, '-map', f'0:a:{track_index}', '-vn', output_audio_file, '-map', '0:v', output_video_file]
        process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if stderr:
            print(f"Error splitting track {track_index + 1}:")
            print(stderr.decode())
        else:
            print(f"Track {track_index + 1} split successfully.")

def split_video_into_tracks(video_file, output_directory):
    choice = input("Enter 'audio' to split audio tracks only, or 'both' to split both audio and video tracks: ").lower()

    if choice == 'audio':
        split_audio_only(video_file, output_directory)
    elif choice == 'both':
        split_audio_and_video(video_file, output_directory)
    else:
        print("Invalid choice. Please enter 'audio' or 'both'.")

# Example usage
video_file_path = 'path-to-file.mp4'
output_directory = 'directory-path'

split_video_into_tracks(video_file_path, output_directory)
