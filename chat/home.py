from uuid import uuid4
import streamlit as st
import torch
from st_oauth import st_oauth
from db import Db
import db_util
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores.pgvector import PGVector

MODEL_NAME = "intfloat/multilingual-e5-large"
USER_NAME = "user"
ASSISTANT_NAME = "assistant"

st.set_page_config(page_title="Home", layout="wide")

user_id = st_oauth("azureEntraId", "Click to login")


@st.cache_resource
def load_model() -> PGVector:
    model_kwargs = {"device": "cuda" if torch.cuda.is_available() else "cpu"}
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME, model_kwargs=model_kwargs)
    docsearch = PGVector(db_util.get_connection_string(), embeddings, "embedding_store")

    return docsearch


docsearch = load_model()

st.write(open("streamlit.md").read())
st.balloons()
