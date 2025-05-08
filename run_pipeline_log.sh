#!/bin/bash
# run_pipeline.sh: Runs the full RECOVER fMRI pipeline including FEAT stats,
# randomise permutation testing, post-stats calculation, and report generation.
# Processes a single subject derived from fmriprepdir input, for all tasks (motor_run-01, motor_run-02, lang).
# Updated to add checkpoints, improve logging, and fix output organization, May 2025
# Updated to enhance logging for all checkpoint messages, May 2025
# Updated to handle fmriprep unzip directory dynamically from zip file suffix and extract subject from sub-UPN007trial2, May 2025
# Updated to export SUBDIR for use in called scripts, May 2025
# Updated to dynamically find .fsf and .zip files and debug execution, May 2025

# Enable debugging
set -x
# Exit on any error, including in pipelines and subshells
set -e
set -o pipefail

# Default configuration
TASKS="motor_run-01 motor_run-02 lang"
CLUSTER_THRESHOLD=3.1

# Usage message
usage() {
    echo "[$(date)] Usage: $0" | tee -a "$LOG_FILE"
    echo "[$(date)] Runs all steps of the RECOVER fMRI pipeline for all tasks for a single subject derived from fmriprepdir." | tee -a "$LOG_FILE"
    exit 1
}

# Function to log messages
log_message() {
    echo "[$(date)] $1" | tee -a "$LOG_FILE"
}

# Function to log section headers
log_section() {
    echo "[$(date)] === $1 ===" | tee -a "$LOG_FILE"
}

# Function to check if a file exists
check_file() {
    local file=$1
    log_message "Checking file: $file"
    if [ ! -f "$file" ]; then
        log_message "Error: File not found: $file"
        exit 1
    fi
    log_message "File exists: $file"
}

# Function to check if a directory exists
check_dir() {
    local dir=$1
    log_message "Checking directory: $dir"
    if [ ! -d "$dir" ]; then
        log_message "Error: Directory not found: $dir"
        exit 1
    fi
    log_message "Directory exists: $dir"
    log_message "Directory contents: $(ls -l "$dir" || echo 'Empty or inaccessible')"
}

# Flywheel directories
base_dir=/flywheel/v0
INPUT_DIR=${base_dir}/input
OUTPUT_DIR=${base_dir}/output
WORK_DIR=${base_dir}/work
SRC_DIR=${base_dir}/src
mkdir -p "$OUTPUT_DIR" "$WORK_DIR"
LOG_FILE="$OUTPUT_DIR/pipeline.log"

# Echo early setup messages to both console and file
echo "[$(date)] Starting setup..." | tee -a "$LOG_FILE"
echo "[$(date)] Created directories: $OUTPUT_DIR, $WORK_DIR" | tee -a "$LOG_FILE"

# Redirect output to log file (after directory creation)
exec 1>>"$LOG_FILE" 2>&1
echo "[$(date)] Logging redirected. Pipeline starting..."  # This will be in the log
log_message "Starting RECOVER fMRI pipeline workflow"
log_message "Log file: $LOG_FILE"

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
log_message "Script paths: FEAT_STATS=$FEAT_STATS, RANDOMISE_STATS=$RANDOMISE_STATS, CAL_POST_STATS=$CAL_POST_STATS, ICA_CORRELATION=$ICA_CORRELATION, OUTPUT_GENERATOR=$OUTPUT_GENERATOR"

# Check pipeline scripts
for script in "$FEAT_STATS" "$RANDOMISE_STATS" "$CAL_POST_STATS" "$ICA_CORRELATION" "$OUTPUT_GENERATOR"; do
    check_file "$script"
    chmod +x "$script" 2>/dev/null || log_message "Warning: Could not make $script executable"
done

# Find input files dynamically
log_section "Input File Detection"
# Find .fsf file in design_template directory
DESIGN_FILE=$(find "$INPUT_DIR/design_template" -maxdepth 1 -type f -name "*.fsf" | head -n 1)
if [ -z "$DESIGN_FILE" ]; then
    log_message "Error: No .fsf file found in $INPUT_DIR/design_template"
    exit 1
fi
check_file "$DESIGN_FILE"
log_message "Design template file found: $DESIGN_FILE"

# Find .zip file in fmriprep_dir directory
FMRIPREP_ZIP=$(find "$INPUT_DIR/fmriprep_dir" -maxdepth 1 -type f -name "*.zip" | head -n 1)
if [ -z "$FMRIPREP_ZIP" ]; then
    log_message "Error: No .zip file found in $INPUT_DIR/fmriprep_dir"
    exit 1
