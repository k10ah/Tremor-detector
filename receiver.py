import serial
import json
import time
import threading
from datetime import datetime
import statistics
import os

# --- USER CONFIG ---
# Replace with your Arduino COM port
# Example: 'COM5' for Windows, '/dev/ttyUSB0' or '/dev/ttyACM0' for Linux/Mac
PORT = "COM5"
BAUD_RATE = 9600
SAVE_DIR = "data"

# --- GLOBALS ---
collecting = False
data_buffer = []

# --- SERIAL READER THREAD ---
def read_serial():
    global collecting, data_buffer
    try:
        ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
        print(f"✅ Connected to {PORT}")
    except serial.SerialException as e:
        print(f"❌ Could not open serial port {PORT}: {e}")
        return

    while True:
        if collecting:
            try:
                line = ser.readline().decode("utf-8").strip()
                if not line:
                    continue
                try:
                    sample = json.loads(line)
                    data_buffer.append(sample)
                    # Optional live print for debugging:
                    print(sample)
                except json.JSONDecodeError:
                    print(f"⚠️ Bad JSON: {line}")
            except Exception as e:
                print("⚠️ Serial read error:", e)
        else:
            time.sleep(0.1)

# --- CONTROL FUNCTIONS ---
def start_collection():
    global collecting, data_buffer
    data_buffer = []
    collecting = True
    print("▶️ Started collecting data...")

def stop_collection():
    global collecting, data_buffer
    collecting = False
    print("⏹️ Stopped collecting data.")
    if data_buffer:
        save_data()
    else:
        print("⚠️ No data to save.")

def compute_summary(data_list):
    """Compute summary statistics for accelerometer and gyro."""
    summary = {}
    for key in ["ax", "ay", "az", "gx", "gy", "gz"]:
        values = [d[key] for d in data_list if key in d]
        if values:
            summary[key] = {
                "mean": statistics.mean(values),
                "std": statistics.stdev(values) if len(values) > 1 else 0,
                "min": min(values),
                "max": max(values),
            }
    return summary

def save_data():
    """Save session data and summary to JSON file."""
    os.makedirs(SAVE_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{SAVE_DIR}/session_{timestamp}.json"

    summary = compute_summary(data_buffer)
    session_data = {
        "timestamp": timestamp,
        "num_samples": len(data_buffer),
        "summary": summary,
        "data": data_buffer,
    }

    with open(filename, "w") as f:
        json.dump(session_data, f, indent=2)

    print(f"💾 Data saved to {filename}")
    return filename

# --- MAIN ---
if __name__ == "__main__":
    # Start serial thread
    t = threading.Thread(target=read_serial, daemon=True)
    t.start()

    print("\nReceiver ready. Type:")
    print("  start - begin monitoring")
    print("  stop  - end monitoring and save JSON")
    print("  exit  - quit\n")

    while True:
        cmd = input("> ").strip().lower()
        if cmd == "start":
            start_collection()
        elif cmd == "stop":
            stop_collection()
        elif cmd == "exit":
            print("👋 Exiting receiver.")
            break
        else:
            print("Unknown command. Use 'start', 'stop', or 'exit'.")
