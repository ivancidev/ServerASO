from flask import Flask, request, jsonify
from src.routes import sambaRoute
from flask_cors import CORS
import pam

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

@app.route('/enable', methods=['GET'])
def enable():
    return sambaRoute.get_enableAtBoot()

@app.route('/update_samba', methods=['POST'])
def updateSamba():
    data = request.get_json()
    action = data.get('action')
    onReboot = data.get('onReboot')
    result = sambaRoute.update_samba(action)
    return jsonify(result)

@app.route('/login', methods=['POST'])
def login():
        username = request.json['username']
        password = request.json['password']
        if authenticate(username, password):
            return jsonify({'message': 'Login successful'}), 200
        else:
            return jsonify({'error': 'Login failed'}), 401

def authenticate(username, password):
    p = pam.pam()
    return p.authenticate(username, password)

@app.route('/shares/<share_name>', methods=['PUT'])
def update_share(share_name):
    updates = request.data.decode('utf-8')

    try:
        updates_json = sambaRoute.parse_json(updates)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    if sambaRoute.update_share_config(share_name, updates_json):
        return jsonify({"status": "success", "updated": updates_json})
    else:
        return jsonify({"status": "error", "message": "Share not found"}), 404

@app.route('/deleteShare', methods=['POST'])
def delete_share():
    data = request.json
    share_name = data.get('share_name')

    if not share_name:
        return jsonify({"error": "Share name not provided."}), 400

    success, message = sambaRoute.delete_samba_share(share_name)
    
    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 500

if __name__ == "__main__":
    app.run(debug=True)
