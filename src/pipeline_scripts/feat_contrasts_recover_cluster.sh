#!/bin/bash
# This script runs the FEAT stats (1st level GLM model) for functional scans
# Code adapted for RECOVER project based on the protocol from MGH by K. Nguyen at A. Wu Jan 2025

# Check if at least one subject ID was provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <subject_id1> <subject_id2> ... <subject_idN>"
    exit 1
fi

# Check if TASKS environment variable is set
if [ -z "$TASKS" ]; then
    echo "Error: TASKS environment variable not set. Please define tasks in master_workflow_cluster.sh."
    exit 1
fi

# Set the number of parallel jobs to run. change based on available cores in the cluster
export OMP_NUM_THREADS=4

process_subject_task() {
    subject=$1
    task=$2

    SUBDIR=${DATADIR}/sub-${subject}/ses-01
    mkdir -p ${SUBDIR}/fsl_stats

    T1=${SUBDIR}/anat/*MNI152NLin6Asym_desc-preproc_T1w.nii.gz
    input=${SUBDIR}/func/*${task}_space-MNI152NLin6Asym_desc-preproc_bold.nii.gz
    FUNC_MASK=${SUBDIR}/func/sub-${subject}_ses-01_task-${task}_space-MNI152NLin6Asym_desc-brain_mask.nii.gz

	if [ ! -f ${SUBDIR}/sub-${subject}_ses-01_task-${task}_confounds_motion.txt ]; then
        echo "Confounds motion.txt not found, using fsl_motion_outlier"
        fsl_motion_outliers -i $input -o ${SUBDIR}/sub-${subject}_ses-01_task-${task}_confounds_motion.txt --dummy=0
    fi

	echo "Motion outlier confounds.txt found, skip fsl_motion_outlier"
    confinput=${SUBDIR}/sub-${subject}_ses-01_task-${task}_confounds_motion.txt
    output=${SUBDIR}/fsl_stats/sub-${subject}_task-${task}_contrasts

	for i in $TEMPLATE; do
        sed -e 's@SUB_input_SUB@'$input'@g' \
            -e 's@SUB_confinput_SUB@'$confinput'@g' \
            -e 's@SUB_T1_SUB@'$T1'@g' \
            -e 's@SUB_FuncMask_SUB@'$FUNC_MASK'@g' \
            -e 's@SUB_output_SUB@'$output'@g' <$i> ${output}.fsf
        feat ${output}.fsf
        if [ $? -ne 0 ]; then
            echo "FEAT failed for sub-${subject}, skipping to next subject."
            return 1
        fi
    done
    echo "Complete ${task} first level for sub-${subject}"
}

# Export the function to be used in parallel
export -f process_subject_task

# Process all subjects for the tasks specified in TASKS
for subject in "$@"; do
    for task in $TASKS; do
        echo "Processing ${task} for sub-${subject} in parallel"
        process_subject_task "$subject" "$task" &
    done
done

wait  # Wait for all parallel jobs to finish
echo "All tasks completed for subjects: $@"