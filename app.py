from flask import Flask
from src.routes import sambaRoute

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return sambaRoute.greet()

@app.route('/shares')
def index():
    return sambaRoute.get_shares()



if __name__ == "__main__":
    app.run(debug=True)