import subprocess
import json
import os

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

def split_video_into_tracks(video_file):
    # Get the base name of the input video file
    base_name = os.path.splitext(os.path.basename(video_file))[0]

    # Get the number of audio tracks in the video file
    audio_tracks_count = get_audio_tracks_count(video_file)

    if audio_tracks_count is None:
        print("Failed to determine the number of audio tracks.")
        return

    # Run ffmpeg command to split the video into distinct audio and video tracks
    for track_index in range(audio_tracks_count):
        output_video_file = f"{base_name}_output_video_track_{track_index + 1}.mp4"
        output_audio_file = f"{base_name}_output_audio_track_{track_index + 1}.mp3"

        ffmpeg_command = ['ffmpeg', '-i', video_file, '-map', f'0:a:{track_index}', '-vn', output_audio_file, '-map', '0:v', output_video_file]
        process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if stderr:
            print(f"Error splitting track {track_index + 1}:")
            print(stderr.decode())
        else:
            print(f"Track {track_index + 1} split successfully.")

# Example usage
video_file_path = 'file-path.mp4'
split_video_into_tracks(video_file_path)
