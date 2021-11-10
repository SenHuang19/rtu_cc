FROM senhuang/pyfmi

MAINTAINER Sen

# Installing EnergyPlus 
ENV ENERGYPLUS_VERSION 9.0.1
ENV ENERGYPLUS_TAG v9.0.1
ENV ENERGYPLUS_SHA bb7ca4f0da
ENV ENERGYPLUS_INSTALL_VERSION 9-0-1
ENV ENERGYPLUS_DOWNLOAD_BASE_URL https://github.com/NREL/EnergyPlus/releases/download/$ENERGYPLUS_TAG
ENV ENERGYPLUS_DOWNLOAD_FILENAME EnergyPlus-$ENERGYPLUS_VERSION-$ENERGYPLUS_SHA-Linux-x86_64.sh
ENV ENERGYPLUS_DOWNLOAD_URL $ENERGYPLUS_DOWNLOAD_BASE_URL/$ENERGYPLUS_DOWNLOAD_FILENAME

RUN apt-get update --allow-releaseinfo-change && apt-get install -y ca-certificates curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -SLO $ENERGYPLUS_DOWNLOAD_URL \
    && chmod +x $ENERGYPLUS_DOWNLOAD_FILENAME \
    && echo "y\r" | ./$ENERGYPLUS_DOWNLOAD_FILENAME \
    && rm $ENERGYPLUS_DOWNLOAD_FILENAME \
    && cd /usr/local/EnergyPlus-$ENERGYPLUS_INSTALL_VERSION \
    && rm -rf DataSets Documentation ExampleFiles WeatherData MacroDataSets PostProcess/convertESOMTRpgm \
    PostProcess/EP-Compare PreProcess/FMUParser PreProcess/ParametricPreProcessor PreProcess/IDFVersionUpdater

# Remove the broken symlinks
RUN cd /usr/local/bin \
    && find -L . -type l -delete

RUN pip install --user flask-restful pandas requests psutil

RUN mkdir /home/developer

RUN mkdir /home/developer/idf

RUN mkdir /home/developer/idf/output

COPY web.py /home/developer/idf/

COPY config /home/developer/idf/config

COPY output.py /home/developer/idf/

COPY wrapper.py /home/developer/idf/

COPY template /home/developer/idf/template

COPY wea /home/developer/idf/wea

WORKDIR /home/developer/idf

CMD python web.py
