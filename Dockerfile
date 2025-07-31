# Base stage with common dependencies, try 24.04
#FROM ubuntu:22.04 AS base
FROM  nvidia/cuda:12.9.1-cudnn-devel-ubuntu24.04 AS base
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

RUN apt-get update && apt-get install -y --no-install-recommends \
    autoconf \
    bc \
    bzip2 \
    build-essential \
    curl \
    cython3 \
    file \
    git \
    jq \
    libatomic1 \
    libfontconfig1 \
    libfreetype6 \
    libgl1-mesa-dev \
    libgl1-mesa-dri \
    libglib2.0-0 \
    libglu1-mesa-dev \
    libgomp1 \
    libice6 \
    libsm6 \
    python3-matplotlib \
    python3-numpy \
    python3-pandas \
    python3-scipy \
    libopenblas-dev \
    libtbbmalloc2 \
    libtool \
    libxcursor1 \
    libxext6 \
    libxft2 \
    libxinerama1 \
    libxrandr2 \
    libxrender1 \
    libxt6 \
    python3-full \
    python3-pip \
    python3-venv \
    sudo \
    unzip \
    wget \
    vim \
    xvfb \
    zip

    #libtbb2 \
    #libopenblas-base \

COPY ca-certificates/ /usr/local/share/ca-certificates/
RUN update-ca-certificates

# FSL stage
#FROM base AS fsl
#RUN curl -fsSL https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/releases/fslinstaller.py | \
#    python3 - -d /opt/fsl-6.0.7.1 -V 6.0.7.1
#
#COPY ./fsl-6.0.7.1 /opt/fsl-6.0.7.1/

# ANTs stage
FROM base AS ants
RUN mkdir /opt/ants && \
    curl -fsSL https://github.com/ANTsX/ANTs/releases/download/v2.5.4/ants-2.5.4-ubuntu-22.04-X64-gcc.zip -o ants.zip && \
    unzip ants.zip -d /opt && \
    chmod +x /opt/ants-2.5.4/bin/*

# Final stage
FROM base AS final

COPY --from=ants /opt/ /opt/

ENV ANTSPATH="/opt/ants-2.5.4/bin"
ENV FLYWHEEL="/flywheel/v0"
ENV FSLDIR="/opt/fsl-6.0.7.1"
ENV PATH="$FSLDIR/bin:$ANTSPATH:$PATH"
ENV FSLOUTPUTTYPE="NIFTI_GZ"
ENV FSLMULTIFILEQUIT="TRUE"
ENV FSLTCLSH="$FSLDIR/bin/fsltclsh"
ENV FSLWISH="$FSLDIR/bin/fslwish"
#ENV FSLLOCKDIR=""
#ENV FSLMACHINELIST=""
#ENV FSLREMOTECALL=""
ENV FSLGECUDAQ="cuda.q"
ENV MKL_NUM_THREADS=1
ENV OMP_NUM_THREADS=1
ENV PYTHONNOUSERSITE=1
ENV LIBOMP_USE_HIDDEN_HELPER_TASK=0
ENV LIBOMP_NUM_HIDDEN_HELPER_THREADS=0
ENV LD_LIBRARY_PATH="$FSLDIR/bin"
ENV USER="flywheel"

# Install Python dependencies
COPY Anaconda3-2025.06-0-Linux-x86_64.sh /tmp

RUN bash /tmp/Anaconda3-2025.06-0-Linux-x86_64.sh -b -p $HOME/anaconda3

RUN ~/anaconda3/bin/conda init

RUN ~/anaconda3/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main/linux-64 --channel https://repo.anaconda.com/pkgs/main/noarch --channel  https://repo.anaconda.com/pkgs/r/linux-64 --channel https://repo.anaconda.com/pkgs/r/noarch

RUN  . ~/.bashrc ; pip install nilearn nibabel jinja2 flywheel-sdk
WORKDIR "${FLYWHEEL}"
    
# Copy Flywheel gear files
RUN mkdir -p ${FLYWHEEL}
COPY ./src/ ${FLYWHEEL}/src/
COPY ./manifest.json ${FLYWHEEL}/
COPY ./config.json ${FLYWHEEL}/
COPY ./run_pipeline.sh ${FLYWHEEL}/

# Set permissions
RUN chmod +x ${FLYWHEEL}/run_pipeline.sh ${FLYWHEEL}/src/pipeline_scripts/* && \
    chmod -R 755 ${FLYWHEEL} && \
    ln -sf /bin/bash /bin/sh

ENV DATADIR='/flywheel/v0/work/fmriprep_unzipped/67cf0442cc5019460f9cc3aa'

ENTRYPOINT ["/bin/bash", "/flywheel/v0/run_pipeline.sh"]
