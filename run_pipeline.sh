#!/bin/bash
# run_pipeline.sh: Runs the full RECOVER fMRI pipeline including FEAT stats,
# randomise permutation testing, post-stats calculation, and report generation.
# Processes a single subject derived from fmriprepdir input, for all tasks (motor_run-01, motor_run-02, lang).
# Updated to add checkpoints, improve logging, and fix output organization, May 2025
# Updated to handle fmriprep unzip directory dynamically from zip file suffix and extract subject May 2025

CmdName=$(basename "$0")
Syntax="${CmdName} 
[-b BaseDir]
[-c ConfigJsonFile]
[-C ClusterThreshold] 
[-d DesignFilePath]
[-f ForceSubtasks]
[-i InputDir]
[-n]
[-o OutputDir]
[-r RoiDir]
[-s ScriptsDir]
[-t TaskList]
[-w WorkDir]
[-v]
[-z FMriZipFile]
"
# Enable debugging
set -x
# # Exit on any error, including in pipelines and subshells
set -e
set -o pipefail

while getopts b:C:c:d:f:i:no:r:s:t:w:vz: arg
do
	case "$arg" in
		b|C|c|d|f|i|n|o|r|s|t|w|v|z)
			eval "opt_${arg}='${OPTARG:=1}'"
			;;
	esac
done
shift $(("$OPTIND" - 1))

# Default configuration

# Flywheel directories
base_dir=/flywheel/v0 && [ -n "$opt_b" ] && base_dir="$opt_b"
INPUT_DIR=${base_dir}/input && [ -n "$opt_i" ] && INPUT_DIR="$opt_i"
OUTPUT_DIR=${base_dir}/output && [ -n "$opt_o" ] && OUTPUT_DIR="$opt_o"
WORK_DIR=${base_dir}/work && [ -n "$opt_w" ] && WORK_DIR="$opt_w"


# Parse configuration from config.json
CONFIG_FILE=${base_dir}/config.json && [ -n "$opt_c" ] && CONFIG_FILE="$opt_c"
if [ -f "$CONFIG_FILE" ]; then
    CLUSTER_THRESHOLD=$(jq -r '.config.cluster_threshold // 3.1' "$CONFIG_FILE")
fi
[ -z "$CLUSTER_THRESHOLD" ] && CLUSTER_THRESHOLD=2.35 
[ -n "$opt_C" ] && CLUSTER_THRESHOLD="$opt_C"

SCRIPTSDIR="${base_dir}/src/pipeline_scripts" && [ -n "$opt_s" ] && SCRIPTSDIR="$opt_s"
TASKS="motor_run-01 motor_run-02 lang" && [ -n "$opt_t" ] && TASKS="$opt_t"

[ -e "$OUTPUT_DIR" ] || mkdir -p "$OUTPUT_DIR"
[ -e "$WORK_DIR" ] || mkdir -p "$WORK_DIR"

# Base directories
ARCHIVEDIR="$WORK_DIR"
ROI="$INPUT_DIR/ROI" && [ -n "$opt_r" ] && ROI="$opt_r"
export ARCHIVEDIR
export ROI

if [ -n "$opt_f" ]
then
	DESIGN_FILE="$opt_f"
else
	DESIGN_FILE=$(find "$INPUT_DIR/design_template" -maxdepth 1 -type f -name "*.fsf" | head -n 1)
fi

if [ -z "$DESIGN_FILE" ]; then
    echo "[$(date)] Error: No .fsf file found in $INPUT_DIR/design_template" >&2
    exit 1
fi
check_file "$DESIGN_FILE"

if [ -n "$opt_f" ]
then
	for i in $(echo "$opt_f" | sed 's/, */ /g')
	do
		eval "${i}='true'"
	done
fi

# Usage message
usage() {
    echo "[$(date)] ${Syntax}" 1>&2
    echo "[$(date)] Runs all steps of the RECOVER fMRI pipeline for all tasks for a single subject derived from fmriprepdir." 1>&2
    exit 1
}

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

#
# Do not need to check as 
# set -e
# will kill this pipeline if a script is missing
# #
#
# Check pipeline scripts
# for script in "$FEAT_STATS" "$RANDOMISE_STATS" "$CAL_POST_STATS" "$ICA_CORRELATION" "$OUTPUT_GENERATOR"; do
#     check_file "$script"
#     chmod +x "$script" 2>/dev/null
# done

# Find input files dynamically
# Find .fsf file in design_template directory
# Find .zip file in fmriprep_dir directory
FMRIPREP_ZIP=$(find "$INPUT_DIR/fmriprep_dir" -maxdepth 1 -type f -name "*.zip" | head -n 1)
if [ -z "$FMRIPREP_ZIP" ]; then
    echo "[$(date)] Error: No .zip file found in $INPUT_DIR/fmriprep_dir" >&2
    exit 1
fi
check_file "$FMRIPREP_ZIP"

# Checkpoint: Extract fmriprep files
UNZIP_DIR="${WORK_DIR}/fmriprep_unzipped"
[ -d "$UNZIP_DIR" ] || {
	mkdir -p "$UNZIP_DIR"
	unzip -o "$FMRIPREP_ZIP" -d "$UNZIP_DIR" || {
    		echo "[$(date)] Error: Failed to unzip $FMRIPREP_ZIP" >&2
    		exit 1
	}
}
# Debug: List unzipped directory structure
echo "[$(date)] Debug: Unzipped directory structure:"
find "$UNZIP_DIR" -maxdepth 4 -type d

