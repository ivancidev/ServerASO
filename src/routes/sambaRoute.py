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
def update_samba(action, onReboot):
    try:
        # Mapa de acciones a comandos systemctl
        commands = {
            'stop': 'systemctl stop smbd.service',
            'restart': 'systemctl restart smbd.service',
            'reload': 'systemctl reload smbd.service',
            'enabled': 'systemctl enable smbd.service',
            'disabled': 'systemctl disable smbd.service'
        }
        if action in commands:
            action_result = execute_command(commands[action])
        else:
            return {
                'success': False,
                'message': 'Invalid action. Please use "stop", "restart", or "reload".'
            }
        if onReboot in commands:
            boot_result = execute_command(commands[onReboot])
        else:
            return {
                'success': False,
                'message': 'Invalid boot action. Please use "enable" or "disable".'
            }
        return {
            'success': True,
            'action_result': action_result,
            'boot_result': boot_result
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
    
    
def format_key(key):
    formatted_key = ''
    for i, char in enumerate(key):
        if i > 0 and char.isupper():
            formatted_key += ' ' + char.lower()
        else:
            formatted_key += char
    return formatted_key

def add_samba_share(config_path, share_config):
    config = configparser.ConfigParser(allow_no_value=True)
    config.optionxform = str  
    config.read(config_path)

    if config.has_section(share_config['name']):
        raise ValueError(f"Share {share_config['name']} already exists")

    config.add_section(share_config['name'])

    for key, value in share_config.items():
        if key != 'name': 
            formatted_key = format_key(key)
            config.set(share_config['name'], formatted_key, value)

    with open(config_path, 'w') as configfile:
        config.write(configfile)

def execute_command(command):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if result.returncode == 0:
        return {
            'success': True,
            'output': result.stdout.strip()
        }
    else:
        return {
            'success': False,
            'error': result.stderr.strip()
        }

