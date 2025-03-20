import os
import cv2
import numpy as np
import time
import csv
import datetime
import pandas as pd
from insightface.app import FaceAnalysis

KNOWN_FACES_FOLDER = "images"
SNAPSHOT_FOLDER = "snapshot"
ATTENDANCE_CSV = "attendance.csv"
EXCEL_FILENAME = "attendance_summary.xlsx"
THRESHOLD = 25

CAPTURE_INTERVAL = 30
CYCLE_DURATION = 2 * 60
ABSENT_THRESHOLD = 3

if not os.path.exists(SNAPSHOT_FOLDER):
    os.makedirs(SNAPSHOT_FOLDER)

app = FaceAnalysis(name="buffalo_l", providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))

def get_face_embedding(image_path):
    img = cv2.imread(image_path)
    faces = app.get(img)
    if faces:
        return faces[0].embedding
    return None

known_faces = {}
for filename in os.listdir(KNOWN_FACES_FOLDER):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        person_name = os.path.splitext(filename)[0]
        image_path = os.path.join(KNOWN_FACES_FOLDER, filename)
        embedding = get_face_embedding(image_path)
        if embedding is not None:
            known_faces[person_name] = embedding
        else:
            print(f"Warning: No face detected in {filename}")

if not known_faces:
    print("No known faces found in the 'images/' folder!")
    exit()

csv_header = ["timestamp", "snapshot", "name", "status"]
if not os.path.exists(ATTENDANCE_CSV):
    with open(ATTENDANCE_CSV, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(csv_header)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam!")
    exit()

print("Live face recognition running. Press 'q' to quit.")

last_capture_time = time.time()
cycle_start_time = time.time()
period = 1

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame!")
        break

    cv2.imshow("Live Face Recognition", frame)
    current_time = time.time()

    if current_time - last_capture_time >= CAPTURE_INTERVAL:
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_filename = f"snapshot_{timestamp_str}.jpg"
        snapshot_path = os.path.join(SNAPSHOT_FOLDER, snapshot_filename)
        cv2.imwrite(snapshot_path, frame)
        print(f"[INFO] Snapshot captured: {snapshot_filename}")

        detected_faces = app.get(frame)
        attendance_status = {person: "Absent" for person in known_faces.keys()}
        recognized_names = []

        if not detected_faces:
            print("[INFO] No face detected in this snapshot; marking all as Absent.")
        else:
            for detected_face in detected_faces:
                detected_embedding = detected_face.embedding
                best_match_name = None
                best_match_distance = float("inf")
                for person_name, known_embedding in known_faces.items():
                    distance = np.linalg.norm(known_embedding - detected_embedding)
                    if distance < THRESHOLD and distance < best_match_distance:
                        best_match_distance = distance
                        best_match_name = person_name
                if best_match_name:
                    attendance_status[best_match_name] = "Present"
                    recognized_names.append(best_match_name)
                    x1, y1, x2, y2 = detected_face.bbox.astype(int)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, best_match_name, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        print(f"Snapshot: {snapshot_filename}, Recognized: {', '.join(recognized_names) if recognized_names else 'None'}")

        with open(ATTENDANCE_CSV, mode="a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=csv_header)
            for person, status in attendance_status.items():
                row = {
                    "timestamp": timestamp_str,
                    "snapshot": snapshot_filename,
                    "name": person,
                    "status": status
                }
                writer.writerow(row)
            empty_row = {col: "" for col in csv_header}
            writer.writerow(empty_row)
        print(f"[INFO] Attendance recorded for {timestamp_str}")
        last_capture_time = current_time

    if current_time - cycle_start_time >= CYCLE_DURATION:
        print(f"[INFO] Period {period} complete. Processing attendance summary...")
        df = pd.read_csv(ATTENDANCE_CSV)
        df = df.dropna(how="all")
        if "name" not in df.columns:
            df.columns = csv_header

        current_summary = {}
        for person in known_faces.keys():
            person_rows = df[df["name"] == person]
            absent_count = (person_rows["status"] == "Absent").sum()
            current_summary[person] = "Absent" if absent_count >= ABSENT_THRESHOLD else "Present"

        period_col = f"Period {period}"
        summary_df = pd.DataFrame({
            "Person": list(current_summary.keys()),
            period_col: list(current_summary.values())
        })

        if os.path.exists(EXCEL_FILENAME):
            excel_df = pd.read_excel(EXCEL_FILENAME)
            for person in known_faces.keys():
                if person not in excel_df["Person"].values:
                    excel_df = pd.concat([excel_df, pd.DataFrame({"Person": [person]})], ignore_index=True)
            excel_df.set_index("Person", inplace=True)
            excel_df[period_col] = summary_df.set_index("Person")[period_col]
            excel_df.reset_index(inplace=True)
        else:
            excel_df = summary_df.copy()

        written = False
        while not written:
            try:
                excel_df.to_excel(EXCEL_FILENAME, index=False)
                written = True
            except PermissionError:
                print(f"[ERROR] Permission denied when writing {EXCEL_FILENAME}. Please close it and press Enter to retry.")
                input()

        print(f"[INFO] Updated summary: column '{period_col}' in {EXCEL_FILENAME}")

        with open(ATTENDANCE_CSV, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(csv_header)
        cycle_start_time = current_time

        if period >= 7:
            print("[INFO] Period 7 reached. Ending program.")
            break
        else:
            period += 1

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
