from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return """
    <h1>CS Research Assistant</h1>
    <p>Basic version is working!</p>
    <p>Next: Add the full functionality.</p>
    """

@app.route('/api/health')
def health():
    return jsonify({"status": "healthy", "message": "Basic app running"})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
