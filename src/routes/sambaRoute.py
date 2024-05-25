from flask import jsonify,request
import subprocess
import re
import json
from flask import jsonify
import subprocess
import re
import json
import configparser

SAMBA_CONFIG_FILE = '/etc/samba/smb.conf'


def greet():
    return 'Hola soy el API'

#Mostrar los recursos compartidos
def get_shares():
    shares = []
    current_share = None

    with open('/etc/samba/smb.conf', 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                if current_share and current_share['name'] != 'global':
                    shares.append(current_share)
                current_share = {
                    'name': line[1:-1],
                    'status': 'Enable', 
                    'readOnly': '',
                    'path': '',
                    'guestAccess': 'No',
                    'comment': '',
                    'validUsers': '',
                    'browseable': '',
                    'inheritAcls': '',
                    'createMask': '',
                    'directoryMask': '',
                    'writeList': '',
                    'forceGroup': '',
                    'printable': '',
                    'vetoFiles': ''

                }

            elif '=' in line and current_share:
                key, value = [x.strip() for x in line.split('=', 1)]
                if key == 'path':
                    current_share['path'] = value
                elif key == 'read only':
                    current_share['readOnly'] = value
                elif key == 'guest ok':
                    current_share['guestAccess'] = 'Yes' if value.lower() == 'yes' else 'No'
                elif key == 'comment':
                    current_share['comment'] = value
                elif key == 'valid users':
                    current_share['validUsers'] = value
                elif key == 'browseable':
                    current_share['browseable'] = value
                elif key == 'inherit acls':
                    current_share['inheritAcls'] = value
                elif key == 'create mask':
                    current_share['createMask'] = value
                elif key == 'directory mask':
                    current_share['directoryMask'] = value
                elif key == 'write list':
                    current_share['writeList'] = value
                elif key == 'force group':
                    current_share['forceGroup'] = value
                elif key == 'printable':
                    current_share['printable'] = value
                elif key == 'veto files':
                    current_share['vetoFiles'] = value


        if current_share:
            shares.append(current_share)
    return jsonify(shares)

#Cambiar de nombre de recurso
def rename_share(old_name, new_name):
    with open('/etc/samba/smb.conf', 'r') as file:
        lines = file.readlines()

    with open('/etc/samba/smb.conf', 'w') as file:
        for line in lines:
            if line.strip().startswith('[') and line.strip().endswith(']'):
                share_name = line.strip()[1:-1]
                if share_name == old_name:
                    line = f"[{new_name}]\n"
            file.write(line)

def get_status():
    try:
        # Ejecuta el comando `systemctl is-active smb`
        result = subprocess.run(['systemctl', 'is-active', 'smbd.service'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        
        # Captura la salida y limpia los espacios en blanco
        output = result.stdout.strip()
        
        # Verifica si el comando se ejecutó correctamente y si el servicio está activo
        if result.returncode == 0 and output == 'active':
            return jsonify({
                'success': True,
                'status': 'active'
            })
        else:
            return jsonify({
                'success': True,
                'status': output
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


def load_config():
    with open(SAMBA_CONFIG_FILE, 'r') as file:
        return file.readlines()

def save_config(config_lines):
    with open(SAMBA_CONFIG_FILE, 'w') as file:
        file.writelines(config_lines)

def update_share_config(share_name, updates):
    config_lines = load_config()
    share_section = False
    updated_lines = []
    share_found = False

    for line in config_lines:
        if line.strip().startswith('['):
            current_section = line.strip().strip('[]')
            share_section = current_section == share_name

        if share_section:
            share_found = True
            key_value_match = re.match(r'(\s*([^=]+)\s*=\s*(.*))', line)
            if key_value_match:
                full_line, key, value = key_value_match.groups()
                key = key.strip()
                if key in updates:
                    value = updates[key]
                    updated_lines.append(f"{key} = {value}\n")
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)

    if not share_found:
        return False

    save_config(updated_lines)
    return True

def from_camel_case(s):
    return re.sub(r'([a-z])([A-Z])', r'\1 \2', s).lower()

def parse_json(data):
    try:
        json_data = json.loads(data)
    except json.JSONDecodeError as e:
        raise ValueError("Error parsing JSON data: " + str(e))

    transformed_data = {}
    for key, value in json_data.items():
        transformed_key = from_camel_case(key)
        transformed_data[transformed_key] = value

    return transformed_data
  
def get_enableAtBoot():
    try:
        # Ejecuta el comando `systemctl is-active smb`
        result = subprocess.run(['systemctl', 'is-enabled', 'smbd.service'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        
        # Captura la salida y limpia los espacios en blanco
        output = result.stdout.strip()
        
        # Verifica si el comando se ejecutó correctamente y si el servicio está activo
        if result.returncode == 0 and output == 'active':
            return jsonify({
                'success': True,
                'status': 'enabled'
            })
        else:
            return jsonify({
                'success': True,
                'status': output
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })
def update_samba(action):
    try:
        # Mapa de acciones a comandos systemctl
        commands = {
            'stop': 'systemctl stop smb',
            'restart': 'systemctl restart smb',
            'reload': 'systemctl reload smb'
        }
        # Verifica si la acción es válida
        if action in commands:
            # Ejecuta el comando correspondiente
            result = subprocess.run(commands[action], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': f'Samba service {action}ed successfully.',
                    'output': result.stdout.strip()
                }
            else:
                return {
                    'success': False,
                    'message': f'Failed to {action} Samba service.',
                    'error': result.stderr.strip()
                }
        else:
            return {
                'success': False,
                'message': 'Invalid action. Please use "stop", "restart", or "reload".'
            }
    except Exception as e:
        return {
            'success': False,
            'message': 'An error occurred while updating the Samba service.',
            'error': str(e)
        }

def delete_samba_share(share_name):
    try:
        with open(SAMBA_CONFIG_FILE, 'r') as file:
            lines = file.readlines()

        start_idx = None
        end_idx = None

        for i, line in enumerate(lines):
            if line.strip().startswith(f"[{share_name}]"):
                start_idx = i
                break

        if start_idx is None:
            return False, f"Share '{share_name}' not found."

        for i in range(start_idx + 1, len(lines)):
            if lines[i].strip().startswith('['):
                end_idx = i
                break
        if end_idx is None:
            end_idx = len(lines)

        new_lines = lines[:start_idx] + lines[end_idx:]

        with open(SAMBA_CONFIG_FILE, 'w') as file:
            file.writelines(new_lines)

        return True, f"Share '{share_name}' successfully deleted."
    except Exception as e:
        return False, str(e)

def get_workgroup():
    try:
        with open(SAMBA_CONFIG_FILE, 'r') as file:
            for line in file:
                if line.strip().startswith('workgroup'):
                    _, workgroup = line.strip().split('=', 1)
                    workgroup = workgroup.strip()
                    return jsonify({'workgroup': workgroup}), 200
        return jsonify({'error': 'Workgroup not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def update_workgroup():
    try:
        new_workgroup = request.json.get('workgroup')
        if new_workgroup:
            success, message = update_workgroup_config(new_workgroup)
            if success:
                return jsonify({'success': True, 'message': message}), 200
            else:
                return jsonify({'success': False, 'error': message}), 500
        else:
            return jsonify({'success': False, 'error': 'No workgroup provided in request'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def update_workgroup_config(new_workgroup):
    try:
        lines = []
        with open(SAMBA_CONFIG_FILE, 'r') as file:
            lines = file.readlines()

        with open(SAMBA_CONFIG_FILE, 'w') as file:
            for i, line in enumerate(lines):
                if line.strip().startswith('workgroup'):
                    lines[i] = f'        workgroup = {new_workgroup}\n'
                    break

            file.writelines(lines)

        return True, 'Workgroup updated successfully'
    except Exception as e:
        return False, str(e)


  

