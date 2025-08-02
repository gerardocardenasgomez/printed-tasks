import random
from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics
from datetime import datetime

from ascii_art import RANDOM_RECEIPT_ART

from escpos.printer import Usb

app = Flask(__name__)
metrics = PrometheusMetrics(app)

@app.route("/")
def hello():
    return jsonify(message="Hello from the Python microservice wow")

@app.route("/print_task", methods=["POST"])
@metrics.counter('printer_invocations_total', 'Total number of printer invocations.',
                 labels={'endpoint': '/print'})
def print_task():
    try:
        data = request.get_json()
        if not data or "task_description" not in data:
            return jsonify({"error":"Missing task_description in JSON payload"}), 400
        if "task_name" not in data:
            return jsonify({"error":"Missing task_name in JSON payload"}), 400
        if "priority" not in data:
            return jsonify({"error":"Missing priority in JSON payload"}), 400
        task_name = data['task_name']
        task_description = data['task_description']
        priority = data['priority']
        print(f"Received task: {task_name} with desc: {task_description}")
    except Exception as e:
        print("Error: ", e)
        return jsonify({"error":"Something went wrong trying to get data"}), 400
    try:
        p = Usb(0x0FE6, 0x811E, 0, profile="simple")
        if p is None:
            print("could not init printer")
            return jsonify({"error":"printer experienced an error"}), 503
        selected_art = random.choice(RANDOM_RECEIPT_ART)
        p.text(f"ADVANCED TASK MANAGEMENT SYSTEM v0.01\n")
        p.text(f"TASK: {task_name}\n")
        p.text(f"TASK_DESC: {task_description}\n")
        p.text("\n")
        p.text(f"PRIORITY: {priority}")
        p.text("\n")
        p.text(f"PRINTED ON: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        p.text("\n")
        p.text(selected_art)
        p.text("\n")
        p.cut()
        p.close()
        print(f"Printed {task_name}")
    except Exception as e:
        print("Error: ", e)
        return jsonify({"error":"there was a heck up :("}), 501
    return jsonify({"message":"Task was added!"}), 200
