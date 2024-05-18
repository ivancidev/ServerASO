# aqui debe ir todas la configuraciones que se hace en cada peticion 
from flask import jsonify

def greet():
    return 'Hola soy el API'

# mostrar recursos compartidos
def get_shares():
    shares = []
    with open('/etc/samba/smb.conf', 'r') as file:
        for line in file:
            if line.startswith('['):
                share_name = line.strip()[1:-1]
                shares.append(share_name)
    return jsonify(shares)
    

