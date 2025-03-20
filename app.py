from flask import Flask, render_template, send_file, send_from_directory
import os
import subprocess
import pandas as pd

app = Flask(__name__)

# Constants
IMAGES_DIR = "images"
SNAPSHOT_DIR = "snapshot"
ATTENDANCE_CSV = "attendance.csv"
EXCEL_FILE = "attendance_summary.xlsx"


@app.route("/")
def index():
    """Render the home page."""
    return render_template("index.html")


@app.route("/run_final", methods=["POST"])
def run_final():
    """Run final_main.py in the background and display output in the terminal."""
    subprocess.Popen(["python", "final_main.py"])
    return "Final main started successfully!"


@app.route("/images")
def list_images():
    """List all images in the 'images' folder."""
    try:
        file_names = [f for f in os.listdir(IMAGES_DIR) if os.path.isfile(os.path.join(IMAGES_DIR, f))]
        return render_template("files.html", folder=IMAGES_DIR, files=file_names)
    except Exception as e:
        return f"Error listing images: {e}", 500


@app.route("/snapshots")
def list_snapshots():
    """List all snapshots in the 'snapshot' folder."""
    try:
        file_names = [f for f in os.listdir(SNAPSHOT_DIR) if os.path.isfile(os.path.join(SNAPSHOT_DIR, f))]
        return render_template("files.html", folder=SNAPSHOT_DIR, files=file_names)
    except Exception as e:
        return f"Error listing snapshots: {e}", 500


@app.route("/attendance")
def view_attendance():
    """Display attendance CSV content as a table without extra blank rows."""
    try:
        if not os.path.exists(ATTENDANCE_CSV):
            return "Attendance file not found!", 404

        df = pd.read_csv(ATTENDANCE_CSV)

        # Remove completely empty rows
        df = df.dropna(how="all")

        # Strip unwanted whitespace and newline characters
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

        return render_template("attendance.html", tables=[df.to_html(classes='data', index=False)], titles=df.columns.values)
    except Exception as e:
        return f"Error loading attendance CSV: {e}", 500


@app.route("/download_excel")
def download_excel():
    """Download the attendance Excel file."""
    try:
        if os.path.exists(EXCEL_FILE):
            return send_file(EXCEL_FILE, as_attachment=True)
        else:
            return "Attendance Excel file not found!", 404
    except Exception as e:
        return f"Error downloading Excel file: {e}", 500


@app.route("/images/<filename>")
def serve_image(filename):
    """Serve images from the images directory."""
    try:
        return send_from_directory(IMAGES_DIR, filename)
    except Exception as e:
        return f"Error loading image: {e}", 500


@app.route("/snapshot/<filename>")
def serve_snapshot(filename):
    """Serve snapshots from the snapshot directory."""
    try:
        return send_from_directory(SNAPSHOT_DIR, filename)
    except Exception as e:
        return f"Error loading snapshot: {e}", 500


if __name__ == "__main__":
    app.run(debug=True, threaded=True)
