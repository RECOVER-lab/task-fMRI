# task-fMRI
Flywheel gear to process task-based fMRI BOLD sequences (motor and language tasks).
The pipeline is desgined specifically for detecting consciousness of comatose patients

## Task-based fMRI Pipeline (RECOVER Project)
Created by K. Nguyen and A. Wu, Mar 2025.

This pipeline implements two testing methods:
- **GLM Testing:** Adapted from the MGH protocol. Use GLM model to conduct the analysis. Cluster thresholding at Z=3.1
- **Permutation Testing:** Non-parametric method. Randomly shuffling or rearranging data to estimate the sampling distribution of a test statistic under the null hypothesis. Includes a threshold-free clustering enhancement (TFCE) method.

---

## Inputs

The pipeline uses outputs from fMRIPrep gear on flywheel(version: 23.0.1).  
**fMRIPrep command used:**
`/opt/conda/bin/fmriprep /flywheel/v0/work/bids /flywheel/v0/output/67b747ac81e8158d3b6ad2c6 participant --aroma-melodic-dimensionality=-200 --bold2t1w-dof=6 --bold2t1w-init=register --dvars-spike-threshold=1.5 --fd-spike-threshold=0.5 --n_cpus=2 --omp-nthreads=2 --output-spaces=MNI152NLin6Asym --skull-strip-t1w=force --skull-strip-template=OASIS30ANTs --use-aroma --mem=12203`

**Required inputs:**
- **fmriPrep Output Zip File** func and anat folder. Images are in MNI space
- **Design template:** For FSL FEAT analysis (`design_test_script.fsf`).
- **ROIs:** Default: Motor (`SMA_PMC.nii.gz`) and Language tasks (`STG.nii.gz`, `Heschl.nii.gz`).
---

## Src folder - Pipeline scripts

1. **`feat_contrasts_recover_cluster.sh`:**  
   - Runs FSL FEAT analysis (GLM test) with the specified design matrix and configurations.

2. **`run_permutation_test_cluster.sh`:**  
   - Runs randomize permutation testing with time series data.
  
3. **`cal_post_stats_thresh.sh`:**  
   - Calculates quantitative measurements based on the output of the previous step.

4. **`ica_corr.py`:**
   - Runs ICA analysis on time-series data. Temporal correlation with task regressor and spatial orrelation with GLM zstat

6. **`output_generator.py`:**  
   - Calls `data_processor.py` and uses `html_template.py`.
   - Processes and combines results and plots.  
   - Generates an HTML report with visualizations for easier diagnosis and reporting.

---

## Outputs

Zip file including below: 
- **Excel sheets** Save all the calculation results from cal_post_stats_thresh.sh
- **Tables:** Show the number and percentage of suprathresholded voxels in ROIs and the whole brain.
- **Thresholded Z-maps:** In native space, obtained from FSL FEAT analysis.
- **HTML Viewer (+ PDF):** Includes:
  - Tables and plots mentioned above.
  - Interactive brain viewer for physicians to diagnose and report results.
  - ICA results.
