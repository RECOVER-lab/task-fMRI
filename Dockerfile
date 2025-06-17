# Base stage with common dependencies, try 24.04
FROM ubuntu:22.04 AS base
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

RUN apt-get update && apt-get install -y --no-install-recommends \
    autoconf \
    bc \
    bzip2 \
    build-essential \
    ca-certificates \
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
    libopenblas-base \
    libsm6 \
    libtbb2 \
    libtool \
    libxcursor1 \
    libxext6 \
    libxft2 \
    libxinerama1 \
    libxrandr2 \
    libxrender1 \
    libxt6 \
    python3 \
    python3-pip \
    python3-venv \
    sudo \
    unzip \
    wget \
    xvfb \
    zip

# FSL stage
FROM base AS fsl
RUN curl -fsSL https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/releases/fslinstaller.py | \
    python3 - -d /opt/fsl-6.0.7.1 -V 6.0.7.1

# ANTs stage
FROM base AS ants
RUN mkdir /opt/ants && \
    curl -fsSL https://github.com/ANTsX/ANTs/releases/download/v2.5.4/ants-2.5.4-ubuntu-22.04-X64-gcc.zip -o ants.zip && \
    unzip ants.zip -d /opt && \
    chmod +x /opt/ants-2.5.4/bin/*

# Final stage
FROM base AS final
ENV ANTSPATH="/opt/ants-2.5.4/bin"
ENV FLYWHEEL="/flywheel/v0"
ENV FSLDIR="/opt/fsl-6.0.7.1"
ENV PATH="$FSLDIR/bin:$ANTSPATH:$PATH"
ENV FSLOUTPUTTYPE="NIFTI_GZ"
ENV FSLMULTIFILEQUIT="TRUE"
ENV FSLTCLSH="$FSLDIR/bin/fsltclsh"
ENV FSLWISH="$FSLDIR/bin/fslwish"
ENV FSLLOCKDIR=""
ENV FSLMACHINELIST=""
ENV FSLREMOTECALL=""
ENV FSLGECUDAQ="cuda.q"
ENV MKL_NUM_THREADS=1
ENV OMP_NUM_THREADS=1
ENV PYTHONNOUSERSITE=1
ENV LIBOMP_USE_HIDDEN_HELPER_TASK=0
ENV LIBOMP_NUM_HIDDEN_HELPER_THREADS=0
ENV LD_LIBRARY_PATH="$FSLDIR/bin"
ENV USER="flywheel"

# Install Python dependencies
RUN pip3 install --no-cache-dir \
    numpy \
    pandas \
    matplotlib \
    nilearn \
    scipy \
    nibabel \
    jinja2 \
    flywheel-sdk
    
# Copy Flywheel gear files
RUN mkdir -p ${FLYWHEEL}
COPY ./input/ ${FLYWHEEL}/input/
COPY ./src/ ${FLYWHEEL}/src/
COPY ./manifest.json ${FLYWHEEL}/
COPY ./run_pipeline.sh ${FLYWHEEL}/

# Set permissions
RUN chmod +x ${FLYWHEEL}/run_pipeline.sh ${FLYWHEEL}/src/pipeline_scripts/* && \
    chmod -R 755 ${FLYWHEEL} && \
    ln -sf /bin/bash /bin/sh

ENTRYPOINT ["/bin/bash", "/flywheel/v0/run_pipeline.sh"]
