import os
import chainlit as cl
import db_util
import torch
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores.pgvector import PGVector
from uuid import uuid4
from chainlit.input_widget import Select
import runhouse as rh
import doc_loader

MODEL_NAME = "intfloat/multilingual-e5-large"

max_size_mb = int(os.environ.get("MAX_SIZE_MB", 10))
max_files = int(os.environ.get("MAX_FILES", 4))

model_kwargs = {"device": "cuda" if torch.cuda.is_available() else "cpu"}
embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME, model_kwargs=model_kwargs)

docsearch = PGVector(db_util.get_connection_string(), embeddings, "embedding_store")


@cl.on_message
async def main(message: cl.Message):
    # message.content
    res = await docsearch.asimilarity_search_with_relevance_scores(message.content)
    base_url = "http://localhost:8081/img"
    texts = []
    for doc, score in res:
        if not "img_ids" in doc.metadata:
            texts = doc.page_content.split("\n")
            continue
        for i, text in enumerate(doc.page_content.split("\n")):
            texts.append(text)
            for img_info in filter(
                lambda x: x["line_no"] == i, doc.metadata["img_ids"]
            ):
                url = f"{base_url}/{img_info['img_id']}"
                texts.append(f"![{img_info['img_id']}]({url})")
    # Do any post processing here
    # Send the response
    await cl.Message(content="\n".join(texts)).send()