fi
check_file "$FMRIPREP_ZIP"
log_message "fmriprep zip file found: $FMRIPREP_ZIP"

# Parse configuration from config.json
log_section "Configuration Parsing"
CONFIG_FILE=${base_dir}/config.json
if [ -f "$CONFIG_FILE" ]; then
    CLUSTER_THRESHOLD=$(jq -r '.config.cluster_threshold // 3.1' "$CONFIG_FILE")
    log_message "Cluster threshold set to $CLUSTER_THRESHOLD from $CONFIG_FILE"
else
    log_message "No config.json found, using default cluster threshold: $CLUSTER_THRESHOLD"
fi

# Checkpoint: Check required tools
log_section "Tool Check"
for cmd in feat fslmaths randomise antsApplyTransforms python3 jq unzip; do
    log_message "Checking tool: $cmd"
    if ! command -v "$cmd" &> /dev/null; then
        log_message "Error: $cmd not found. Please ensure FSL, ANTs, and Python are installed."
        exit 1
    fi
    log_message "Tool found: $cmd"
done
log_message "All required tools are available"

# Checkpoint: Extract fmriprep files
log_section "fmriprep Directory Setup"
log_message "Processing fmriprep zip file: $FMRIPREP_ZIP"
FMRIPREP_DIR_NAME=$(basename "$FMRIPREP_ZIP" .zip)
log_message "Extracted fmriprep directory name from zip: $FMRIPREP_DIR_NAME"
# Unzip to a consistent location
UNZIP_DIR="${INPUT_DIR}/fmriprep_unzipped"
mkdir -p "$UNZIP_DIR"
log_message "Unzipping $FMRIPREP_ZIP to $UNZIP_DIR"
unzip -o "$FMRIPREP_ZIP" -d "$UNZIP_DIR" || {
    log_message "Error: Failed to unzip $FMRIPREP_ZIP"
    exit 1
}
FMRIPREP_DIR=$(find "$UNZIP_DIR" -maxdepth 3 -type d -name "$FMRIPREP_DIR_NAME" || true)
if [ ! -d "$FMRIPREP_DIR" ]; then
    log_message "Error: fmriprep directory ($FMRIPREP_DIR_NAME) not found after extraction"
    exit 1
fi
log_message "fmriprep directory found: $FMRIPREP_DIR"
check_dir "$FMRIPREP_DIR"

# Main execution
log_section "Main Execution"
log_message "Starting RECOVER fMRI pipeline for tasks: $TASKS"

# Checkpoint: Extract subject ID
log_message "Extracting subject ID from $FMRIPREP_DIR"
SUBJECT=$(find "$FMRIPREP_DIR" -maxdepth 2 -type d -name "sub-*" | sed -E 's|.*/sub-([^/]+).*|\1|' | head -n 1)
if [ -z "$SUBJECT" ]; then
    log_message "Error: No subject ID (sub-*) found in $FMRIPREP_DIR"
    exit 1
fi
log_message "Subject ID: $SUBJECT"

# Checkpoint: Copy fmriprep inputs
log_section "fmriprep Input Copy"
log_message "Copying fmriprep inputs to $ARCHIVEDIR/derivatives/sub-$SUBJECT/ses-01"
SUBDIR="$ARCHIVEDIR/derivatives/sub-$SUBJECT/ses-01"
export SUBDIR
mkdir -p "$SUBDIR/func" "$SUBDIR/anat"
if [ -d "$FMRIPREP_DIR/sub-$SUBJECT/ses-01/func" ]; then
    log_message "Copying func files from $FMRIPREP_DIR/sub-$SUBJECT/ses-01/func"
    cp -r "$FMRIPREP_DIR/sub-$SUBJECT/ses-01/func/"* "$SUBDIR/func/" || {
        log_message "Error: Failed to copy func files from $FMRIPREP_DIR/sub-$SUBJECT/ses-01/func"
        exit 1
    }
    log_message "Func files copied successfully"
else
    log_message "Warning: No func directory found in $FMRIPREP_DIR/sub-$SUBJECT/ses-01"
fi
if [ -d "$FMRIPREP_DIR/sub-$SUBJECT/ses-01/anat" ]; then
    log_message "Copying anat files from $FMRIPREP_DIR/sub-$SUBJECT/ses-01/anat"
    cp -r "$FMRIPREP_DIR/sub-$SUBJECT/ses-01/anat/"* "$SUBDIR/anat/" || {
        log_message "Error: Failed to copy anat files from $FMRIPREP_DIR/sub-$SUBJECT/ses-01/anat"
        exit 1
    }
    log_message "Anat files copied successfully"
