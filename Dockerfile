FROM python:3.11.5-slim-bookworm

ARG S6_OVERLAY_VERSION=3.1.6.2 LAVALINK_VERSION=3.7.10 DEBIAN_FRONTEND="noninteractive" 

ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz /tmp
ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-x86_64.tar.xz /tmp
ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-symlinks-noarch.tar.xz /tmp
ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-symlinks-arch.tar.xz /tmp

RUN apt-get update && \
  apt-get install -y git curl jq openjdk-17-jre-headless xz-utils && \
  apt-get clean && \
  tar -C / -Jxpf /tmp/s6-overlay-noarch.tar.xz && \
  tar -C / -Jxpf /tmp/s6-overlay-x86_64.tar.xz && \
  tar -C / -Jxpf /tmp/s6-overlay-symlinks-noarch.tar.xz && \
  tar -C / -Jxpf /tmp/s6-overlay-symlinks-arch.tar.xz && \
  groupadd -g 1200 lava && \
  useradd lava --system --gid 1200 --uid 1200 --create-home && \
  mkdir /lava && \
  chown 1200:1200 /lava

COPY --chown=1200:1200 . /lava
WORKDIR /lava
USER lava
RUN rm ./docker -r && \
  python -m pip install -r /lava/requirements.txt && \
  curl -fsSL https://github.com/lavalink-devs/Lavalink/releases/download/${LAVALINK_VERSION}/Lavalink.jar -o /lava/lavalink.jar

USER root
ENV S6_VERBOSITY=1 \
  S6_BEHAVIOUR_IF_STAGE2_FAILS=2 \
  S6_CMD_WAIT_FOR_SERVICES_MAXTIME=0 \
  SHELL=/bin/bash
COPY --chmod=755 ./docker /

ENTRYPOINT ["/init"]
