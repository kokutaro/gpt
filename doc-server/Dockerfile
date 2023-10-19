FROM python:3.11

USER root

RUN apt update
RUN apt install -y \ 
  vim \ 
  sudo \
  less

ARG UID=1000
ARG USER_NAME=user
ARG GROUP_ID=1000
ARG GROUP_NAME=user

ENV FILE_BASE /var/data/doc-data/

RUN set -x \
  && groupadd --gid ${GROUP_ID} ${GROUP_NAME}

RUN set - x \
  && echo "$USER_NAME ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers.d/${USER_NAME} \
  && chmod 0440 /etc/sudoers.d/${USER_NAME} \
  && useradd \
  --uid ${UID} \
  --gid ${GROUP_ID} \
  --home-dir /home/${USER_NAME} \
  --create-home \
  --shell /bin/bash \
  ${USER_NAME}

USER ${UID}

ADD --chown=${USER_NAME} ./requirements.txt /work/requirements.txt

WORKDIR ${FILE_BASE}
WORKDIR /work/

RUN set -x \
  && mkdir -p /home/${USER_NAME}/.vscode-server/extensions \
  && chown -R ${GROUP_NAME}:${USER_NAME} /home/${USER_NAME}/.vscode-server

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD [ "/bin/bash" ]