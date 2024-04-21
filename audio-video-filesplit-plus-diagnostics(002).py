import subprocess
import json
import os

### DOES NOT WORK.  OVERCLOCKS PROCESSOR###


def get_audio_and_video_tracks_count(video_file):
    # Run ffprobe command to get JSON output with audio and video stream information
    ffprobe_command = ['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type', '-of', 'json', video_file]
    process = subprocess.Popen(ffprobe_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if stderr:
        print("Error running ffprobe command:")
        print(stderr.decode())
        return None, None

    # Parse JSON output to extract audio and video tracks count
    try:
        ffprobe_output = json.loads(stdout.decode())
        audio_tracks_count = len([stream for stream in ffprobe_output['streams'] if stream['codec_type'] == 'audio'])
        video_tracks_count = len([stream for stream in ffprobe_output['streams'] if stream['codec_type'] == 'video'])
        return audio_tracks_count, video_tracks_count
    except (json.JSONDecodeError, KeyError):
        print("Error parsing ffprobe output.")
        return None, None

def split_video_into_tracks(video_file):
    # Get the number of audio and video tracks in the video file
    audio_tracks_count, video_tracks_count = get_audio_and_video_tracks_count(video_file)

    if audio_tracks_count is None or video_tracks_count is None:
        print("Failed to determine the number of audio or video tracks.")
        return

    # Run ffmpeg command to split the video into distinct audio and video tracks
    for track_index in range(audio_tracks_count):
        output_video_file = f"output_video_track_{track_index + 1}.mp4"
        output_audio_file = f"output_audio_track_{track_index + 1}.mp3"

        ffmpeg_command = ['ffmpeg', '-i', video_file, '-map', f'0:a:{track_index}', '-vn', output_audio_file, '-map', '0:v', output_video_file]
        process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if stderr:
            print(f"Error splitting audio track {track_index + 1}:")
            print(stderr.decode())
        else:
            print(f"Audio track {track_index + 1} split successfully.")

    for track_index in range(video_tracks_count):
        output_video_file = f"output_video_only_track_{track_index + 1}.mp4"

        ffmpeg_command = ['ffmpeg', '-i', video_file, '-map', f'0:v:{track_index}', '-an', output_video_file]
        process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if stderr:
            print(f"Error splitting video track {track_index + 1}:")
            print(stderr.decode())
        else:
            print(f"Video track {track_index + 1} split successfully.")

# Example usage
video_file_path = 'path/to/your/video_file.mp4'
split_video_into_tracks(video_file_path)
