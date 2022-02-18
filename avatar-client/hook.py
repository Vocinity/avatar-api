#!/usr/bin/python3
import os

from flask_cors import CORS
from flask import Flask, request, jsonify, Response
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = "uploads/"
app.secret_key = os.urandom(42)
CORS(app)

allowed_extensions = set(['mp4', 'webm'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


@app.route("/avatar", methods = ['POST'])
def download_avatar():
    if 'file' not in request.files:
        resp = jsonify({'message' : 'No file parameter'})
        resp.status_code = 400
        return resp

    file = request.files['file']
    if file.filename == '':
        resp = jsonify({'message' : 'file parameter found, but is empty'})
        resp.status_code = 400
        return resp

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        resp = jsonify({'message' : 'file uploaded'})
        resp.status_code = 201
        return resp
    else:
        resp = jsonify({'message' : 'This file type is not allowed'})
        resp.status_code = 400
        return resp

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8085, debug=True)
