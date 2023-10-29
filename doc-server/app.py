import os
from werkzeug.routing import Rule
from dotenv import load_dotenv
from flask_dance.contrib.azure import make_azure_blueprint, azure
from flask import Blueprint, Flask, redirect, render_template, request, url_for, session
from flask_paginate import get_page_parameter, Pagination
from werkzeug.middleware.proxy_fix import ProxyFix
from hashlib import sha512
from util import get_safe_filename
from uuid import uuid4
from config import Config
from db import Db

load_dotenv()

app = Flask(
    __name__,
    static_folder=Config.STATIC_FOLDER_PATH,
    static_url_path=Config.get_static_url_path(),
)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.secret_key = os.environ.get("SECRET_KEY")

blueprint = make_azure_blueprint(
    client_id=os.environ.get("CLIENT_ID"),
    client_secret=os.environ.get("CLIENT_SECRET"),
    tenant=os.environ.get("TENANT"),
    redirect_to="get_file",
)

if not Config.APP_ROOT is None:

    class CustomRuleForBasePath(Rule):
        def __init__(self, string, *args, **kwargs):
            # check if APP_ROOT endswith '/'
            if Config.APP_ROOT.endswith("/"):
                prefix_without_end_slash = Config.APP_ROOT.rstrip("/")
            else:
                prefix_without_end_slash = Config.APP_ROOT
            # check if APP_ROOT startswith '/'
            if Config.APP_ROOT.startswith("/"):
                prefix = prefix_without_end_slash
            else:
                prefix = "/" + prefix_without_end_slash
            super(CustomRuleForBasePath, self).__init__(
                prefix + string, *args, **kwargs
            )

    app.url_rule_class = CustomRuleForBasePath

app.register_blueprint(blueprint, url_prefix="/login")


@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if not azure.authorized:
        return redirect(url_for("azure.login"))
    resp = azure.get("/v1.0/me")
    assert resp.ok
    if request.method == "GET":
        return render_template(
            "upload.html", accepts=",".join(Config.ACCEPTS), user=resp.json()
        )
    with Db() as db:
        file_statuses = []
        files = request.files.getlist("file")
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
            with open(os.path.join(Config.FILE_BASE, file_name), "wb") as f:
                f.write(file_bin)
            # file.save(os.path.join(Config.FILE_BASE, file_name))
            db.insert_doc(uuid, file_name, file_hash, file_type)
            file_status["status"] = "Saved"
            file_status["uuid"] = uuid
            file_statuses.append(file_status)

    return render_template(
        "uploaded.html", file_statuses=file_statuses, user=resp.json()
    )


@app.route("/logoff")
def logoff():
    if "azure_oauth_token" in session:
        del session["azure_oauth_token"]
    if "azure_oauth_state" in session:
        del session["azure_oauth_state"]
    return redirect(url_for("get_file"))


@app.route("/", methods=["GET"])
def get_file():
    if not azure.authorized:
        return redirect(url_for("azure.login"))

    page = request.args.get(get_page_parameter(), type=int, default=1)
    resp = azure.get("/v1.0/me")
    assert resp.ok
    with Db() as db:
        (count, data) = db.get_docs(page, 20)

    pagination = Pagination(
        page=page, total=count, per_page=20, css_framework="bootstrap5"
    )
    return render_template(
        "index.html", files=data, user=resp.json(), pagination=pagination
    )


@app.route("/<guid:id>", methods=["GET"])
def get_file_by_id(id):
    # TODO: Implement
    ...


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
