import streamlit as st
from ultralytics import YOLO
import cv2
from PIL import Image
import numpy as np
import pyttsx3
import time
import pythoncom

# --------------------------
# TTS Function (with COM fix)
# --------------------------
def speak_label(text):
    pythoncom.CoInitialize()
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.say(text)
    engine.runAndWait()
    pythoncom.CoUninitialize()

# --------------------------
# Load YOLO model
# --------------------------
model = YOLO(r"C:\Users\porje\Downloads\best (1).pt")  # Replace with your actual model path

# --------------------------
# Streamlit Page Setup
# --------------------------
st.set_page_config(layout="wide")
st.markdown("<h2 style='text-align: center; color: red; padding-top: 0rem;'>YOLO based Traffic Sign Detection for Autonomous Vehicles</h2>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# --------------------------
# Initialize session state
# --------------------------
if 'mode' not in st.session_state:
    st.session_state.mode = None
if 'uploaded_image' not in st.session_state:
    st.session_state.uploaded_image = None

# --------------------------
# Buttons to select mode
# --------------------------
cols = st.columns([1, 1, 1, 1])  # Centered layout
with cols[1]:
    if st.button("📷 Upload Image"):
        st.session_state.mode = "image"
with cols[2]:
    if st.button("🎥 Start Real-Time Video"):
        st.session_state.mode = "video"

# --------------------------
# IMAGE MODE
# --------------------------
if st.session_state.mode == "image":
    uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        st.session_state.uploaded_image = Image.open(uploaded_file)

    if st.session_state.uploaded_image:
        st.image(st.session_state.uploaded_image, width=150, caption="Uploaded Image")

        # Show "Predict Sign" button
        if st.button("🔍 Predict Sign"):
            img_array = cv2.cvtColor(np.array(st.session_state.uploaded_image.convert("RGB")), cv2.COLOR_RGB2BGR)
            results = model(img_array, conf=0.25)[0]

            # Find and speak only the most confident detection
            if results.boxes:
                best_box = max(results.boxes, key=lambda b: float(b.conf[0]))
                cls_id = int(best_box.cls[0])
                conf = float(best_box.conf[0])
                label = model.names[cls_id]

                st.markdown(f"🟢 **Predicted sign is:** `{label}` (Confidence: {conf:.2f})")
                speak_label(f"Detected traffic sign is {label}")
            else:
                st.warning("⚠️ No traffic sign detected. Try another image or reduce confidence threshold.")

# --------------------------
# VIDEO MODE
# --------------------------
if st.session_state.mode == "video":
    st.session_state.video_running = True
    run_video = st.empty()
    stop_btn = st.button("🛑 Stop Video")

    cap = cv2.VideoCapture(0)
    spoken_labels = set()

    while cap.isOpened() and st.session_state.video_running:
        ret, frame = cap.read()
        if not ret:
            st.error("Webcam not available.")
            break

        # Check if stop button clicked
        if stop_btn:
            st.session_state.video_running = False
            break

        results = model(frame, conf=0.25)[0]
        annotated_frame = results.plot()
        resized_frame = cv2.resize(annotated_frame, (300, int(annotated_frame.shape[0] * 300 / annotated_frame.shape[1])))
        run_video.image(resized_frame, channels="BGR")

        for box in results.boxes:
            cls = int(box.cls[0])
            label = model.names[cls]

            if label not in spoken_labels:
                spoken_labels.add(label)
                speak_label(f"Detected traffic sign is {label}")
                time.sleep(0.5)

    cap.release()
    run_video.empty()
    st.success("Video stopped.")
