#!/usr/bin/env python
# coding: utf-8
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
from nilearn import image, plotting
from nilearn.maskers import NiftiMasker
from nilearn.input_data import NiftiMapsMasker
from nilearn.glm.first_level import FirstLevelModel
from nilearn.datasets import load_mni152_template
from nilearn.image import threshold_img
import argparse
from jinja2 import Template
from matplotlib.backends.backend_pdf import PdfPages
import base64
from io import BytesIO
from scipy.ndimage import label
import nibabel as nib

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Generate ICA reports for subjects")
parser.add_argument("--sub_dir", required=True, help="Directory containing input data")
parser.add_argument("--tasks", required=True, help="Space-separated list of tasks (e.g., 'motor_run-01 motor_run-02 lang')")
parser.add_argument("subjects", nargs="+", help="List of subject IDs")
args = parser.parse_args()

sub_dir = args.sub_dir
tasks = args.tasks.split()  # Convert space-separated string to list

# Set up task timing to convert to volumes
tr = 0.8  # Repetition time in seconds
block_duration = int(16 / tr)  # Number of time points per block (16s on/off)
num_blocks = 10  # Number of on-off cycles

# Create task regressor (1 for "on", 0 for "off")
task_regressor = np.tile([1] * block_duration + [0] * block_duration, num_blocks)


for subj in args.subjects:
    report_sections = []
    report_dir = os.path.join(sub_dir, f"post_stats")
    os.makedirs(report_dir, exist_ok=True)
    for task in tasks:
        print(f"\nProcessing Subject {subj}, Task {task}")
        
        base = os.path.join(sub_dir, f"fsl_stats/sub-{subj}_task-{task}_contrasts.feat")
        ica_path = os.path.join(base, "filtered_func_data.ica")
        
        func_file = os.path.join(base, "filtered_func_data.nii.gz")
        melodic_ic_file = os.path.join(ica_path, "melodic_IC.nii.gz")
        melodic_mix_file = os.path.join(ica_path, "melodic_mix")
        zstat_file = os.path.join(base, "stats/zstat1.nii.gz")
        
        # Check if required files exist
        for f in [func_file, melodic_ic_file, melodic_mix_file, zstat_file]:
            if not os.path.exists(f):
                print(f"Warning: File {f} not found for subject {subj}, task {task}. Skipping.")
                continue
        
        melodic_ic_img = image.load_img(melodic_ic_file)
        melodic_mix = np.loadtxt(melodic_mix_file)
        melodic_df = pd.DataFrame(melodic_mix)
        
        # Find best-matching component
        correlations = [pearsonr(melodic_df.iloc[:, i], task_regressor)[0] for i in range(melodic_df.shape[1])]
        best_component = np.argmax(np.abs(correlations))
        best_corr = correlations[best_component]
        
        # Spatial correlation with GLM zstat map
        glm_map = image.load_img(zstat_file)
        best_ic_map = image.index_img(melodic_ic_img, best_component)
        
        ic_data = image.get_data(best_ic_map).flatten()
        glm_data = image.get_data(glm_map).flatten()
        
        valid_mask = ~np.isnan(ic_data) & ~np.isnan(glm_data)
        spatial_corr = np.corrcoef(ic_data[valid_mask], glm_data[valid_mask])[0, 1]
        
        # Extract and threshold best component
        best_ic_map = image.index_img(melodic_ic_img, best_component)
        threshold = np.percentile(image.get_data(best_ic_map), 90)
        binary_mask_img = image.math_img(f"img > {threshold}", img=best_ic_map)
        
        # Time series from top voxels
        masker = NiftiMasker(mask_img=binary_mask_img, standardize=True)
        voxel_timeseries = masker.fit_transform(func_file)
        avg_timeseries = np.mean(voxel_timeseries, axis=1)
        
        # Dual regression
        ica_masker = NiftiMapsMasker(maps_img=melodic_ic_img, standardize=True)
        ica_timeseries = ica_masker.fit_transform(func_file)
        ica_df = pd.DataFrame(ica_timeseries, columns=[f"Comp_{i}" for i in range(ica_timeseries.shape[1])])
        
        glm = FirstLevelModel(t_r=tr)
        glm.fit(func_file, design_matrices=[ica_df])
        subject_maps = glm.compute_contrast(np.eye(ica_timeseries.shape[1]))
        subject_maps.to_filename(os.path.join(base, f"sub-{subj}_{task}_dual_regression_maps.nii.gz"))
        
        best_map = image.index_img(melodic_ic_img, best_component)

        # Apply voxel threshold Z > 3.1
        voxel_thresh_map = threshold_img(best_map, threshold=3.1)
        # Cluster cleanup (optional — post-process for contiguous blobs)

        # Convert to binary image and label clusters
        data = voxel_thresh_map.get_fdata()
        labels, n_clusters = label(data > 0)

        # Remove clusters smaller than min size
        min_cluster_size = 20  # typical FSL choice
        cleaned_data = np.zeros(data.shape)

        for i in range(1, n_clusters + 1):
            cluster = (labels == i)
            if cluster.sum() >= min_cluster_size:
                cleaned_data[cluster] = data[cluster]

        # Save final map
        thresholded_ica_map = nib.Nifti1Image(cleaned_data, affine=voxel_thresh_map.affine)
        thresholded_ica_path = os.path.join(base, f"sub-{subj}_{task}_ica_thresholded.nii.gz")
        nib.save(thresholded_ica_map, thresholded_ica_path)
        
        # --- Plot time series and encode to base64 ---
        buf_ts = BytesIO()
        plt.figure()
        plt.plot(avg_timeseries)
        plt.title(f"Mean Voxel Time Series - Component {best_component}")
        plt.xlabel("Time (TR)")
        plt.ylabel("Signal")
        plt.tight_layout()
        plt.savefig(buf_ts, format='png', dpi=100)
        plt.close()
        buf_ts.seek(0)
        ts_b64 = base64.b64encode(buf_ts.read()).decode('utf-8')

        # --- Plot dual regression map and encode to base64 ---
        buf_dr = BytesIO()
        display = plotting.plot_stat_map(
            thresholded_ica_map,
            bg_img=load_mni152_template(),
            title=f"Thresholded Component {best_component}",
            display_mode="ortho",
            colorbar=True
        )
        display.savefig(buf_dr, dpi=100)
        display.close()
        buf_dr.seek(0)
        dr_b64 = base64.b64encode(buf_dr.read()).decode('utf-8')

        ...
        section_html = f"""
        <h2>Task: {task}</h2>
        <p><strong>Best-matching ICA component:</strong> {best_component}</p>
        <p><strong>Temporal correlation with task regressor:</strong> {best_corr:.3f}</p>
        <p><strong>Spatial correlation with GLM zstat:</strong> {spatial_corr:.3f}</p>
        <h3>Time Series Plot</h3>
        <img src="data:image/png;base64,{ts_b64}" width="600"><br>
        <h3>Thresholded ICA Map</h3>
        <img src="data:image/png;base64,{dr_b64}" width="600"><br>
        """
        report_sections.append(section_html)
        
    html_file = os.path.join(report_dir, f"sub-{subj}_ica_report_alltasks.html")
    with open(html_file, "w") as f:
        f.write(f"<h1>ICA Report for Subject {subj}</h1>")
        f.writelines(report_sections)
    print(f"Report for subject {subj} saved to {html_file}")
