from flask import Flask, request, jsonify
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

@app.route('/renameShare', methods=['POST'])
def rename_share_route():
    data = request.json
    old_name = data['oldName']
    new_name = data['newName']
    sambaRoute.rename_share(old_name, new_name)

    return jsonify({'message': 'Share renamed succesfully'})

@app.route('/start', methods=['GET'])
def status():
    return sambaRoute.get_status()


if __name__ == "__main__":
    app.run(debug=True)
