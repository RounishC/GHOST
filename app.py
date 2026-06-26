"""
Root level Flask app for Vercel deployment - Minimal working version
"""
from flask import Flask, jsonify

# Create Flask app
app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({"message": "GHOST Route Planner", "status": "running"}), 200

@app.route('/api/health')
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(debug=False)
