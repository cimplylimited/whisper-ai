import subprocess
import json
import os
import sys
import subprocess

## This script is designed to work with any audio file compatible with ffmpeg package.

# User-defined variables.
# Be sure to set the file path in the video_file_path and define the output directory

# This version now includes some error handling for checking if files exist.


video_file_path = 'file-path.mp4'  # Path to the input video file
output_directory = 'directory-path'  # Destination directory for output files


def check_input_file_exists(video_file):
    if not os.path.isfile(video_file):
        print("Error001: File does not exist.")
        sys.exit(1)
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

def split_video_into_tracks(video_file, output_directory):
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    audio_tracks_count = 2  # Placeholder for audio tracks count (replace with actual count)

    for track_index in range(audio_tracks_count):
        output_video_file = os.path.join(output_directory, f"{base_name}_output_video_track_{track_index + 1}.mp4")
        output_audio_file = os.path.join(output_directory, f"{base_name}_output_audio_track_{track_index + 1}.mp3")

        ffmpeg_command = ['ffmpeg', '-i', video_file, '-map', f'0:a:{track_index}', '-vn', output_audio_file, '-map', '0:v', output_video_file]

        try:
            process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate(timeout=300)  # Increase timeout if needed
            if stderr:
                print(f"Error splitting track {track_index + 1}:")
                print(stderr.decode())
            else:
                print(f"Track {track_index + 1} split successfully.")
                print(stdout.decode())  # Print output for debugging
        except subprocess.TimeoutExpired:
            print(f"Timeout expired while splitting track {track_index + 1}.")
        except Exception as e:
            print(f"Error during splitting track {track_index + 1}: {e}")

# Check if input file exists before proceeding
check_input_file_exists(video_file_path)

# Example usage
split_video_into_tracks(video_file_path, output_directory)