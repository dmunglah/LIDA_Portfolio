FROM deeplabcut/deeplabcut:2.3.5-base-cuda11.7.1-cudnn8-runtime-ubuntu20.04-latest AS base
RUN apt-get update && apt-get install -y ffmpeg=7:4.2.7-0ubuntu0.1 libsm6=2:1.2.3-1 libxext6=2:1.3.4-0ubuntu1 libegl1=1.3.2-1~ubuntu0.20.04.2 x11-apps=7.7+8 libxkbcommon-x11-0=0.10.0-1 libxcb-icccm4=0.4.1-1.1 build-essential=12.8ubuntu1.1 libxcb-image0=0.4.0-1build1 libxcb-keysyms1=0.4.0-1build1 libxcb-randr0-dev=1.14-2 libxcb-render-util0=0.3.9-1build1

FROM base AS dlc
RUN pip install 'deeplabcut[gui]'
ENV XDG_RUNTIME_DIR='/tmp/runtime-root' 