# aqui debe ir todas la configuraciones que se hace en cada peticion 
from flask import jsonify

def greet():
    return 'Hola soy el API'

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
                    'comment': ''
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

        if current_share:
            shares.append(current_share)
            
    return jsonify(shares)
    

