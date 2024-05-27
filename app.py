from flask import Flask, request, jsonify
from src.routes import sambaRoute
from flask_cors import CORS
import pam
import os
import re

app = Flask(__name__)
CORS(app)
SMB_CONF_PATH = '/etc/samba/smb.conf'


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
    data = request.json
    act = data.get('actual')
    on = data.get('onReboot')
    res = sambaRoute.update_samba(act, on)
    print(res)
    return jsonify(res)


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

@app.route('/workgroup', methods=['GET', 'PUT'])
def workgroup():
    if request.method == 'GET':
        return sambaRoute.get_workgroup()
    elif request.method == 'PUT':
        return sambaRoute.update_workgroup()

if __name__ == "__main__":
    app.run(debug=True)

@app.route('/add_user', methods=['POST'])
def addUser():
    data = request.json
    username = data.get('name')
    password = data.get('pass')
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required'}), 400

    # Verificar si el usuario ya existe en el sistema Linux
    if not sambaRoute.user_exists(username):
        return jsonify({'success': False, 'message': f'User {username} does not exist in the system'}), 404

    # Establecer la contraseña de Samba
    samba_result = sambaRoute.set_samba_password(username, password)
    if not samba_result['success']:
        return jsonify(samba_result), 500
    print("Si se pudo wachin")
    return jsonify({'success': True, 'message': 'Samba user created successfully'})

@app.route('/samba_users', methods=['GET'])
def samba_users():
    result = sambaRoute.get_samba_users()
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500

@app.route('/delete_samba_user', methods=['DELETE'])
def delete_user():
    data = request.get_json()
    username = data.get('username')
    if not username:
        return jsonify({'success': False, 'message': 'Username is required'}), 400

    # Eliminar el usuario de Samba
    result = sambaRoute.delete_samba_user(username)
    if not result['success']:
        return jsonify(result), 500

    return jsonify({'success': True, 'message': f'Samba user {username} deleted successfully'})


@app.route('/addShare', methods=['POST'])
def add_samba_share_endpoint():
    try:
        share_config = request.json
        if 'name' not in share_config or 'path' not in share_config:
            return jsonify({"error": "The 'name' and 'path' fields are required"}), 400

        sambaRoute.add_samba_share(SMB_CONF_PATH, share_config)
        return jsonify({"message": "Samba resource successfully added"}), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": "Internal Server Error"}), 500
    
   
@app.route('/files', methods=['GET'])
def get_files():
    user = request.args.get('user')
    if not user:
        return jsonify({"error": "User parameter is required"}), 400

    home_path = f'/home/{user}'
    try:
        home_files = [f for f in os.listdir(home_path) 
                      if os.path.isdir(os.path.join(home_path, f)) and not f.startswith('.')]
        home_files = [os.path.join(home_path, f) for f in home_files]
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    return jsonify(home_files)


@app.route('/deleteAttribute', methods=['POST'])
def delete_smb_attribute():
    resource_name = request.json.get('resourceName')
    attribute_name = request.json.get('attributeName')

    if not resource_name or not attribute_name:
        return jsonify({'error': 'Nombre de recurso o atributo no especificado'}), 400

    attribute_name_formatted = re.sub(r'(?<!^)(?=[A-Z])', ' ', attribute_name).lower()

    resource_found = False

    try:
        with open('/etc/samba/smb.conf', 'r') as f:
            lines = f.readlines()

        with open('/etc/samba/smb.conf', 'w') as f:
            in_target_section = False
            for line in lines:
                if line.strip().startswith('[' + resource_name):
                    in_target_section = True
                    resource_found = True
                elif line.strip().startswith('['):
                    in_target_section = False

                if in_target_section and attribute_name_formatted in line.lower():
                    continue 
                else:
                    f.write(line)

        if not resource_found:
            return jsonify({'error': f'El recurso {resource_name} no fue encontrado en smb.conf'}), 404
        else:
            return jsonify({'message': f'Atributo {attribute_name} eliminado del recurso {resource_name} correctamente'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/addAttribute', methods=['POST'])
def add_smb_attribute():
    resource_name = request.json.get('resourceName')
    attribute_name = request.json.get('attributeName')
    attribute_value = request.json.get('attributeValue')

    if not resource_name or not attribute_name or not attribute_value:
        return jsonify({'error': 'Nombre de recurso, atributo o valor no especificado'}), 400

    attribute_name_formatted = format_attribute_name(attribute_name)

    line_to_add = f"\t{attribute_name_formatted} = {attribute_value}\n"

    resource_found = False

    try:
        with open('/etc/samba/smb.conf', 'r') as f:
            lines = f.readlines()

        with open('/etc/samba/smb.conf', 'w') as f:
            for line in lines:
                f.write(line)
                if line.strip().startswith('[' + resource_name):
                    resource_found = True
                    f.write(line_to_add)

        if not resource_found:
            return jsonify({'error': f'El recurso {resource_name} no fue encontrado en smb.conf'}), 404
        else:
            return jsonify({'message': f'Atributo {attribute_name} agregado al recurso {resource_name} correctamente'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def format_attribute_name(attribute_name):
    formatted_name = re.sub(r'(?<!^)(?=[A-Z])', ' ', attribute_name).lower()
    return formatted_name


@app.route('/updateGuest', methods=['POST'])
def update_guest_access():
    data = request.json
    share_name = data['shareName']
    guest_access = data['guestAccess']

    try:
        sambaRoute.update_guest_access(share_name, guest_access)
        return jsonify({'message': 'Guest access updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500