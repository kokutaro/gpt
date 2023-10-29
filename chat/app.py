import os
import torch
import db_util
import doc_loader
from hashlib import sha512
from uuid import uuid4
from config import Config
from db import Db
from flask import Flask, render_template, request, send_file
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores.pgvector import PGVector

from util import get_safe_filename

MODEL_NAME = "intfloat/multilingual-e5-large"

model_kwargs = {"device": "cuda" if torch.cuda.is_available() else "cpu"}
embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME, model_kwargs=model_kwargs)
docsearch = PGVector(db_util.get_connection_string(), embeddings, "embedding_store")

app = Flask(__name__)


@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "GET":
        return render_template("upload.html", accepts=",".join(Config.ACCEPTS))

    file_statuses = []
    files = request.files.getlist("file")
    with Db() as db:
        for file in files:
            file_bin = file.read()
            file_hash = sha512(file_bin).hexdigest()
            file_name = get_safe_filename(file.filename)
            file_type = file.content_type

            file_status = {
                "file_name": file_name,
                "file_type": file_type,
                "file_hash": file_hash,
            }

            if not file_type in Config.ACCEPTS:
                file_status["status"] = "Invalid file"
                file_statuses.append(file_status)
                continue

            if db.doc_exists(file_hash):
                file_status["status"] = "Duplicate"
                file_statuses.append(file_status)
                continue
            uuid = str(uuid4())
            file_path = os.path.join(Config.FILE_BASE, file_name)
            with open(file_path, "wb") as f:
                f.write(file_bin)
            db.insert_doc(uuid, file_name, file_hash, file_type)
            documents = doc_loader.load_documents(file_path, uuid)
            docsearch.add_documents(documents)
            file_status["status"] = "Saved"
            file_status["uuid"] = uuid
            file_statuses.append(file_status)

    return render_template("uploaded.html", file_statuses=file_statuses)


@app.route("/img/<uuid:id>", methods=["GET"])
def get_file(id):
    img_path = os.path.join(Config.FILE_BASE, "img", f"{str(id)}.png")
    return send_file(img_path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
