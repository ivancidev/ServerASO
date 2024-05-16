from flask import Flask
from src.routes import sambaRoute

app = Flask(__name__)

@app.route('/')
def index():
    return sambaRoute.greet()


if __name__ == "__main__":
    app.run(debug=True)