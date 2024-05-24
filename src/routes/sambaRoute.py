from flask import jsonify
import subprocess

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
                    'readOnly': 'Yes',
                    'path': '',
                    'guestAccess': 'No',
                    'comment': '',
                    'validUsers': '',
                    'browseable': '',
                    'inheritAcls': '',
                    'createMask': '',
                    'directoryMask': '',
                    'writeList': '',
                    'forceGroup': ''

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
        result = subprocess.run(['systemctl', 'is-active', 'smb'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        
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