else
    log_message "Warning: No anat directory found in $FMRIPREP_DIR/sub-$SUBJECT/ses-01"
fi
check_dir "$SUBDIR/func"
check_dir "$SUBDIR/anat"

# Function to run feat_contrasts_recover_cluster.sh
run_feat_stats() {
    local subject=$1
    log_section "FEAT Stats"
    log_message "Running feat_contrasts_recover_cluster.sh for subject: $subject with tasks: $TASKS"
    export TASKS DESIGN_FILE
    bash "$FEAT_STATS" "$subject" || {
        log_message "Error: feat_contrasts_recover_cluster.sh failed for subject $subject"
        exit 1
    }
    # Checkpoint: Verify FEAT outputs
    for task in $TASKS; do
        local feat_dir="$SUBDIR/fsl_stats/sub-${subject}_task-${task}_contrasts.feat"
        check_dir "$feat_dir"
        check_file "$feat_dir/stats/zstat1.nii.gz"
    done
    log_message "feat_contrasts_recover_cluster.sh completed successfully for subject $subject"
}

# Function to run run_permutation_test.sh
run_permutation_test() {
    local subject=$1
    log_section "Permutation Test"
    log_message "Running run_permutation_test.sh for subject: $subject with tasks: $TASKS"
    export TASKS
    bash "$RANDOMISE_STATS" "$subject" || {
        log_message "Error: run_permutation_test.sh failed for subject $subject"
        exit 1
    }
    # Checkpoint: Verify randomise outputs
    for task in $TASKS; do
        local feat_dir="$SUBDIR/fsl_stats/sub-${subject}_task-${task}_contrasts.feat"
        check_file "$feat_dir/randomise_time_series_tfce_corrp_tstat1.nii.gz"
    done
    log_message "run_permutation_test.sh completed successfully for subject $subject"
}

# Function to run calc_post_stats_thresh.sh
run_cal_post_stats() {
    local subject=$1
    log_section "Post-Stats Calculation"
    log_message "Running calc_post_stats_thresh.sh for subject: $subject with tasks: $TASKS"
    # Checkpoint: Verify inputs for calc_post_stats
    for task in $TASKS; do
        local feat_dir="$SUBDIR/fsl_stats/sub-${subject}_task-${task}_contrasts.feat"
        check_file "$feat_dir/stats/remasked_zstat1.nii.gz"
        check_file "$feat_dir/randomise_time_series_tfce_corrp_tstat1.nii.gz"
    done
    export TASKS CLUSTER_THRESHOLD
    bash "$CAL_POST_STATS" "$subject" || {
        log_message "Error: calc_post_stats_thresh.sh failed for subject $subject"
        exit 1
    }
    # Checkpoint: Verify outputs
    for task in $TASKS; do
        local csv_file="$SUBDIR/post_stats/sub-${subject}_task-${task}_roi_stats.csv"
        check_file "$csv_file"
    done
    log_message "calc_post_stats_thresh.sh completed successfully for subject $subject"
}

# Function to run ICA
run_ica() {
    local subjects="$@"
    log_section "ICA Correlation"
    log_message "Running ICA for subjects: $subjects with tasks: $TASKS"
    python3 "$ICA_CORRELATION" --data_dir "$ARCHIVEDIR/derivatives" --tasks "$TASKS" "$subjects" || {
        log_message "Error: ica_corr.py failed for subjects $subjects"
        exit 1
    }
    log_message "ICA completed successfully for subjects $subjects"
}

# Function to run output_generator.py
run_output_generator() {
    local subject=$1
    log_section "Report Generation"
    log_message "Running output_generator.py for subject: $subject with tasks: $TASKS"
    export TASKS
    python3 "$OUTPUT_GENERATOR" "$subject" || {
        log_message "Error: output_generator.py failed for subject $subject"
        exit 1
    }
}

# Execute steps
run_feat_stats "$SUBJECT"
run_permutation_test "$SUBJECT"
run_cal_post_stats "$SUBJECT"
run_output_generator "$SUBJECT"

# Checkpoint: Organize outputs
log_section "Output Organization"
log_message "Organizing outputs to $OUTPUT_DIR"
cd "$SUBDIR"
zip -r "$OUTPUT_DIR/taskfMRI_outputs.zip" post_stats/

log_message "Zip archive created: $OUTPUT_DIR/taskfMRI_outputs.zip"
log_section "Pipeline Completion"
log_message "RECOVER fMRI task-based pipeline workflow completed on $(date)"
