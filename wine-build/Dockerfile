FROM tobix/pywine:3.9

RUN apt-get update
RUN apt-get install -y git

RUN mkdir /build
RUN mkdir /opt/wineprefix/drive_c/build

COPY build-wine-docker.sh /build/build-wine-docker.sh
COPY entrypoint.sh /build/entrypoint.sh

ENTRYPOINT ["/build/entrypoint.sh"]


