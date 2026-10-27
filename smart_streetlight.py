"""
AI-Based Smart Street Lighting System — Dual-Interface (OpenCV Window + Streamlit Dashboard)

Features:
- Native OpenCV window for real-time, low-latency video & YOLO detection
- Streamlit web dashboard for control mode, schedules, status metrics, and Excel data export
- Threaded camera reading to prevent frame buffering lag
- Single-zone YOLO person detection & 3-second stability delay
- Excel export including detection records
"""

from datetime import datetime, time as dt_time
from pathlib import Path
import threading
import time
import io

import cv2
import pandas as pd
import requests
import streamlit as st
from ultralytics import YOLO


# -------------------------- DEFAULT SETTINGS --------------------------
DEFAULT_CAMERA_URL = "http://192.168.1.3:8080/video"
DEFAULT_ESP32_IP = "192.168.76.187"
MODEL_PATH = "yolov8n.pt"
DETECTION_DELAY_SECONDS = 3.0
FRAME_SAVE_DIR = Path("saved_detection_frames")


def brightness_for_count(count: int) -> int:
    """Brightness thresholds: 0 people -> 25%, 1 person -> 65%, 2+ people -> 100%."""
    if count >= 2:
        return 100
    if count == 1:
        return 65
    return 25


def schedule_is_active(now: datetime, start: dt_time, stop: dt_time) -> bool:
    current = now.time()
    if start == stop:
        return True
    if start < stop:
        return start <= current < stop
    return current >= start or current < stop


