import os
import subprocess
import uuid
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Ensure the static/videos directory exists
VIDEOS_DIR = os.path.join("static", "videos")
os.makedirs(VIDEOS_DIR, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate_video():
    data = request.json
    try:
        duration_seconds = float(data.get("duration", 5))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid duration"}), 400

    filename = f"video_{uuid.uuid4().hex}.mp4"
    output_path = os.path.join(VIDEOS_DIR, filename)
    
    # Use the centisecond version (00->99) as provided by Claude
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    ffmpeg_cmd = [
        ffmpeg_exe, "-y",
        "-f", "lavfi", "-i", f"color=c=black:s=1920x1080:r=30:d={duration_seconds}",
        "-vf",
        "drawtext=fontfile=font.ttf:"
        "text='%{eif\\:floor(t/3600)\\:d\\:2}\\:%{eif\\:floor(mod(t\\,3600)/60)\\:d\\:2}"
        "\\:%{eif\\:floor(mod(t\\,60))\\:d\\:2}\\:%{eif\\:floor(mod(t\\,1)*100)\\:d\\:2}':"
        "fontcolor=white:fontsize=150:x=(w-text_w)/2:y=(h-text_h)/2",
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        output_path,
    ]
    
    # Khusus Windows: cegah jendela CMD muncul, TANPA bikin error di Railway/Linux
    kwargs = {}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        
    try:
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True, **kwargs)
        return jsonify({"video_url": f"/static/videos/{filename}"})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"FFmpeg failed: {e.stderr.decode('utf-8', errors='ignore')}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")
