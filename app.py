from flask import Flask
from src.routes import sambaRoute
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
@app.route('/', methods=['GET'])
def index():
    return sambaRoute.greet()

@app.route('/shares', methods=['GET'])
def shares():
    return sambaRoute.get_shares()

@app.route('/start', methods=['GET'])
def status():
    return sambaRoute.get_status()

if __name__ == "__main__":
    app.run(debug=True)
