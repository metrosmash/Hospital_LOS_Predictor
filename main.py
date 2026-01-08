from flask import Flask
from markupsafe import escape
from flask import request
app = Flask(__name__)

@app.route("/")
def hello():
    name = request.args.get("name", "Flask")
    return f"Hello,{escape(name)}"
deactivate
if __name__ == '__main__':
    app.run(debug=True)