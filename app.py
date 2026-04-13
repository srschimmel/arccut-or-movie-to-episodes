from flask import Flask, render_template, request
import subprocess
import os
import tempfile
from urllib.parse import urlparse

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200 MB upload limit


def is_allowed_video_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def get_video_duration(source):
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            source,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or "Could not read video source.")

    output = result.stdout.strip()
    if not output:
        raise ValueError("No duration returned from ffprobe.")

    return float(output)


def seconds_to_timestamp(seconds):
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hrs:02}:{mins:02}:{secs:02}"


@app.route("/", methods=["GET", "POST"])
def index():
    cuts = []
    duration = None
    error = None
    selected_url = ""

    if request.method == "POST":
        target_minutes = int(request.form["length"])
        video_url = request.form.get("video_url", "").strip()
        selected_url = video_url
        file = request.files.get("video")

        source = None
        temp_path = None

        try:
            if video_url:
                if not is_allowed_video_url(video_url):
                    raise ValueError("Please enter a valid http or https video URL.")
                source = video_url
            elif file and file.filename:
                with tempfile.NamedTemporaryFile(delete=False) as temp:
                    file.save(temp.name)
                    temp_path = temp.name
                    source = temp_path
            else:
                raise ValueError("Upload a video or enter a direct video URL.")

            duration = get_video_duration(source)

            segment_length = target_minutes * 60
            num_segments = int(duration // segment_length) + 1

            for i in range(num_segments):
                start = i * segment_length
                end = min((i + 1) * segment_length, duration)
                cuts.append(
                    {
                        "episode": i + 1,
                        "start": seconds_to_timestamp(start),
                        "end": seconds_to_timestamp(end),
                    }
                )

        except Exception as exc:
            error = str(exc)

        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    return render_template(
        "index.html",
        cuts=cuts,
        duration=duration,
        error=error,
        selected_url=selected_url,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