# ---------------------- CAMERA & DETECTION THREAD ----------------------
class CameraThread(threading.Thread):
    def __init__(self, camera_url: str, model_path: str):
        super().__init__()
        self.camera_url = camera_url
        self.model_path = model_path
        self.running = False
        self.cap = None
        self.model = None

        # Shared state parameters
        self.latest_count = 0
        self.applied_count = 0
        self.applied_brightness = 25
        self.camera_error = ""
        self.esp_error = ""
        self.history = []

        # Control settings (updated dynamically from Streamlit)
        self.mode = "Automatic Schedule"
        self.start_time = dt_time(18, 0)
        self.stop_time = dt_time(6, 0)
        self.esp32_ip = DEFAULT_ESP32_IP
        self.save_frames = False

        # Internal tracking
        self.candidate_count = None
        self.candidate_since = None
        self.last_logged_sig = None
        self.last_command_sig = None
        self.last_command_time = 0.0
        self.last_frame_save_time = 0.0

    def get_enabled(self, now: datetime) -> bool:
        if self.mode == "Manual ON":
            return True
        if self.mode == "Manual OFF":
            return False
        return schedule_is_active(now, self.start_time, self.stop_time)

    def send_light_command(self, enabled: bool, brightness: int):
        esp32_url = f"http://{self.esp32_ip}/set" if self.esp32_ip else ""
        signature = (enabled, brightness if enabled else 0)
        now_mono = time.monotonic()

        if signature == self.last_command_sig and now_mono - self.last_command_time < 5:
            return

        if not esp32_url:
            self.esp_error = "Enter the ESP32 IP address in the sidebar."
            return

        params = {
            "enabled": 1 if enabled else 0,
            "z1": brightness if enabled else 0,
            "z2": brightness if enabled else 0,
        }
        try:
            res = requests.get(esp32_url, params=params, timeout=1.5)
            res.raise_for_status()
            self.last_command_sig = signature
            self.last_command_time = now_mono
            self.esp_error = ""
        except requests.RequestException as exc:
            self.esp_error = f"ESP32 connection failed: {exc}"

    def run(self):
        self.running = True
        try:
            self.model = YOLO(self.model_path)
        except Exception as e:
            self.camera_error = f"Model load error: {e}"
            return

        self.cap = cv2.VideoCapture(self.camera_url)
        try:
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass

        window_name = "Live Camera - AI Smart Streetlight"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        while self.running:
            ok, frame = self.cap.read()
            if not ok or frame is None:
                self.camera_error = "No camera frame received. Check IP Webcam connection."
                time.sleep(0.1)
                continue

            self.camera_error = ""
            now_local = datetime.now()
            current_mono = time.monotonic()
            enabled_now = self.get_enabled(now_local)

            # YOLO inference
            results = self.model.predict(
                source=frame,
                classes=[0],  # Person class
                conf=0.35,
                imgsz=640,
                verbose=False,
            )
            result = results[0]
            count = len(result.boxes) if result.boxes is not None else 0
            self.latest_count = count

            annotated_frame = result.plot()

            # Save frames if enabled
            if self.save_frames and count > 0 and (current_mono - self.last_frame_save_time >= 3.0):
                FRAME_SAVE_DIR.mkdir(parents=True, exist_ok=True)
                timestamp_str = now_local.strftime("%Y%m%d_%H%M%S")
                frame_path = FRAME_SAVE_DIR / f"person_detection_{timestamp_str}.jpg"
                cv2.imwrite(str(frame_path), annotated_frame)
                self.last_frame_save_time = current_mono

            # 3-Second stability check
            if count != self.candidate_count:
                self.candidate_count = count
                self.candidate_since = current_mono
            elif self.candidate_since is None:
                self.candidate_since = current_mono

            stable_for = current_mono - self.candidate_since
            delay_complete = stable_for >= DETECTION_DELAY_SECONDS

            if delay_complete:
                self.applied_count = count
                self.applied_brightness = brightness_for_count(count)

                # Logging history
                log_sig = (
                    now_local.strftime("%Y-%m-%d %H:%M"),
                    count,
                    self.applied_brightness,
                    self.mode,
                    enabled_now,
                )
                if log_sig != self.last_logged_sig:
                    self.history.append({
                        "Timestamp": now_local.strftime("%Y-%m-%d %H:%M:%S"),
                        "Detected people": count,
                        "Zone": "Single zone",
                        "Brightness (%)": self.applied_brightness if enabled_now else 0,
                        "Operating mode": self.mode,
                        "Light enabled": "Yes" if enabled_now else "No",
                        "Stable detection (seconds)": round(stable_for, 2),
                    })
                    self.last_logged_sig = log_sig

            # Send light commands
            if enabled_now:
                self.send_light_command(True, self.applied_brightness)
            else:
                self.send_light_command(False, 0)

            # Display frame in native OpenCV Python window
            cv2.imshow(window_name, annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

    def stop(self):
        self.running = False


# --------------------------- STREAMLIT PAGE ---------------------------
st.set_page_config(
    page_title="AI Smart Streetlight Dashboard",
    page_icon="💡",
    layout="wide",
)

st.title("💡 AI-Based Smart Street Lighting System")
st.caption("Native Python OpenCV camera window • Adjustable schedule • Excel export")


# Initialize background camera thread
if "cam_thread" not in st.session_state:
    st.session_state.cam_thread = None


# ------------------------------ SIDEBAR -------------------------------
with st.sidebar:
    st.header("⚙️ System settings")
    camera_url = st.text_input("IP Webcam video URL", value=DEFAULT_CAMERA_URL)
    esp32_ip = st.text_input("ESP32 IP address", value=DEFAULT_ESP32_IP).strip()

    st.divider()
    st.subheader("Camera Control")
    cam_running = st.session_state.cam_thread is not None and st.session_state.cam_thread.is_alive()

    col_btn1, col_btn2 = st.columns(2)
    if col_btn1.button("Start Camera Window", disabled=cam_running):
        thread = CameraThread(camera_url, MODEL_PATH)
        thread.esp32_ip = esp32_ip
        thread.start()
        st.session_state.cam_thread = thread
        st.rerun()

    if col_btn2.button("Stop Camera Window", disabled=not cam_running):
        if st.session_state.cam_thread:
            st.session_state.cam_thread.stop()
            st.session_state.cam_thread = None
        st.rerun()

    st.divider()
    st.subheader("Operating mode")
    mode = st.radio("Choose control mode", ["Automatic Schedule", "Manual ON", "Manual OFF"], index=0)

    st.subheader("Demonstration schedule")
    start_time = st.time_input("Light ON time", value=dt_time(18, 0), key="start_time")
    stop_time = st.time_input("Light OFF time", value=dt_time(6, 0), key="stop_time")

    save_frames = st.checkbox("Save selected detection frames", value=False)


# Update thread settings on each Streamlit cycle
if st.session_state.cam_thread and st.session_state.cam_thread.is_alive():
    t = st.session_state.cam_thread
    t.mode = mode
    t.start_time = start_time
    t.stop_time = stop_time
    t.esp32_ip = esp32_ip
    t.save_frames = save_frames


# ----------------------- DASHBOARD METRICS -----------------------
now = datetime.now()
scheduled_active = schedule_is_active(now, start_time, stop_time)

if st.session_state.cam_thread and st.session_state.cam_thread.is_alive():
    t = st.session_state.cam_thread
    system_enabled = t.get_enabled(now)
    applied_brightness = t.applied_brightness
    latest_count = t.latest_count
    history_data = t.history
    cam_err = t.camera_error
    esp_err = t.esp_error
else:
    system_enabled = mode == "Manual ON" or (mode == "Automatic Schedule" and scheduled_active)
    applied_brightness = 25
    latest_count = 0
    history_data = []
    cam_err = "Camera window is not running. Click 'Start Camera Window' in the sidebar."
    esp_err = ""

col1, col2, col3, col4 = st.columns(4)
col1.metric("System Clock", now.strftime("%I:%M:%S %p"))
col2.metric("Schedule", "ACTIVE" if scheduled_active else "INACTIVE")
col3.metric("Light Control", "ON" if system_enabled else "OFF")
col4.metric("Current Brightness", f"{applied_brightness}%" if system_enabled else "0%")

if cam_err:
    st.warning(cam_err)
if esp_err:
    st.error(esp_err)

st.divider()

# ----------------------- LIVE STATUS & DATA EXPORT -----------------------
left_col, right_col = st.columns([1, 1])

with left_col:
    st.subheader("📊 Live Status")
    st.metric("People Detected (Current Frame)", latest_count)
    st.metric("Applied Brightness Command", f"{applied_brightness}%" if system_enabled else "0% (OFF)")

with right_col:
    st.subheader("📁 Export Detection Log to Excel")
    if history_data:
        df_history = pd.DataFrame(history_data)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_history.to_excel(writer, index=False, sheet_name="Detection Log")
            df_readme = pd.DataFrame([
                {"Setting": "Model", "Value": MODEL_PATH},
                {"Setting": "Detection Delay", "Value": f"{DETECTION_DELAY_SECONDS} seconds"},
                {"Setting": "Brightness Mapping", "Value": "0 people=25%; 1 person=65%; 2+ people=100%"},
            ])
            df_readme.to_excel(writer, index=False, sheet_name="Read Me")

        st.download_button(
            label="⬇️ Download Detection Log (.xlsx)",
            data=buffer.getvalue(),
            file_name=f"streetlight_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        st.caption(f"{len(df_history)} record(s) logged in current session.")
    else:
        st.info("Detection records will appear here for Excel export once detected.")

# Fragment refresh for metric updates
@st.fragment(run_every="1s")
def auto_refresh():
    pass

auto_refresh()