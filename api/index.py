from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({"message": "GHOST Route Planner", "status": "ok"}), 200

@app.route('/api/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/api/config')
def config():
    return jsonify({"azure_maps": False}), 200


