#!/bin/bash
# run_pipeline.sh: Runs the full RECOVER fMRI pipeline including FEAT stats,
# randomise permutation testing, post-stats calculation, and report generation.
# Processes a single subject derived from fmriprepdir input, for all tasks (motor_run-01, motor_run-02, lang).
# Updated to add checkpoints, improve logging, and fix output organization, May 2025
# Updated to handle fmriprep unzip directory dynamically from zip file suffix and extract subject May 2025

# Enable debugging
set -x
# # Exit on any error, including in pipelines and subshells
set -e
set -o pipefail

# Default configuration
TASKS="motor_run-01 motor_run-02 lang"
CLUSTER_THRESHOLD=3.1

# Usage message
usage() {
    echo "[$(date)] Usage: $0"
    echo "[$(date)] Runs all steps of the RECOVER fMRI pipeline for all tasks for a single subject derived from fmriprepdir."
    exit 1
}

# Set ANTs path
#export PATH="/Users/aliceqichaowu/ANTs/bin:$PATH"
#log_section "ANTs Setup"
#log_message "Checking antsApplyTransforms"
#if ! command -v antsApplyTransforms &> /dev/null; then
#    log_message "Error: antsApplyTransforms not found. Please verify ANTs installation at /Users/aliceqichaowu/ANTs/bin or adjust PATH."
#    exit 1
#fi


check_file() {
    local file=$1
    if [ ! -f "$file" ]; then
        echo "[$(date)] Error: File not found: $file" >&2
        exit 1
    fi
}

# Function to check if a directory exists
check_dir() {
    local dir=$1
    if [ ! -d "$dir" ]; then
        echo "[$(date)] Error: Directory not found: $dir" >&2
        exit 1
    fi
}

# Flywheel directories
base_dir=/flywheel/v0
#base_dir=/Volumes/Alice_Data/RECOVER_project/fw_gear_taskfMRI
INPUT_DIR=${base_dir}/input
OUTPUT_DIR=${base_dir}/output
WORK_DIR=${base_dir}/work
SRC_DIR=${base_dir}/src
mkdir -p "$OUTPUT_DIR" "$WORK_DIR"

# Base directories
ARCHIVEDIR="$WORK_DIR"
ROI="$INPUT_DIR/ROI"
export ARCHIVEDIR
export ROI
SCRIPTSDIR="$SRC_DIR/pipeline_scripts"
FEAT_STATS="$SCRIPTSDIR/feat_contrasts_recover_cluster.sh"
RANDOMISE_STATS="$SCRIPTSDIR/run_permutation_test.sh"
CAL_POST_STATS="$SCRIPTSDIR/calc_post_stats_thresh.sh"
ICA_CORRELATION="$SCRIPTSDIR/ica_corr.py"
OUTPUT_GENERATOR="$SCRIPTSDIR/output_generator.py"

# Check pipeline scripts
for script in "$FEAT_STATS" "$RANDOMISE_STATS" "$CAL_POST_STATS" "$ICA_CORRELATION" "$OUTPUT_GENERATOR"; do
    check_file "$script"
    chmod +x "$script" 2>/dev/null
done

# Find input files dynamically
# Find .fsf file in design_template directory
DESIGN_FILE=$(find "$INPUT_DIR/design_template" -maxdepth 1 -type f -name "*.fsf" | head -n 1)
if [ -z "$DESIGN_FILE" ]; then
    echo "[$(date)] Error: No .fsf file found in $INPUT_DIR/design_template" >&2
    exit 1
fi
check_file "$DESIGN_FILE"

# Find .zip file in fmriprep_dir directory
FMRIPREP_ZIP=$(find "$INPUT_DIR/fmriprep_dir" -maxdepth 1 -type f -name "*.zip" | head -n 1)
if [ -z "$FMRIPREP_ZIP" ]; then
    echo "[$(date)] Error: No .zip file found in $INPUT_DIR/fmriprep_dir" >&2
    exit 1
fi
check_file "$FMRIPREP_ZIP"

# Parse configuration from config.json
CONFIG_FILE=${base_dir}/config.json
if [ -f "$CONFIG_FILE" ]; then
    CLUSTER_THRESHOLD=$(jq -r '.config.cluster_threshold // 3.1' "$CONFIG_FILE")
fi

# Checkpoint: Check required tools
for cmd in feat fslmaths randomise antsApplyTransforms python3 jq unzip; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "[$(date)] Error: $cmd not found. Please ensure FSL, ANTs, and Python are installed." >&2
        exit 1
    fi
done

# Checkpoint: Extract fmriprep files
FMRIPREP_DIR_NAME=$(basename "$FMRIPREP_ZIP" .zip)
UNZIP_DIR="${WORK_DIR}/fmriprep_unzipped"
mkdir -p "$UNZIP_DIR"
unzip -o "$FMRIPREP_ZIP" -d "$UNZIP_DIR" || {
    echo "[$(date)] Error: Failed to unzip $FMRIPREP_ZIP" >&2
    exit 1
}
# Debug: List unzipped directory structure
echo "[$(date)] Debug: Unzipped directory structure:"
find "$UNZIP_DIR" -maxdepth 4 -type d

