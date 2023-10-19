import os
import psycopg2
from flask import Flask, render_template, request
from hashlib import sha512
from werkzeug.utils import secure_filename
from uuid import uuid4

FILE_BASE = os.environ.get("FILE_BASE", "/var/data/doc-data/")

accepts = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
]

app = Flask(__name__, static_folder="resources")

sql = """
SELECT COUNT(1) AS COUNT
FROM uploaded_documents
WHERE sha512 = %s
"""

sql_insert = """
INSERT INTO uploaded_documents
(uuid, file_name, sha512, content_type)
VALUES (%s, %s, %s, %s)
"""

sql_get_all_docs = """
SELECT uuid, file_name, sha512, content_type
FROM uploaded_documents
"""


@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        con = psycopg2.connect(
            host=os.environ.get("POSTGRES_DB_HOST", "host.docker.internal"),
            port=int(os.environ.get("POSTGRES_DB_PORT", "5432")),
            database=os.environ.get("POSTGRES_DB", "postgres"),
            user=os.environ.get("POSTGRES_USER", "postgres"),
            password=os.environ.get("POSTGRES_PASSWORD", "password"),
        )
        cur = con.cursor()
        file_statuses = []
        files = request.files.getlist("file")
        for file in files:
            file_hash = sha512(file.read()).hexdigest()
            file_name = secure_filename(file.filename)
            file_type = file.content_type

            file_status = {
                "file_name": file_name,
                "file_type": file_type,
                "file_hash": file_hash,
            }

            if not file_type in accepts:
                file_status["status"] = "Invalid file"
                file_statuses.append(file_status)
                continue

            cur.execute(sql, [file_hash])
            (count,) = cur.fetchone()
            if int(count) > 0:
                file_status["status"] = "Duplicate"
                file_statuses.append(file_status)
                continue
            uuid = str(uuid4())
            file.save(os.path.join(FILE_BASE, file_name))
            cur.execute(sql_insert, (uuid, file_name, file_hash, file_type))
            con.commit()
            file_status["status"] = "Saved"
            file_status["uuid"] = uuid
            file_statuses.append(file_status)

        return render_template("uploaded.html", file_statuses=file_statuses)
    else:
        return render_template("upload.html", accepts=",".join(accepts))


@app.route("/", methods=["GET"])
def get_file():
    con = psycopg2.connect(
        host=os.environ.get("POSTGRES_DB_HOST", "host.docker.internal"),
        port=int(os.environ.get("POSTGRES_DB_PORT", "5432")),
        database=os.environ.get("POSTGRES_DB", "postgres"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "password"),
    )
    cur = con.cursor()
    cur.execute(sql_get_all_docs)

    data = [
        {
            "uuid": uuid,
            "file_name": file_name,
            "file_hash": sha512,
            "file_type": content_type,
        }
        for uuid, file_name, sha512, content_type in cur.fetchall()
    ]
    return render_template("index.html", files=data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
