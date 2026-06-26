from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return {"message": "GHOST Route Planner", "status": "ok"}, 200

@app.route('/api/health')  
def health():
    return {"status": "healthy"}, 200


