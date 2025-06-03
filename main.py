from flask import Flask, request
from flask_cors import CORS
from translator import get_translation_and_vertices


app = Flask(__name__)
CORS(app)


@app.route("/api/translate", methods=["POST"])
def translate():
    print("start")
    img_file = request.files["screen"]
    img_data = img_file.read()
    if img_file.filename == "":
        return {"error": "No file provided"}, 400
    ret = get_translation_and_vertices(img_data)
    return {"result": ret}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8020)
