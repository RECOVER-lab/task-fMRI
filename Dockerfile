# Stage 1: Install ANTs 2.5.4
FROM ubuntu:22.04 AS step1
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# Install build tools and dependencies for ANTs
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        file \
        libtbb2 \
        libgomp1 \
        libatomic1 \
        libtool \
        bzip2 \
        xvfb \
        cython3 \
        autoconf \
        pkg-config \
        jq \
        zip \
        unzip \
        nano \
        git \
        unzip && \
    mkdir /opt/ants && \
    curl -fsSL https://github.com/ANTsX/ANTs/releases/download/v2.5.4/ants-2.5.4-ubuntu-22.04-X64-gcc.zip -o ants.zip && \
    unzip ants.zip -d /opt && \
    rm ants.zip

ENV ANTSPATH="/opt/ants-2.5.4/bin"

# Stage 2: Main image with FSL and Flywheel
FROM ubuntu:22.04 AS final
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# Install original dependencies plus FSL prerequisites, including curl
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget \
        curl \
        libglib2.0-0 \
        libxext6 \
        libsm6 \
        libxrender1 \
        python3 \
        python3-pip \
        bc \
        dc \
        file \
        libfontconfig1 \
        libfreetype6 \
        libgl1-mesa-dev \
        libgl1-mesa-dri \
        libglu1-mesa-dev \
        libgomp1 \
        libice6 \
        libopenblas-base \
        libxcursor1 \
        libxft2 \
        libxinerama1 \
        libxrandr2 \
        libxrender1 \
        libxt6 \
        sudo \
        nano \
        dialog \
        libx11-6 \
        python3-venv && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install Miniconda for FSL
RUN curl -fsSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o miniconda.sh && \
    bash miniconda.sh -b -p /opt/miniconda && \
    rm miniconda.sh && \
    /opt/miniconda/bin/conda init bash

# Update PATH for Conda
ENV PATH="/opt/miniconda/bin:$PATH"

# Install FSL 6.0.7.1 with detailed logging
RUN echo "Installing FSL ..." && \
    curl -v -fsSL https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/releases/fslinstaller.py -o fslinstaller.py && \
    python3 fslinstaller.py -d /opt/fsl-6.0.7.1 -V 6.0.7.1 -v > fsl_install.log 2>&1 || { cat fsl_install.log; exit 1; } && \
    rm -rf /opt/fsl-6.0.7.1/doc /opt/fsl-6.0.7.1/data

# Copy ANTs from the first stage
COPY --from=step1 /opt/ants-2.5.4 /opt/ants-2.5.4

# Define ANTSPATH before using it
ENV ANTSPATH="/opt/ants-2.5.4/bin"

# Install required Python packages
RUN pip3 install \
    numpy \
    pandas \
    matplotlib \
    nilearn \
    scipy \
    nibabel \
    flywheel-sdk && \
    rm -rf /root/.cache/pip

# Set up Flywheel environment
ENV FLYWHEEL="/flywheel/v0"
RUN mkdir -p ${FLYWHEEL}

# Set environment variables for FSL and ANTs
ENV FSLDIR="/opt/fsl-6.0.7.1"
ENV PATH="$FSLDIR/bin:$ANTSPATH:$PATH" \
    FSLOUTPUTTYPE="NIFTI_GZ" \
    FSLMULTIFILEQUIT="TRUE" \
    FSLTCLSH="$FSLDIR/bin/fsltclsh" \
    FSLWISH="$FSLDIR/bin/fslwish" \
    FSLLOCKDIR="" \
    FSLMACHINELIST="" \
    FSLREMOTECALL="" \
    FSLGECUDAQ="cuda.q"

# Copy files and set permissions
COPY ./input/ ${FLYWHEEL}/input/
COPY ./src/ ${FLYWHEEL}/src/
COPY ./manifest.json ${FLYWHEEL}/
COPY ./run_pipeline.sh ${FLYWHEEL}/
RUN chmod +x ${FLYWHEEL}/run_pipeline.sh ${FLYWHEEL}/src/pipeline_scripts/* && \
    chmod -R 755 ${FLYWHEEL} && \
    ln -sf /bin/bash /bin/sh

# Configure entrypoint
ENTRYPOINT ["/bin/bash", "/flywheel/v0/run_pipeline.sh"]
