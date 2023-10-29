from lxml import html
from pydantic import BaseModel
from typing import Any, Optional
import torch
from unstructured.partition.pdf import partition_pdf
from langchain.vectorstores.pgvector import PGVector
from langchain.schema.document import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.storage import LocalFileStore
from langchain.retrievers.multi_vector import MultiVectorRetriever
from db_util import get_connection_string
import uuid

path = "out/"
raw_pdf_elements = partition_pdf(
    filename=path + "cmd465_m.pdf",
    # Unstructured first finds embedded image blocks
    extract_images_in_pdf=True,
    # Use layout model (YOLOX) to get bounding boxes (for tables) and find titles
    # Titles are any sub-section of the document
    infer_table_structure=True,
    languages=["eng", "jpn"],
    # Post processing to aggregate text once we have the title
    chunking_strategy="by_title",
    # Chunking params to aggregate text blocks
    # Attempt to create a new chunk 3800 chars
    # Attempt to keep chunks > 2000 chars
    max_characters=4000,
    new_after_n_chars=3800,
    combine_text_under_n_chars=2000,
    image_output_dir_path=path,
)
# Create a dictionary to store counts of each type
category_counts = {}

for element in raw_pdf_elements:
    category = str(type(element))
    if category in category_counts:
        category_counts[category] += 1
    else:
        category_counts[category] = 1

# Unique_categories will have unique elements
unique_categories = set(category_counts.keys())
print(category_counts)


class Element(BaseModel):
    type: str
    text: Any


categorized_elements = []
for element in raw_pdf_elements:
    if "unstructured.documents.elements.Table" in str(type(element)):
        categorized_elements.append(Element(type="table", text=str(element)))
    elif "unstructured.documents.elements.CompositeElement" in str(type(element)):
        categorized_elements.append(Element(type="text", text=str(element)))

# Tables
table_elements = [e for e in categorized_elements if e.type == "table"]
print(len(table_elements))

# Text
text_elements = [e for e in categorized_elements if e.type == "text"]
print(len(text_elements))

tables = [bytes(i.text, "utf-8", "ERROR") for i in table_elements]
table_summaries = tables
texts = [bytes(i.text, "utf-8", "ERROR") for i in text_elements]
text_summaries = texts


MODEL_NAME = "intfloat/multilingual-e5-large"
model_kwargs = {"device": "cuda" if torch.cuda.is_available() else "cpu"}
embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME, model_kwargs=model_kwargs)

vectorstore = PGVector(
    collection_name="summaries",
    connection_string=get_connection_string(),
    embedding_function=embeddings,
)
store = LocalFileStore("docs")
id_key = "doc_id"
retriever = MultiVectorRetriever(vectorstore=vectorstore, docstore=store, id_key=id_key)

doc_ids = [str(uuid.uuid4()) for _ in texts]
summary_texts = [
    Document(page_content=s, metadata={id_key: doc_ids[i]})
    for i, s in enumerate(text_summaries)
]
retriever.vectorstore.add_documents(summary_texts)
retriever.docstore.mset(list(zip(doc_ids, texts)))

table_ids = [str(uuid.uuid4()) for _ in tables]
summary_tables = [
    Document(page_content=s, metadata={id_key: table_ids[i]})
    for i, s in enumerate(table_summaries)
]
retriever.vectorstore.add_documents(summary_tables)
retriever.docstore.mset(list(zip(table_ids, tables)))