FMRIPREP_DIR_NAME=$(basename "$FMRIPREP_ZIP" .zip)
FMRIPREP_DIR=$(find "$UNZIP_DIR" -maxdepth 3 -type d -name "$FMRIPREP_DIR_NAME" || true)
if [ -z "$FMRIPREP_DIR" ]; then
    # Fallback: Search for any sub-* directory
    FMRIPREP_DIR=$(find "$UNZIP_DIR" -maxdepth 3 -type d -name "sub-*" | head -n 1)
fi
#if [ ! -d "$FMRIPREP_DIR" ]; then
#    echo "[$(date)] Error: fmriprep directory not found after extraction in $UNZIP_DIR" >&2
#    exit 1
#fi
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
    local Tasks="$2"
    local DesignFile="$3"
    local RunFeatStats=

    local FEAT_STATS="$SCRIPTSDIR/feat_contrasts_recover_cluster.sh"
    
    # Only run feat_stats if we're missing task feature
    for task in $TASKS; do
        local feat_dir="$SUBDIR/fsl_stats/sub-${subject}_task-${task}_contrasts.feat"
	[ -e "$feat_dir/stats/zstat1.nii.gz" ] || RunFeatStats='true'
    done

    if [ -n "$ForceFeatStats" ] || [ -n "$RunFeatStats" ] 
    then
    	export TASKS DESIGN_FILE
    	bash "$FEAT_STATS" "$subject" || {
       		echo "[$(date)] Error: feat_contrasts_recover_cluster.sh failed for subject $subject" >&2
        	exit 1
    	}
    fi

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
    local Tasks="$2"

    local RANDOMISE_STATS="$SCRIPTSDIR/run_permutation_test.sh"
    local RunPermutationTest=

    export TASKS

    for task in $TASKS; do
        local feat_dir="$SUBDIR/fsl_stats/sub-${subject}_task-${task}_contrasts.feat"
        [ -e "$feat_dir/randomise_time_series_tfce_corrp_tstat1.nii.gz" ] || RunPermutationTest=true
    done

    if [ -n "$ForcePermutationTest" ] || [ -n "$RunPermutationTest" ]
    then
	    bash "$RANDOMISE_STATS" "$subject" || {
	        echo "[$(date)] Error: run_permutation_test.sh failed for subject $subject" >&2
	        exit 1
	    }
    fi

    # Checkpoint: Verify randomise outputs
    for task in $TASKS; do
        local feat_dir="$SUBDIR/fsl_stats/sub-${subject}_task-${task}_contrasts.feat"
        check_file "$feat_dir/randomise_time_series_tfce_corrp_tstat1.nii.gz"
    done
}

# Function to run ICA
run_ica() {
    local subjects="$@"
    # *** Should be a way to check if this has been run
    local ICA_CORRELATION="$SCRIPTSDIR/ica_corr.py"
    local html_file="$SUBDIR/post_stats/sub-${subjects}_ica_report_alltasks.html" 

    [ -e "$html_file" ] || python "$ICA_CORRELATION" --sub_dir "$SUBDIR" --tasks "$TASKS" "$subjects" || {
        echo "[$(date)] Error: ica_corr.py failed for subjects $subjects" >&2
        exit 1
    }
}

# Function to run calc_post_stats_thresh.sh
run_cal_post_stats() {
    local subject=$1
    local Tasks="$2"
    local ClusterThreshhold="$3"

    local CAL_POST_STATS="$SCRIPTSDIR/calc_post_stats_thresh.sh"
    local RunCalPostStats=

    for task in $TASKS; do
        local csv_file="$SUBDIR/post_stats/sub-${subject}_task-${task}_roi_stats.csv"
        local feat_dir="$SUBDIR/fsl_stats/sub-${subject}_task-${task}_contrasts.feat"

        [ -e "$csv_file" ] || RunCalPostStats='true'
        [ -e "$feat_dir" ] || RunCalPostStats='true'
    done

    export TASKS CLUSTER_THRESHOLD
    if [ -n "$ForceCalPostStats" ] || [ -n "$RunCalPostStats" ]
    then
	    bash "$CAL_POST_STATS" "$subject" || {
	        echo "[$(date)] Error: calc_post_stats_thresh.sh failed for subject $subject" >&2
	        exit 1
	    }
    fi

    # Checkpoint: Verify outputs
    for task in $TASKS; do
        local csv_file="$SUBDIR/post_stats/sub-${subject}_task-${task}_roi_stats.csv"
        check_file "$csv_file"
    done
}

# Function to run output_generator.py
run_output_generator() {
    local subject=$1
    #
    #    Don't see that TASKS is used in output_generator.py
    #	Does want ROI and SUBDIR env variables
    #
    unset TASKS
    OUTPUT_GENERATOR="$SCRIPTSDIR/output_generator.py"
    [ -e "/flywheel/v0/work/fmriprep_unzipped/67cf0442cc5019460f9cc3aa/sub-UPN007trial2/ses-01/post_stats/sub-UPN007trial2_task_pipeline_report.html" ] || RunOutputGenerator='true'

    if [ -n "$ForceRunOutputGenerator" ] || [ -n "$RunOutputGenerator" ]
    then
	    python "$OUTPUT_GENERATOR" "$subject" || {
                echo "[$(date)] Error: output_generator.py failed for subject $subject" >&2
                exit 1
            }
    fi
}

# Execute steps
run_feat_stats "$SUBJECT" "$TASKS" "$DESIGN_FILE"
run_permutation_test "$SUBJECT"
run_ica "$SUBJECT"
run_cal_post_stats "$SUBJECT"
run_output_generator "$SUBJECT"

# Checkpoint: Organize outputs
cd "$SUBDIR"

[ -e "$OUTPUT_DIR/taskfMRI_outputs.zip" ] || zip -r "$OUTPUT_DIR/taskfMRI_outputs.zip" post_stats/
