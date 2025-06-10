#!/opt/anaconda3/bin/python
# Python 3.8.20
# output_generator.py: Simplified and optimized functions to generate PDF and HTML reports
# Updated to include separate Z-stat and TFCE tables, and to match HTML layout for native and MNI spaces, Oct 2025
# Updated to add unthresholded viewers, generate HTML directly if plots/tables exist, and adjust sizes, Apr 2025
# Updated to restore iframe-based viewers with links and always regenerate viewers, Apr 2025

import os
import sys
import logging
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import base64
from io import BytesIO
from html_template import HTML_TEMPLATE

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class OutputGenerator:
    def __init__(self, subject, path_img):
        self.subject = subject
        self.path_img = path_img
        self.subject_path = os.path.join(path_img, f"derivatives/sub-{subject}/ses-01")
        self.output_dir = os.path.join(self.subject_path, "post_stats")
        os.makedirs(self.output_dir, exist_ok=True)  # Ensure directory exists once here
        logging.info(f"Initializing OutputGenerator for subject {subject}")

    def _fig_to_base64(self, fig):
        """Convert a matplotlib figure to base64-encoded PNG string efficiently."""
        if not fig:
            return ""
        with BytesIO() as buf:
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close(fig)  # Close figure immediately after saving
        return img_str

    def _check_existing_files(self):
        """Check if all required plots and tables exist in the output directory."""
        required_files = [
            f"sub-{self.subject}_roi_zmap_plot_Native_3.1.png",
            f"sub-{self.subject}_roi_zmap_plot_Native_2.35.png",
            f"sub-{self.subject}_roi_stats_table_Native_zstat_3.1.png",
            f"sub-{self.subject}_roi_stats_table_Native_tfce_p005.png",
            f"sub-{self.subject}_roi_stats_table_Native_zstat_2.35.png",
            f"sub-{self.subject}_roi_stats_table_Native_tfce_p005.png",
            f"sub-{self.subject}_roi_zmap_plot_MNI_3.1.png",
            f"sub-{self.subject}_roi_zmap_plot_MNI_2.35.png",
            f"sub-{self.subject}_roi_stats_table_MNI_zstat_3.1.png",
            f"sub-{self.subject}_roi_stats_table_MNI_tfce_p005.png",
            f"sub-{self.subject}_roi_stats_table_MNI_zstat_2.35.png",
            f"sub-{self.subject}_roi_stats_table_MNI_tfce_p005.png",
        ]
        all_exist = all(os.path.exists(os.path.join(self.output_dir, f)) for f in required_files)
        logging.info(f"All required plot and table files exist: {all_exist}")
        return all_exist

    def _load_existing_fig(self, filename):
        """Load an existing PNG file as a matplotlib figure with size matching generated figures."""
        filepath = os.path.join(self.output_dir, filename)
        if not os.path.exists(filepath):
            return None
        
        # Determine figure size based on file type (match data_processor.py)
        if 'roi_zmap_plot' in filename:
            figsize = (10, 18)  # Size for ROI plots from plot_roi
        elif 'roi_stats_table' in filename:
            figsize = (16, 6)   # Size for tables from plot_table
        else:
            figsize = (10, 10)  # Default fallback size
        
        fig, ax = plt.subplots(figsize=figsize)
        ax.imshow(plt.imread(filepath))
        ax.axis('off')
        return fig

    def _save_pdf(self, data):
        """Generate and save PDF report with native and MNI space figures, mimicking HTML layout."""
        pdf_path = os.path.join(self.output_dir, f"sub-{self.subject}_task_pipeline_report.pdf")

        with PdfPages(pdf_path) as pdf:
            # Cover page
            fig, ax = plt.subplots(figsize=(10, 2))
            ax.text(0.5, 0.5, f"Task-Based fMRI Report for {self.subject}", ha='center', va='center', fontsize=14)
            ax.axis('off')
            pdf.savefig(fig, dpi=300, bbox_inches='tight')
            plt.close(fig)

            # Z=3.1 Section (Native Space)
            fig_native_31, (ax_roi_native_31, ax_zstat_native_31, ax_tfce_native_31) = plt.subplots(3, 1, figsize=(10, 12))
            plt.tight_layout(h_pad=4)

            # ROI Plot (Native, Z=3.1)
            if data.get('native_roi_fig_31'):
                ax_roi_native_31.imshow(plt.imread(os.path.join(self.subject_path, f"post_stats/sub-{self.subject}_roi_zmap_plot_Native_3.1.png")))
                ax_roi_native_31.axis('off')
                ax_roi_native_31.set_title("Z-Maps with ROI Outlines (Native, Z=3.1)", fontdict={'fontweight': 'bold', 'fontsize': 10})

            # Z-Stat Table (Native, Z=3.1)
            if data.get('native_table_fig_zstat_31'):
                ax_zstat_native_31.imshow(plt.imread(os.path.join(self.subject_path, f"post_stats/sub-{self.subject}_roi_stats_table_Native_zstat_3.1.png")))
                ax_zstat_native_31.axis('off')
                ax_zstat_native_31.set_title("GLM Test Z-map ROI Statistics (Native, Z=3.1)", fontdict={'fontweight': 'bold', 'fontsize': 10})

            # TFCE Table (Native, Z=3.1)
            if data.get('native_table_fig_tfce_31'):
                ax_tfce_native_31.imshow(plt.imread(os.path.join(self.subject_path, f"post_stats/sub-{self.subject}_roi_stats_table_Native_tfce_p005.png")))
                ax_tfce_native_31.axis('off')
                ax_tfce_native_31.set_title("Permutation Test T-map ROI Statistics (Native, p<0.05)", fontdict={'fontweight': 'bold', 'fontsize': 10})

            plt.suptitle("Native Space Results (Z=3.1)", fontweight='bold', fontsize=12, y=0.98)
            pdf.savefig(fig_native_31, dpi=300, bbox_inches='tight')
            plt.close(fig_native_31)

            # Z=3.1 Section (MNI Space)
            fig_mni_31, (ax_roi_mni_31, ax_zstat_mni_31, ax_tfce_mni_31) = plt.subplots(3, 1, figsize=(10, 12))
            plt.tight_layout(h_pad=4)

            # ROI Plot (MNI, Z=3.1)
            if data.get('mni_roi_fig_31'):
                ax_roi_mni_31.imshow(plt.imread(os.path.join(self.subject_path, f"post_stats/sub-{self.subject}_roi_zmap_plot_MNI_3.1.png")))
                ax_roi_mni_31.axis('off')
                ax_roi_mni_31.set_title("Z-Maps with ROI Outlines (MNI, Z=3.1)", fontdict={'fontweight': 'bold', 'fontsize': 10})

            # Z-Stat Table (MNI, Z=3.1)
            if data.get('mni_table_fig_zstat_31'):
                ax_zstat_mni_31.imshow(plt.imread(os.path.join(self.subject_path, f"post_stats/sub-{self.subject}_roi_stats_table_MNI_zstat_3.1.png")))
                ax_zstat_mni_31.axis('off')
                ax_zstat_mni_31.set_title("GLM Test Z-map ROI Statistics (MNI, Z=3.1)", fontdict={'fontweight': 'bold', 'fontsize': 10})

            # TFCE Table (MNI, Z=3.1)
            if data.get('mni_table_fig_tfce_31'):
                ax_tfce_mni_31.imshow(plt.imread(os.path.join(self.subject_path, f"post_stats/sub-{self.subject}_roi_stats_table_MNI_tfce_p005.png")))
                ax_tfce_mni_31.axis('off')
                ax_tfce_mni_31.set_title("Permutation Test ROI Statistics (MNI, p<0.05)", fontdict={'fontweight': 'bold', 'fontsize': 10})

            plt.suptitle("MNI Space Results (Z=3.1)", fontweight='bold', fontsize=12, y=0.98)
            pdf.savefig(fig_mni_31, dpi=300, bbox_inches='tight')
            plt.close(fig_mni_31)

            # Z=2.35 Section (Native Space)
            fig_native_235, (ax_roi_native_235, ax_zstat_native_235, ax_tfce_native_235) = plt.subplots(3, 1, figsize=(10, 12))
            plt.tight_layout(h_pad=4)

            # ROI Plot (Native, Z=2.35)
            if data.get('native_roi_fig_235'):
                ax_roi_native_235.imshow(plt.imread(os.path.join(self.subject_path, f"post_stats/sub-{self.subject}_roi_zmap_plot_Native_2.35.png")))
                ax_roi_native_235.axis('off')
                ax_roi_native_235.set_title("Z-Maps with ROI Outlines (Native, Z=2.35)", fontdict={'fontweight': 'bold', 'fontsize': 10})

            # Z-Stat Table (Native, Z=2.35)
            if data.get('native_table_fig_zstat_235'):
                ax_zstat_native_235.imshow(plt.imread(os.path.join(self.subject_path, f"post_stats/sub-{self.subject}_roi_stats_table_Native_zstat_2.35.png")))
                ax_zstat_native_235.axis('off')
                ax_zstat_native_235.set_title("GLM Test Z-map ROI Statistics (Native, Z=2.35)", fontdict={'fontweight': 'bold', 'fontsize': 10})

            # TFCE Table (Native, Z=2.35)
            if data.get('native_table_fig_tfce_235'):
                ax_tfce_native_235.imshow(plt.imread(os.path.join(self.subject_path, f"post_stats/sub-{self.subject}_roi_stats_table_Native_tfce_p005.png")))
                ax_tfce_native_235.axis('off')
                ax_tfce_native_235.set_title("Permutation Test T-map ROI Statistics (Native, p<0.05)", fontdict={'fontweight': 'bold', 'fontsize': 10})

            plt.suptitle("Native Space Results (Z=2.35)", fontweight='bold', fontsize=12, y=0.98)
            pdf.savefig(fig_native_235, dpi=300, bbox_inches='tight')
            plt.close(fig_native_235)

            # Z=2.35 Section (MNI Space)
            fig_mni_235, (ax_roi_mni_235, ax_zstat_mni_235, ax_tfce_mni_235) = plt.subplots(3, 1, figsize=(10, 12))
            plt.tight_layout(h_pad=4)

            # ROI Plot (MNI, Z=2.35)
            if data.get('mni_roi_fig_235'):
                ax_roi_mni_235.imshow(plt.imread(os.path.join(self.subject_path, f"post_stats/sub-{self.subject}_roi_zmap_plot_MNI_2.35.png")))
                ax_roi_mni_235.axis('off')
                ax_roi_mni_235.set_title("Z-Maps with ROI Outlines (MNI, Z=2.35)", fontdict={'fontweight': 'bold', 'fontsize': 10})

            # Z-Stat Table (MNI, Z=2.35)
            if data.get('mni_table_fig_zstat_235'):
                ax_zstat_mni_235.imshow(plt.imread(os.path.join(self.subject_path, f"post_stats/sub-{self.subject}_roi_stats_table_MNI_zstat_2.35.png")))
                ax_zstat_mni_235.axis('off')
                ax_zstat_mni_235.set_title("GLM Test Z-map ROI Statistics (MNI, Z=2.35)", fontdict={'fontweight': 'bold', 'fontsize': 10})

            # TFCE Table (MNI, Z=2.35)
            if data.get('mni_table_fig_tfce_235'):
                ax_tfce_mni_235.imshow(plt.imread(os.path.join(self.subject_path, f"post_stats/sub-{self.subject}_roi_stats_table_MNI_tfce_p005.png")))
                ax_tfce_mni_235.axis('off')
                ax_tfce_mni_235.set_title("Permutation Test T-map Statistics (MNI, p<0.05)", fontdict={'fontweight': 'bold', 'fontsize': 10})

            plt.suptitle("MNI Space Results (Z=2.35)", fontweight='bold', fontsize=12, y=0.98)
            pdf.savefig(fig_mni_235, dpi=300, bbox_inches='tight')
            plt.close(fig_mni_235)

        logging.info(f"Combined PDF saved at: {pdf_path}")
        return pdf_path

    def _save_html(self, data, skip_plot_processing=False):
        """Generate and save HTML report with embedded images and viewer links, always regenerating viewers."""
        html_path = os.path.join(self.output_dir, f"sub-{self.subject}_task_pipeline_report.html")
        viewer_dir = os.path.join(self.output_dir, "viewers")
        os.makedirs(viewer_dir, exist_ok=True)

        # Load or convert figures to base64
        if skip_plot_processing:
            img_data = {
                'native_roi_img_31': self._fig_to_base64(self._load_existing_fig(f"sub-{self.subject}_roi_zmap_plot_Native_3.1.png")),
                'native_roi_img_235': self._fig_to_base64(self._load_existing_fig(f"sub-{self.subject}_roi_zmap_plot_Native_2.35.png")),
                'native_table_img_zstat_31': self._fig_to_base64(self._load_existing_fig(f"sub-{self.subject}_roi_stats_table_Native_zstat_3.1.png")),
                'native_table_img_tfce_31': self._fig_to_base64(self._load_existing_fig(f"sub-{self.subject}_roi_stats_table_Native_tfce_p005.png")),
                'native_table_img_zstat_235': self._fig_to_base64(self._load_existing_fig(f"sub-{self.subject}_roi_stats_table_Native_zstat_2.35.png")),
                'native_table_img_tfce_235': self._fig_to_base64(self._load_existing_fig(f"sub-{self.subject}_roi_stats_table_Native_tfce_p005.png")),
                'mni_roi_img_31': self._fig_to_base64(self._load_existing_fig(f"sub-{self.subject}_roi_zmap_plot_MNI_3.1.png")),
                'mni_roi_img_235': self._fig_to_base64(self._load_existing_fig(f"sub-{self.subject}_roi_zmap_plot_MNI_2.35.png")),
                'mni_table_img_zstat_31': self._fig_to_base64(self._load_existing_fig(f"sub-{self.subject}_roi_stats_table_MNI_zstat_3.1.png")),
                'mni_table_img_tfce_31': self._fig_to_base64(self._load_existing_fig(f"sub-{self.subject}_roi_stats_table_MNI_tfce_p005.png")),
                'mni_table_img_zstat_235': self._fig_to_base64(self._load_existing_fig(f"sub-{self.subject}_roi_stats_table_MNI_zstat_2.35.png")),
                'mni_table_img_tfce_235': self._fig_to_base64(self._load_existing_fig(f"sub-{self.subject}_roi_stats_table_MNI_tfce_p005.png")),
            }
        else:
            img_data = {
                'native_roi_img_31': self._fig_to_base64(data.get('native_roi_fig_31')),
                'native_roi_img_235': self._fig_to_base64(data.get('native_roi_fig_235')),
                'native_table_img_zstat_31': self._fig_to_base64(data.get('native_table_fig_zstat_31')),
                'native_table_img_tfce_31': self._fig_to_base64(data.get('native_table_fig_tfce_31')),
                'native_table_img_zstat_235': self._fig_to_base64(data.get('native_table_fig_zstat_235')),
                'native_table_img_tfce_235': self._fig_to_base64(data.get('native_table_fig_tfce_235')),
                'mni_roi_img_31': self._fig_to_base64(data.get('mni_roi_fig_31')),
                'mni_roi_img_235': self._fig_to_base64(data.get('mni_roi_fig_235')),
                'mni_table_img_zstat_31': self._fig_to_base64(data.get('mni_table_fig_zstat_31')),
                'mni_table_img_tfce_31': self._fig_to_base64(data.get('mni_table_fig_tfce_31')),
                'mni_table_img_zstat_235': self._fig_to_base64(data.get('mni_table_fig_zstat_235')),
                'mni_table_img_tfce_235': self._fig_to_base64(data.get('mni_table_fig_tfce_235')),
            }

        # Always save viewers and prepare relative paths
        viewer_paths = {}
        tasks = ['Motor 1', 'Motor 2', 'Language']
        
        # Save viewers for Z=3.1
        native_viewers_31 = data.get('native_viewers_31', {})
        for task in tasks:
            viewer_key = f"native_viewer_31_{task.lower().replace(' ', '_')}"
            viewer_file = f"native_{task.lower().replace(' ', '_')}_z31_viewer.html"
            viewer_paths[viewer_key] = os.path.join("viewers", viewer_file)
            if task in native_viewers_31:
                native_viewers_31[task].save_as_html(os.path.join(viewer_dir, viewer_file))

        # Save unthresholded viewers for Z=3.1 base
        native_viewers_unthresh_31 = data.get('native_viewers_unthresh_31', {})
        for task in tasks:
            viewer_key = f"native_viewer_unthresh_31_{task.lower().replace(' ', '_')}"
            viewer_file = f"native_{task.lower().replace(' ', '_')}_unthresh_z31_viewer.html"
            viewer_paths[viewer_key] = os.path.join("viewers", viewer_file)
            if task in native_viewers_unthresh_31:
                native_viewers_unthresh_31[task].save_as_html(os.path.join(viewer_dir, viewer_file))

        # Generate HTML content
        html_content = HTML_TEMPLATE.format(
            subject=self.subject,
            **img_data,
            # native_viewer_31_motor1=viewer_paths.get('native_viewer_31_motor_1', ''),
            # native_viewer_31_motor2=viewer_paths.get('native_viewer_31_motor_2', ''),
            # native_viewer_31_language=viewer_paths.get('native_viewer_31_language', ''),
            native_viewer_unthresh_31_motor1=viewer_paths.get('native_viewer_unthresh_31_motor_1', ''),
            native_viewer_unthresh_31_motor2=viewer_paths.get('native_viewer_unthresh_31_motor_2', ''),
            native_viewer_unthresh_31_language=viewer_paths.get('native_viewer_unthresh_31_language', ''),
        )

        with open(html_path, 'w') as f:
            f.write(html_content)
        logging.info(f"Combined HTML saved at: {html_path}")
        return html_path

    def generate_output(self, data):
        """Generate PDF and HTML outputs for the subject, regenerating viewers always."""
        logging.info(f"Generating output for subject {self.subject}")
        try:
            if self._check_existing_files():
                logging.info("All plots and tables found, loading existing files but regenerating viewers.")
                self._save_html(data, skip_plot_processing=True)
            else:
                logging.info("Generating all outputs from scratch.")
                self._save_pdf(data)
                self._save_html(data, skip_plot_processing=False)
        except Exception as e:
            logging.error(f"Error generating output for subject {self.subject}: {str(e)}")
            raise

def main(subjects):
    logging.info("Starting main execution")
    path_img = os.environ.get('ARCHIVEDIR')
    roi_path = os.environ.get('ROI')
    from data_processor import DataProcessor

    for subject in subjects:
        logging.info(f"Processing subject: {subject}")
        output_generator = OutputGenerator(subject, path_img)
        data_processor = DataProcessor(subject, path_img, roi_path)
        data = data_processor.process_data()
        output_generator.generate_output(data)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logging.error("No subject IDs provided. Usage: python output_generator.py <subject_id1> <subject_id2> ...")
        sys.exit(1)
    subjects = sys.argv[1:]
    main(subjects)