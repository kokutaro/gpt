from uuid import uuid4
import streamlit as st
from st_oauth import st_oauth
from db import Db
from home import docsearch

USER_NAME = "user"
ASSISTANT_NAME = "assistant"

user_id = st_oauth("azureEntraId", "Click to login")

if "chat_titles" not in st.session_state:
    with Db() as db:
        st.session_state.chat_titles = db.get_chat_titles(user_id)

if "chat_id" not in st.session_state:
    st.session_state.chat_id = str(uuid4())

if "chat_logs" not in st.session_state:
    with Db() as db:
        st.session_state.chat_logs = db.get_chat_histories(
            st.session_state.chat_id, user_id
        )

input_q = st.chat_input()

chat_logs = st.session_state.chat_logs
for chat in chat_logs:
    with st.chat_message(chat["name"]):
        st.write(chat["msg"])
    st.divider()

if input_q:
    if st.session_state.chat_id not in st.session_state.chat_titles:
        st.session_state.chat_titles[st.session_state.chat_id] = input_q

    with st.chat_message(USER_NAME):
        st.write(input_q)
    st.divider()

    res = docsearch.similarity_search_with_relevance_scores(input_q)
    base_url = "http://localhost/img"
    texts = []
    for doc, score in res:
        if not "img_ids" in doc.metadata:
            texts.extend(doc.page_content.split("\n"))
            continue
        for i, text in enumerate(doc.page_content.split("\n")):
            texts.append(text)
            for img_info in filter(
                lambda x: x["line_no"] == i, doc.metadata["img_ids"]
            ):
                url = f"{base_url}/{img_info['img_id']}"
                texts.append(f"![{img_info['img_id']}]({url})")
    text = "\n\n".join(texts)
    # text = input_q
    with st.chat_message(ASSISTANT_NAME):
        st.markdown(text)

    chat_logs.append({"name": USER_NAME, "msg": input_q})
    chat_logs.append({"name": ASSISTANT_NAME, "msg": text})

    with Db() as db:
        db.upsert_chat_history(
            st.session_state.chat_id,
            user_id,
            st.session_state.chat_titles[st.session_state.chat_id],
            chat_logs,
        )
    st.session_state.chat_logs = chat_logs


def cleate_new_chat():
    if (
        len(st.session_state.chat_logs) == 0
        and st.session_state.chat_id in st.session_state.chat_titles
    ):
        del st.session_state.chat_titles[st.session_state.chat_id]

    st.write("New chat")
    st.session_state.chat_id = str(uuid4())
    st.session_state.chat_logs = []


def set_chat_id(id):
    if (
        len(st.session_state.chat_logs) == 0
        and st.session_state.chat_id in st.session_state.chat_titles
    ):
        del st.session_state.chat_titles[st.session_state.chat_id]
    st.session_state.chat_id = id
    with Db() as db:
        st.session_state.chat_logs = db.get_chat_histories(
            st.session_state.chat_id, user_id
        )


st.session_state.get(st.session_state.chat_id)
with st.sidebar:
    st.button("Start new chat", type="primary", on_click=cleate_new_chat)
    st.header("Chat histories", divider="rainbow")
    for k, v in reversed(st.session_state.chat_titles.items()):
        st.button(
            label=v,
            key=k,
            use_container_width=True,
            on_click=set_chat_id,
            args=[k],
            disabled=k == st.session_state.chat_id,
        )
