from flask import Flask, render_template, redirect, url_for, request
from flask_socketio import SocketIO, emit
import time, random
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Landing page
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # collect user info
        user_info = {
            'name': request.form['name'],
            'age': request.form['age'],
            'gender': request.form['gender'],
            'doctor': request.form['doctor']
        }
        return render_template('dashboard.html', user=user_info)
    return render_template('index.html')

# Simulate real-time data
def generate_data():
    while True:
        data = {
            'ax': random.uniform(-2, 2),
            'ay': random.uniform(-2, 2),
            'az': random.uniform(-2, 2),
            'gx': random.uniform(-250, 250),
            'gy': random.uniform(-250, 250),
            'gz': random.uniform(-250, 250),
            'fft': random.uniform(0, 1),
            'label': random.choice(['Normal', 'Hypoglycemia Tremor', 'Hypnic Jerks']),
            'prob': round(random.uniform(0.7, 0.99), 2)
        }
        socketio.emit('prediction', data)
        socketio.sleep(0.5)

# Start background thread
threading.Thread(target=generate_data, daemon=True).start()

if __name__ == '__main__':
    socketio.run(app, debug=True)
