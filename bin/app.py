from flask import Flask, render_template, send_from_directory, redirect
import os
from pathlib import Path

app = Flask(__name__)

# Define directories (relative to project root)
IMAGES_DIR = "images"
SNAPSHOT_DIR = "snapshot"
EXCEL_FILE = "attendance_summary.xlsx"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/images")
def list_images():
    # List files (only file names) from the images directory
    path = Path(IMAGES_DIR)
    file_names = [f.name for f in path.iterdir() if f.is_file()]
    return render_template("files.html", folder="images", files=file_names)

@app.route("/snapshots")
def list_snapshots():
    path = Path(SNAPSHOT_DIR)
    file_names = [f.name for f in path.iterdir() if f.is_file()]
    return render_template("files.html", folder="snapshot", files=file_names)

@app.route("/download/attendance")
def download_attendance():
    # Redirect to download attendance_summary.xlsx
    return send_from_directory(directory=".", path=EXCEL_FILE, as_attachment=True)

# Optionally, serve static files if needed
@app.route("/<path:filename>")
def serve_static(filename):
    # This function helps serve files from the project root
    if os.path.exists(filename):
        return send_from_directory(".", filename)
    return "File not found", 404

if __name__ == '__main__':
    app.run(debug=True)
