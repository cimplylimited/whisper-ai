import subprocess
import json

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

# Example usage
video_file_path = 'file-path.mp4'
audio_tracks_count = get_audio_tracks_count(video_file_path)

if audio_tracks_count is not None:
    print(f"The video file contains {audio_tracks_count} audio track(s).")
else:
    print("Failed to determine the number of audio tracks.")

