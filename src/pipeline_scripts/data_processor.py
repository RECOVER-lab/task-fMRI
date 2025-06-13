#!/opt/anaconda3/bin/python
# Python 3.8.20
# data_processor.py: Functions to get values and save in plots and tables
# Updated to use subject-specific ROI folder, Mar 2025
# Updated to separate STG and Heschl ROIs for language task and add ROI voxel percentage, Mar 2025

import os
from nilearn import plotting
import logging
import matplotlib.pyplot as plt                 
import pandas as pd
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataProcessor:
    def __init__(self, subject, subject_path, roi_path):
        self.subject = subject
        self.roi_path = roi_path  # This is the global ROI path for initial templates
        self.subject_path = subject_path
        self.subj_roi_path = os.path.join(self.subject_path, "ROI")  # Subject-specific ROI folder
        self.t1_native = os.path.join(self.subject_path, f"anat/sub-{subject}_ses-01_run-01_desc-brain_T1w.nii.gz")  # Native skull-stripped T1w
        self.t1_mni = os.path.join(self.subject_path, f"anat/sub-{subject}_ses-01_run-01_space-MNI152NLin6Asym_desc-preproc_T1w.nii.gz")  # Standard MNI space
        
        # Define cut_coords for Native space
        self.native_motor_coords = np.linspace(15, 50, 10)
        self.native_stg_coords = np.linspace(-25, 15, 10)
        
        # Define cut_coords for MNI space
        self.mni_motor_coords = np.linspace(20, 75, 10)
        self.mni_stg_coords = np.linspace(-15, 40, 10)
        
        logging.info(f"Initializing DataProcessor for subject {subject}")
        self.task_roi_mapping = self._create_task_roi_mapping()

    def _create_task_roi_mapping(self):
        return {
            'Motor 1': {
                'Native': {
                    'z_map': os.path.join(self.subject_path, f"fsl_stats/sub-{self.subject}_task-motor_run-01_contrasts.feat/stats/zstat1_native.nii.gz"),
                    'thresh_z_map_235': os.path.join(self.subject_path, f"fsl_stats/sub-{self.subject}_task-motor_run-01_contrasts.feat/stats/thresh_zstat1_235_native.nii.gz"),
                    'thresh_z_map_31': os.path.join(self.subject_path, f"fsl_stats/sub-{self.subject}_task-motor_run-01_contrasts.feat/stats/thresh_zstat1_native.nii.gz"),
                    'roi_paths': {
                        'Whole-brain SMA + PMC': os.path.join(self.subj_roi_path, "SMA_PMC_sub_t1w_native.nii.gz"),
                        'Left SMA + PMC': os.path.join(self.subj_roi_path, "SMA_PMC_sub_t1w_native_left.nii.gz"),
                        'Right SMA + PMC': os.path.join(self.subj_roi_path, "SMA_PMC_sub_t1w_native_right.nii.gz")
                    },
                    'csv_file': os.path.join(self.subject_path, f"post_stats/sub-{self.subject}_task-motor_run-01_roi_stats.csv"),
                    'cut_coords': self.native_motor_coords
                },
                'MNI': {
                    'z_map': os.path.join(self.subject_path, f"fsl_stats/sub-{self.subject}_task-motor_run-01_contrasts.feat/stats/remasked_zstat1.nii.gz"),
                    'thresh_z_map_235': os.path.join(self.subject_path, f"fsl_stats/sub-{self.subject}_task-motor_run-01_contrasts.feat/stats/thresh_zstat1_235.nii.gz"),
                    'thresh_z_map_31': os.path.join(self.subject_path, f"fsl_stats/sub-{self.subject}_task-motor_run-01_contrasts.feat/thresh_zstat1.nii.gz"),
                    'roi_paths': {
                        'Whole-brain SMA + PMC': os.path.join(self.subj_roi_path, "SMA_PMC_sub.nii.gz"),
                        'Left SMA + PMC': os.path.join(self.subj_roi_path, "SMA_PMC_sub_left.nii.gz"),
                        'Right SMA + PMC': os.path.join(self.subj_roi_path, "SMA_PMC_sub_right.nii.gz")
                    },
                    'csv_file': os.path.join(self.subject_path, f"post_stats/sub-{self.subject}_task-motor_run-01_roi_stats.csv"),
                    'cut_coords': self.mni_motor_coords
                }
            },
            'Motor 2': {
                'Native': {
                    'z_map': os.path.join(self.subject_path, f"fsl_stats/sub-{self.subject}_task-motor_run-02_contrasts.feat/stats/zstat1_native.nii.gz"),
                    'thresh_z_map_235': os.path.join(self.subject_path, f"fsl_stats/sub-{self.subject}_task-motor_run-02_contrasts.feat/stats/thresh_zstat1_235_native.nii.gz"),
                    'thresh_z_map_31': os.path.join(self.subject_path, f"fsl_stats/sub-{self.subject}_task-motor_run-02_contrasts.feat/stats/thresh_zstat1_native.nii.gz"),
                    'roi_paths': {
                        'Whole-brain SMA + PMC': os.path.join(self.subj_roi_path, "SMA_PMC_sub_t1w_native.nii.gz"),
                        'Left SMA + PMC': os.path.join(self.subj_roi_path, "SMA_PMC_sub_t1w_native_left.nii.gz"),
                        'Right SMA + PMC': os.path.join(self.subj_roi_path, "SMA_PMC_sub_t1w_native_right.nii.gz")
                    },
                    'csv_file': os.path.join(self.subject_path, f"post_stats/sub-{self.subject}_task-motor_run-02_roi_stats.csv"),
                    'cut_coords': self.native_motor_coords
                },
                'MNI': {
                    'z_map': os.path.join(self.subject_path, f"fsl_stats/sub-{self.subject}_task-motor_run-02_contrasts.feat/stats/remasked_zstat1.nii.gz"),
                    'thresh_z_map_235': os.path.join(self.subject_path, f"fsl_stats/sub-{self.subject}_task-motor_run-02_contrasts.feat/stats/thresh_zstat1_235.nii.gz"),
                    'thresh_z_map_31': os.path.join(self.subject_path, f"fsl_stats/sub-{self.subject}_task-motor_run-02_contrasts.feat/thresh_zstat1.nii.gz"),
                    'roi_paths': {
                        'Whole-brain SMA + PMC': os.path.join(self.subj_roi_path, "SMA_PMC_sub.nii.gz"),
                        'Left SMA + PMC': os.path.join(self.subj_roi_path, "SMA_PMC_sub_left.nii.gz"),
                        'Right SMA + PMC': os.path.join(self.subj_roi_path, "SMA_PMC_sub_right.nii.gz")
                    },
                    'csv_file': os.path.join(self.subject_path, f"post_stats/sub-{self.subject}_task-motor_run-02_roi_stats.csv"),
                    'cut_coords': self.mni_motor_coords
                }
            },
            'Language': {
                'Native': {
                    'z_map': os.path.join(self.subject_path, f"fsl_stats/sub-{self.subject}_task-lang_contrasts.feat/stats/zstat1_native.nii.gz"),
                    'thresh_z_map_235': os.path.join(self.subject_path, f"fsl_stats/sub-{self.subject}_task-lang_contrasts.feat/stats/thresh_zstat1_235_native.nii.gz"),
                    'thresh_z_map_31': os.path.join(self.subject_path, f"fsl_stats/sub-{self.subject}_task-lang_contrasts.feat/stats/thresh_zstat1_native.nii.gz"),
                    'roi_paths': {
                        "Whole-brain STG": os.path.join(self.subj_roi_path, "STG_sub_t1w_native.nii.gz"),
                        'Left STG': os.path.join(self.subj_roi_path, "STG_sub_t1w_native_left.nii.gz"),
                        'Right STG': os.path.join(self.subj_roi_path, "STG_sub_t1w_native_right.nii.gz"),
                        "Whole-brain Heschl": os.path.join(self.subj_roi_path, "Heschl_sub_t1w_native.nii.gz"),
                        'Left Heschl': os.path.join(self.subj_roi_path, "Heschl_sub_t1w_native_left.nii.gz"),
                        'Right Heschl': os.path.join(self.subj_roi_path, "Heschl_sub_t1w_native_right.nii.gz")
                    },
                    'csv_file': os.path.join(self.subject_path, f"post_stats/sub-{self.subject}_task-lang_roi_stats.csv"),
                    'cut_coords': self.native_stg_coords
                },
                'MNI': {
                    'z_map': os.path.join(self.subject_path, f"fsl_stats/sub-{self.subject}_task-lang_contrasts.feat/stats/remasked_zstat1.nii.gz"),
                    'thresh_z_map_235': os.path.join(self.subject_path, f"fsl_stats/sub-{self.subject}_task-lang_contrasts.feat/stats/thresh_zstat1_235.nii.gz"),
                    'thresh_z_map_31': os.path.join(self.subject_path, f"fsl_stats/sub-{self.subject}_task-lang_contrasts.feat/thresh_zstat1.nii.gz"),
                    'roi_paths': {
                        "Whole-brain STG": os.path.join(self.subj_roi_path, "STG_sub.nii.gz"),
                        'Left STG': os.path.join(self.subj_roi_path, "STG_sub_left.nii.gz"),
                        'Right STG': os.path.join(self.subj_roi_path, "STG_sub_right.nii.gz"),
                        "Whole-brain Heschl": os.path.join(self.subj_roi_path, "Heschl_sub.nii.gz"),
                        'Left Heschl': os.path.join(self.subj_roi_path, "Heschl_sub_left.nii.gz"),
                        'Right Heschl': os.path.join(self.subj_roi_path, "Heschl_sub_right.nii.gz")
                    },
                    'csv_file': os.path.join(self.subject_path, f"post_stats/sub-{self.subject}_task-lang_roi_stats.csv"),
                    'cut_coords': self.mni_stg_coords
                }
            }
        }

    def plot_roi(self, space, threshold=None):
        logging.info(f"Plotting ROI for {space} space with threshold {threshold}")
        png_path = os.path.join(self.subject_path, f"post_stats/sub-{self.subject}_roi_zmap_plot_{space}_{threshold}.png")
        bg_img = self.t1_native if space == 'Native' else self.t1_mni
        task_roi_mapping = self.task_roi_mapping

        fig, axes = plt.subplots(6, 1, figsize=(10, 18))  # Increased height slightly for clarity
        for i, (task_name, task_info) in enumerate(task_roi_mapping.items()):
            thresh_235_path = task_info[space]['thresh_z_map_235']
            thresh_31_path = task_info[space]['thresh_z_map_31']
            roi_paths = task_info[space]['roi_paths']  # All ROIs for the task
            cut_coords = task_info[space]['cut_coords']
            z_map_path = task_info[space]['z_map']
            if threshold == 3.1:
                img_path = thresh_31_path
                thresh_value = 3.1
            elif threshold == 2.35:
                img_path = thresh_235_path
                thresh_value = 2.35
            else:
                raise ValueError("Threshold must be 3.1 or 2.35")

            # Plot unthresholded z-map
            display1 = plotting.plot_stat_map(
                z_map_path,
                cut_coords=cut_coords,
                display_mode='z',
                vmax=13,
                colorbar=True,
                bg_img=bg_img,
                draw_cross=False,
                radiological=True,
                axes=axes[2*i])
            
            # Plot thresholded z-map
            display2 = plotting.plot_stat_map(
                img_path,
                cut_coords=cut_coords,
                display_mode='z',
                threshold=thresh_value,
                vmax=13,
                colorbar=True,
                bg_img=bg_img,
                draw_cross=False,
                radiological=True,
                axes=axes[2*i+1])

            # Add contours for all ROIs with distinct colors
            if task_name in ['Motor 1', 'Motor 2']:
                display1.add_contours(roi_paths['Whole-brain SMA + PMC'], filled=True, alpha=0.3, colors='#38cb82', linewidths=0.28)  # Green
                display2.add_contours(roi_paths['Whole-brain SMA + PMC'], filled=True, alpha=0.3, colors='#38cb82', linewidths=0.28)  # Green

            elif task_name == 'Language':
                display1.add_contours(roi_paths['Whole-brain STG'], filled=True, alpha=0.3, colors='#38cb82', linewidths=0.28)  # Green
                display1.add_contours(roi_paths['Whole-brain Heschl'], filled=True, alpha=0.3, colors='#b404f8', linewidths=0.28)  # Blue
                display2.add_contours(roi_paths['Whole-brain STG'], filled=True, alpha=0.3, colors='#38cb82', linewidths=0.28)  # Green
                display2.add_contours(roi_paths['Whole-brain Heschl'], filled=True, alpha=0.3, colors='#b404f8', linewidths=0.28)  # Blue
            
            axes[2*i].set_title(f"{self.subject}: {task_name} (Unthresholded)", fontdict={'fontweight': 'bold', 'fontsize': 10})
            axes[2*i+1].set_title(f"{self.subject}: {task_name} (Thresholded)", fontdict={'fontweight': 'bold', 'fontsize': 10})
        
        plt.savefig(png_path, dpi=150, bbox_inches='tight')
        logging.info(f"Z-map plot saved as PNG: {png_path}")
        return fig

    def plot_table(self, space, threshold):
        logging.info(f"Generating tables for {space} space with threshold {threshold}")
        df_all = pd.DataFrame()
        for task_name, task_info in self.task_roi_mapping.items():
            csv_file = task_info[space]['csv_file']
            if not os.path.exists(csv_file):
                logging.warning(f"CSV file missing: {csv_file}")
                continue
            try:
                df_task = pd.read_csv(csv_file)
                logging.info(f"Loaded {csv_file} with {len(df_task)} rows")
                df_all = pd.concat([df_all, df_task], ignore_index=True)
            except Exception as e:
                logging.error(f"Error reading {csv_file}: {str(e)}")
                continue

        # Filter for Z-stats and TFCE separately
        df_zstat = df_all[(df_all['Space'] == space) & (df_all['Threshold'] == f"Z={threshold}") & (df_all['Stat Type'] == 'Z-stat')]
        df_tfce = df_all[(df_all['Space'] == space) & (df_all['Threshold'] == 'TFCE') & (df_all['Stat Type'] == 'TFCE')]
        
        logging.info(f"Z-stat df has {len(df_zstat)} rows, TFCE df has {len(df_tfce)} rows for {space} and threshold {threshold}")

        # Define table structure
        tasks = ['Motor 1', '', '', 'Motor 2', '', '', 'Language', '', '', '', '', '']
        rois = ['Whole-brain SMA + PMC', 'Left SMA + PMC', 'Right SMA + PMC',
                'Whole-brain SMA + PMC', 'Left SMA + PMC', 'Right SMA + PMC',
                'Whole-brain STG', 'Left STG', 'Right STG',
                'Whole-brain Heschl', 'Left Heschl', 'Right Heschl']

        # Function to format table data
        def format_table_data(df):
            if df.empty:
                return [['N/A' for _ in range(6)] for _ in range(12)], 0, [0] * 12
            
            table_data = []
            roi_voxel_counts = df['Voxels in ROI (counts)'].tolist()
            wb_voxel_counts = []
            for i in range(len(df)):
                wb_voxel_count = df['Voxels in Whole Brain (counts)'].iloc[i]
                act_wb = df['Activated Voxels across Whole Brain (counts)'].iloc[i]
                act_roi = df['Activated Voxels within ROI (counts)'].iloc[i]
                perc_wb = df['Activated Voxels across Whole Brain (%)'].iloc[i]
                perc_roi = df['Activated Voxels within ROI (%)'].iloc[i]
                perc_roi_wb = df['Activated ROI/WB (%)'].iloc[i]
                ratio_roi_act_wb = df['%Activated ROI/%Activated WB (ratio)'].iloc[i]

                table_data.append([
                    tasks[i],
                    rois[i],
                    f"{act_wb} ({perc_wb:.1f}%)",
                    f"{act_roi} ({perc_roi:.1f}%)",
                    f"{ratio_roi_act_wb:.1f}",
                    f"{perc_roi_wb:.1f}"
                ])
                wb_voxel_counts.append(wb_voxel_count)
            return table_data, wb_voxel_counts, roi_voxel_counts

        # Z-stat table
        zstat_data, zstat_wb_voxels, zstat_roi_voxels = format_table_data(df_zstat)
        fig_zstat, ax_zstat = plt.subplots(figsize=(10, 6))  # Increased height for more rows
        column_labels = ['Task', 'ROI', 'Activated Voxels\nacross Whole Brain', 
                         'Activated Voxels\nwithin ROI', '%Activated ROI\n/%Activated WB (ratio)*',
                         'Activated Voxels in\nROI across WB (%)*']
        
        if not df_zstat.empty:
            table = ax_zstat.table(cellText=zstat_data, colLabels=column_labels, loc='center', cellLoc='center', bbox=[0, 0, 1, 1])
            table.auto_set_font_size(False)
            table.set_fontsize(8)
            table.auto_set_column_width(col=list(range(len(column_labels))))
            for (row, col), cell in table.get_celld().items():
                if row == 0:
                    cell.set_text_props(weight='bold', color='white')
                    cell.set_facecolor('#4CAF50')
                    cell.set_height(0.1)
                elif row % 3 == 1:
                    cell.set_facecolor('#f2f2f2')
                cell.set_height(0.07)
        else:
            ax_zstat.text(0.5, 0.5, f"No Z-stat data available for {space} space (Z={threshold})", 
                          ha='center', va='center', fontsize=10, color='red')
        
        ax_zstat.axis('off')
        plt.suptitle(f"Supra-thresholded Voxels in {space} Space (Z={threshold})", fontweight='bold', fontsize=12)
        annotation_text = (
            f"Whole-brain voxel counts: {', '.join(map(str, zstat_wb_voxels))}\n"
            f"ROI voxel counts (order follows table): {', '.join(map(str, zstat_roi_voxels))}\n"
            "*%Activated ROI/%Activated WB (ratio): Percent act. voxels in ROI (Column 4) divided by Percent act. voxels in Whole Brain (Column 3)\n"
            "*Activated Voxels in ROI across WB (%): Activated voxels in ROI (Column 4) divided by Whole-brain voxel counts"
        )
        plt.annotate(annotation_text, xy=(0, 0), xytext=(0, -50), xycoords='axes fraction', textcoords='offset points', fontsize=8)
        png_path_zstat = os.path.join(self.subject_path, f"post_stats/sub-{self.subject}_roi_stats_table_{space}_zstat_{threshold}.png")
        plt.savefig(png_path_zstat, bbox_inches='tight', dpi=150)
        logging.info(f"Z-stat table saved as PNG: {png_path_zstat}")

        # TFCE table
        tfce_data, tfce_wb_voxels, tfce_roi_voxels = format_table_data(df_tfce)
        fig_tfce, ax_tfce = plt.subplots(figsize=(10, 6))  # Increased height for more rows
        
        if not df_tfce.empty:
            table = ax_tfce.table(cellText=tfce_data, colLabels=column_labels, loc='center', cellLoc='center', bbox=[0, 0, 1, 1])
            table.auto_set_font_size(False)
            table.set_fontsize(8)
            table.auto_set_column_width(col=list(range(len(column_labels))))
            for (row, col), cell in table.get_celld().items():
                if row == 0:
                    cell.set_text_props(weight='bold', color='white')
                    cell.set_facecolor('#4CAF50')
                    cell.set_height(0.1)
                elif row % 3 == 1:
                    cell.set_facecolor('#f2f2f2')
                cell.set_height(0.07)  # Adjusted height for more rows
        else:
            ax_tfce.text(0.5, 0.5, f"No TFCE data available for {space} space (TFCE)", 
                         ha='center', va='center', fontsize=10, color='red')
        
        ax_tfce.axis('off')
        plt.suptitle(f"Supra-thresholded Voxels in {space} Space (p-corrected t-map)", fontweight='bold', fontsize=12)
        annotation_text = (
            f"Whole-brain voxel counts: {', '.join(map(str, tfce_wb_voxels))}\n"
            f"ROI voxel counts (order follows table): {', '.join(map(str, tfce_roi_voxels))}\n"
           "*%Activated ROI/%Activated WB (ratio): Percent act. voxels in ROI (Column 4) divided by Percent act. voxels in Whole Brain (Column 3)\n"
            "*Activated Voxels in ROI across WB (%): Activated voxels in ROI (Column 4) divided by Whole-brain voxel counts"
        )
        plt.annotate(annotation_text, xy=(0, 0), xytext=(0, -50), xycoords='axes fraction', textcoords='offset points', fontsize=8)
        png_path_tfce = os.path.join(self.subject_path, f"post_stats/sub-{self.subject}_roi_stats_table_{space}_tfce_p005.png")
        plt.savefig(png_path_tfce, bbox_inches='tight', dpi=150)
        logging.info(f"TFCE table saved as PNG: {png_path_tfce}")

        return fig_zstat, df_zstat, fig_tfce, df_tfce

    def process_data(self):
        logging.info(f"Processing data for subject {self.subject}")
        # native_roi_fig_31 = self.plot_roi('Native', threshold=3.1)
        # native_roi_fig_235 = self.plot_roi('Native', threshold=2.35)
        native_table_fig_zstat_31, native_df_zstat_31, native_table_fig_tfce_31, native_df_tfce_31 = self.plot_table('Native', threshold=3.1)
        native_table_fig_zstat_235, native_df_zstat_235, native_table_fig_tfce_235, native_df_tfce_235 = self.plot_table('Native', threshold=2.35)
        mni_roi_fig_31 = self.plot_roi('MNI', threshold=3.1)
        mni_roi_fig_235 = self.plot_roi('MNI', threshold=2.35)
        mni_table_fig_zstat_31, mni_df_zstat_31, mni_table_fig_tfce_31, mni_df_tfce_31 = self.plot_table('MNI', threshold=3.1)
        mni_table_fig_zstat_235, mni_df_zstat_235, mni_table_fig_tfce_235, mni_df_tfce_235 = self.plot_table('MNI', threshold=2.35)

        native_viewers_31 = {task: plotting.view_img(task_info['Native']['thresh_z_map_31'], 
                                                     bg_img=self.t1_native, threshold=3.1, title=f"{task} Z=3.1")
                             for task, task_info in self.task_roi_mapping.items()}
        native_viewers_unthresh_31 = {task: plotting.view_img(task_info['Native']['z_map'],
                                                              bg_img=self.t1_native, threshold=0, title=f"{task} Unthresholded")
                                      for task, task_info in self.task_roi_mapping.items()}
        native_viewers_235 = {task: plotting.view_img(task_info['Native']['thresh_z_map_235'], 
                                                      bg_img=self.t1_native, threshold=2.35, title=f"{task} Z=2.35")
                              for task, task_info in self.task_roi_mapping.items()}
        native_viewers_unthresh_235 = {task: plotting.view_img(task_info['Native']['z_map'],
                                                              bg_img=self.t1_native, threshold=0, title=f"{task} Unthresholded")
                                      for task, task_info in self.task_roi_mapping.items()}
        return {
            # 'native_roi_fig_31': native_roi_fig_31,
            # 'native_roi_fig_235': native_roi_fig_235,
            'native_table_fig_zstat_31': native_table_fig_zstat_31,
            'native_table_fig_tfce_31': native_table_fig_tfce_31,
            'native_table_fig_zstat_235': native_table_fig_zstat_235,
            'native_table_fig_tfce_235': native_table_fig_tfce_235,
            'mni_roi_fig_31': mni_roi_fig_31,
            'mni_roi_fig_235': mni_roi_fig_235,
            'mni_table_fig_zstat_31': mni_table_fig_zstat_31,
            'mni_table_fig_tfce_31': mni_table_fig_tfce_31,
            'mni_table_fig_zstat_235': mni_table_fig_zstat_235,
            'mni_table_fig_tfce_235': mni_table_fig_tfce_235,
            'native_viewers_31': native_viewers_31,
            'native_viewers_unthresh_31': native_viewers_unthresh_31,
        }
