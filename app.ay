from flask import Flask, render_template, request
import subprocess
import os
import tempfile

app = Flask(__name__)

def get_video_duration(file_path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return float(result.stdout.strip())

def seconds_to_timestamp(seconds):
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hrs:02}:{mins:02}:{secs:02}"

@app.route("/", methods=["GET", "POST"])
def index():
    cuts = []
    duration = None

    if request.method == "POST":
        file = request.files["video"]
        target_minutes = int(request.form["length"])

        with tempfile.NamedTemporaryFile(delete=False) as temp:
            file.save(temp.name)
            duration = get_video_duration(temp.name)

        segment_length = target_minutes * 60
        num_segments = int(duration // segment_length) + 1

        for i in range(num_segments):
            start = i * segment_length
            end = min((i + 1) * segment_length, duration)

            cuts.append({
                "episode": i + 1,
                "start": seconds_to_timestamp(start),
                "end": seconds_to_timestamp(end)
            })

        os.remove(temp.name)

    return render_template("index.html", cuts=cuts, duration=duration)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
