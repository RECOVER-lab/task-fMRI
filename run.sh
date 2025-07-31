#!/usr/bin/env bash 

IMAGE=alicewu/taskfmri:0.1.0

# Command:
docker run -v \
	/data/holder/Recover-taskfMri/Recover-taskfMriGear/input:/flywheel/v0/input -v \
	/data/holder/Recover-taskfMri/Recover-taskfMriGear/output:/flywheel/v0/output -v \
	/data/holder/Recover-taskfMri/Recover-taskfMriGear/work:/flywheel/v0/work -v \
	/data/holder/Recover-taskfMri/Recover-taskfMriGear/config.json:/flywheel/v0/config.json \
	-v \
	/data/holder/Recover-taskfMri/Recover-taskfMriGear/manifest.json:/flywheel/v0/manifest.json \
	--entrypoint=/bin/sh -e REQUESTS_CA_BUNDLE='/etc/ssl/certs/ca-certificates.crt' -e \
	FLYWHEEL='/flywheel/v0' -e FSLDIR='/opt/fsl-6.0.7.1' -e ANTSPATH='/opt/ants-2.5.4/bin' \
	-e FSLMULTIFILEQUIT='TRUE' -e FSLTCLSH='/opt/fsl-6.0.7.1/bin/fsltclsh' -e \
	PATH='/opt/fsl-6.0.7.1/bin:/opt/ants-2.5.4/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin' \
	-e FSLGECUDAQ='cuda.q' -e FSLOUTPUTTYPE='NIFTI_GZ' -e DEBIAN_FRONTEND='noninteractive' \
	-e FSLWISH='/opt/fsl-6.0.7.1/bin/fslwish' -e PWD='/flywheel/v0' -e TZ='Etc/UTC' -e \
	SHLVL='0' -e _='/usr/bin/printenv' -e PYTHONNOUSERSITE='1' -e \
	LIBOMP_NUM_HIDDEN_HELPER_THREADS='0' -e LIBOMP_USE_HIDDEN_HELPER_TASK='0' -e \
	USER='flywheel' -e LD_LIBRARY_PATH='/opt/fsl-6.0.7.1/bin' -e OMP_NUM_THREADS='1' -e \
	MKL_NUM_THREADS='1' $IMAGE -c /flywheel/v0/run_pipeline.sh \
