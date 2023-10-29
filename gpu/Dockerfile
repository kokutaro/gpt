FROM nvidia/cuda:12.2.2-base-ubuntu22.04

USER root

RUN apt-get update && \ 
  apt-get install -y \
  sudo \
  wget \
  git \
  vim \
  libgl1-mesa-dev \
  xpdf \
  locales \
  libreoffice \
  fonts-takao-gothic \
  python3-pip

ARG UID=1000
ARG USER_NAME=user
ARG GROUP_ID=1000
ARG GROUP_NAME=user

ENV PATH ${PATH}:/home/${USER_NAME}/.local/bin

RUN ln -s /usr/bin/python3.10 /usr/bin/python
RUN locale-gen ja_JP.UTF-8
RUN localedef -f UTF-8 -i ja_JP ja_JP

ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:jp
ENV LC_ALL ja_JP.UTF-8

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

WORKDIR /work/

ADD --chown=${USER_NAME} ./requirements.txt /work/requirements.txt

RUN set -x \
  && mkdir -p /home/${USER_NAME}/.vscode-server/extensions \
  && chown -R ${GROUP_NAME}:${USER_NAME} /home/${USER_NAME}/.vscode-server

RUN pip install --upgrade pip

EXPOSE 8090

CMD [ "/bin/bash" ]