FMRIPREP_DIR=$(find "$UNZIP_DIR" -maxdepth 3 -type d -name "$FMRIPREP_DIR_NAME" || true)
if [ -z "$FMRIPREP_DIR" ]; then
    # Fallback: Search for any sub-* directory
    FMRIPREP_DIR=$(find "$UNZIP_DIR" -maxdepth 3 -type d -name "sub-*" | head -n 1)
fi
if [ ! -d "$FMRIPREP_DIR" ]; then
    echo "[$(date)] Error: fmriprep directory not found after extraction in $UNZIP_DIR" >&2
    exit 1
fi
check_dir "$FMRIPREP_DIR"

# Checkpoint: Extract subject ID and set SUBDIR
SUBJECT_DIR=$(find "$FMRIPREP_DIR" -maxdepth 3 -type d -name "sub-*" | head -n 1)
if [ -z "$SUBJECT_DIR" ]; then
    echo "[$(date)] Error: No subject directory (sub-*) found in $FMRIPREP_DIR" >&2
    exit 1
fi
SUBJECT=$(find "$FMRIPREP_DIR" -maxdepth 3 -type d -name "sub-*" | sed -E 's|.*/sub-([^/]+).*|\1|' | head -n 1)
if [ -z "$SUBJECT" ]; then
    echo "[$(date)] Error: No subject ID (sub-*) found in $FMRIPREP_DIR" >&2
    exit 1
fi
# Set SUBDIR to $SUBJECT_DIR/ses-01
SUBDIR="$SUBJECT_DIR/ses-01"
export SUBDIR
if [ ! -d "$SUBDIR" ]; then
    echo "[$(date)] Error: Session directory $SUBDIR does not exist" >&2
    exit 1
fi
echo "[$(date)] Debug: Extracted SUBJECT=$SUBJECT, SUBDIR=$SUBDIR"

check_dir "$SUBDIR/func"
check_dir "$SUBDIR/anat"

# Function to run feat_contrasts_recover_cluster.sh
run_feat_stats() {
    local subject=$1
    export TASKS DESIGN_FILE
    bash "$FEAT_STATS" "$subject" || {
        echo "[$(date)] Error: feat_contrasts_recover_cluster.sh failed for subject $subject" >&2
        exit 1
    }
    # Checkpoint: Verify FEAT outputs
    for task in $TASKS; do
        local feat_dir="$SUBDIR/fsl_stats/sub-${subject}_task-${task}_contrasts.feat"
        check_dir "$feat_dir"
        check_file "$feat_dir/stats/zstat1.nii.gz"
    done
}

# Function to run run_permutation_test.sh
run_permutation_test() {
    local subject=$1
    export TASKS
    bash "$RANDOMISE_STATS" "$subject" || {
        echo "[$(date)] Error: run_permutation_test.sh failed for subject $subject" >&2
        exit 1
    }
    # Checkpoint: Verify randomise outputs
    for task in $TASKS; do
        local feat_dir="$SUBDIR/fsl_stats/sub-${subject}_task-${task}_contrasts.feat"
        check_file "$feat_dir/randomise_time_series_tfce_corrp_tstat1.nii.gz"
    done
}

# Function to run calc_post_stats_thresh.sh
run_cal_post_stats() {
    local subject=$1
    # Checkpoint: Verify inputs for calc_post_stats
    for task in $TASKS; do
        local feat_dir="$SUBDIR/fsl_stats/sub-${subject}_task-${task}_contrasts.feat"
        check_file "$feat_dir/stats/remasked_zstat1.nii.gz"
        check_file "$feat_dir/randomise_time_series_tfce_corrp_tstat1.nii.gz"
    done
    export TASKS CLUSTER_THRESHOLD
    bash "$CAL_POST_STATS" "$subject" || {
        echo "[$(date)] Error: calc_post_stats_thresh.sh failed for subject $subject" >&2
        exit 1
    }
    # Checkpoint: Verify outputs
    for task in $TASKS; do
        local csv_file="$SUBDIR/post_stats/sub-${subject}_task-${task}_roi_stats.csv"
        check_file "$csv_file"
    done
}

# Function to run ICA
run_ica() {
    local subjects="$@"
    python "$ICA_CORRELATION" --sub_dir "$SUBDIR" --tasks "$TASKS" "$subjects" || {
        echo "[$(date)] Error: ica_corr.py failed for subjects $subjects" >&2
        exit 1
    }
}

# Function to run output_generator.py
run_output_generator() {
    local subject=$1
    export TASKS
    python "$OUTPUT_GENERATOR" "$subject" || {
        echo "[$(date)] Error: output_generator.py failed for subject $subject" >&2
        exit 1
    }
}

# Execute steps
run_feat_stats "$SUBJECT"
run_permutation_test "$SUBJECT"
run_ica "$SUBJECT"
run_cal_post_stats "$SUBJECT"
run_output_generator "$SUBJECT"

# Checkpoint: Organize outputs
cd "$SUBDIR"
zip -r "$OUTPUT_DIR/taskfMRI_outputs.zip" post_stats/
