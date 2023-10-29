from hashlib import sha512
import os
from uuid import uuid4
import streamlit as st
import doc_loader
from util import get_safe_filename
from config import Config
from st_oauth import st_oauth
from db import Db
from home import docsearch

user_id = st_oauth("azureEntraId", "Click to login")

uploaded_files = []
file_statuses = []

uploaded_files = st.file_uploader(
    "Choose a file",
    accept_multiple_files=True,
    type=Config.FILE_TYPES,
)

for uploaded_file in uploaded_files:
    bytes_data = uploaded_file.read()
    file_hash = sha512(bytes_data).hexdigest()
    file_name = get_safe_filename(uploaded_file.name)
    file_type = uploaded_file.type
    file_status = {
        "file_name": file_name,
        "file_type": file_type,
    }

    if not file_type in Config.ACCEPTS:
        file_status["status"] = "Invalid file type"
        file_statuses.append(file_status)
        continue

    with Db() as db:
        if db.doc_exists(file_hash):
            file_status["status"] = "File duplicates"
            file_statuses.append(file_status)
            continue
        uuid = str(uuid4())
        db.insert_doc(uuid, file_name, file_hash, file_type)

    file_path = os.path.join(Config.FILE_BASE, file_name)
    with open(file_path, "wb") as f:
        f.write(bytes_data)

    docs = doc_loader.load_documents(file_path, uuid)
    docsearch.add_documents(docs)
    file_status["status"] = "Saved"
    file_status["uuid"] = uuid
    file_statuses.append(file_status)

if len(file_statuses) > 0:
    st.dataframe(file_statuses)
