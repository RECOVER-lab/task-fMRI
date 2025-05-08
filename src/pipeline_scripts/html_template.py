# html_template.py: Updated HTML template for output_generator.py
# Updated to add unthresholded viewers with iframes and links, Apr 2025
# Updated to make figures, tables, and viewers the same width, May 2025
# Updated to fix Native Space Z=2.35 tab, remove Z=2.35 viewers, reduce viewer spacing, and left-align elements, May 2025

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{subject}: Task-Based fMRI Report</title>
    <style>
        .space-tab {{
            overflow: hidden;
            border: 1px solid #ccc;
            background-color: #f1f1f1;
        }}
        .space-tab button {{
            background-color: inherit;
            float: left;
            border: none;
            outline: none;
            cursor: pointer;
            padding: 14px 16px;
            transition: 0.3s;
        }}
        .space-tab button:hover {{
            background-color: #ddd;
        }}
        .space-tab button.active {{
            background-color: #ccc;
        }}
        .space-tabcontent {{
            display: none;
            padding: 6px 12px;
            border: 1px solid #ccc;
            border-top: none;
        }}
        .thresh-tab {{
            overflow: hidden;
            background-color: #e9ecef;
        }}
        .thresh-tab button {{
            background-color: inherit;
            float: left;
            border: none;
            outline: none;
            cursor: pointer;
            padding: 10px 12px;
            transition: 0.3s;
        }}
        .thresh-tab button:hover {{
            background-color: #ced4da;
        }}
        .thresh-tab button.active {{
            background-color: #adb5bd;
        }}
        .thresh-tabcontent {{
            display: none;
            padding: 6px 12px;
        }}
        .report-element {{
            width: 100%;
            max-width: 1200px;
            height: auto;
            display: block;
            margin: 0; /* Left-align by removing auto margins */
            text-align: left; /* Ensure text is left-aligned */
        }}
        img.report-element {{
            /* Ensure images scale properly */
        }}
        .viewer {{
            aspect-ratio: 4/3;
            margin-bottom: 5px; /* Reduced from 20px for smaller spacing */
            border: none;
        }}
    </style>
</head>
<body>
    <h1>{subject} Task-Based fMRI Report</h1>
    <div class="space-tab">
        <button class="space-tablinks" onclick="openSpaceTab(event, 'Native')" id="defaultSpaceOpen">Native Space</button>
        <button class="space-tablinks" onclick="openSpaceTab(event, 'MNI')">MNI Space</button>
    </div>

    <!-- Native Space Content -->
    <div id="Native" class="space-tabcontent">
        <div class="thresh-tab">
            <button class="thresh-tablinks" onclick="openThreshTab(event, 'Native_31', 'Native')" id="defaultThreshNative">Cluster-Threshold Z=3.1</button>
            <button class="thresh-tablinks" onclick="openThreshTab(event, 'Native_235', 'Native')">Cluster-Threshold Z=2.35</button>
        </div>
        <div id="Native_31" class="thresh-tabcontent">
            <h2>Z-Maps with ROI Outlines (Native Space, Z=3.1)</h2>
            <img src="data:image/png;base64,{native_roi_img_31}" alt="Native ROI Plot Z=3.1" class="report-element">
            <h2>GLM Test Z-map ROI Statistics Table (Z-map, Native Space, Z=3.1)</h2>
            <img src="data:image/png;base64,{native_table_img_zstat_31}" alt="Native Z-Stat Table Plot Z=3.1" class="report-element">
            <h2>Permutation Test T-map ROI Statistics Table (p-corrected t-map, Native Space, p<0.05)</h2>
            <img src="data:image/png;base64,{native_table_img_tfce_31}" alt="Native TFCE Table Plot Z=3.1" class="report-element">
            <h2>Interactive Brain Viewer (Native Space, Z=3.1)</h2>
            <h3>Motor 1</h3>
            <iframe src="{native_viewer_unthresh_31_motor1}" class="viewer report-element"></iframe>
            <p><a href="{native_viewer_unthresh_31_motor1}" target="_blank">Open Motor 1 Z=3.1 Viewer in New Tab</a></p>
            <h3>Motor 2</h3>
            <iframe src="{native_viewer_unthresh_31_motor2}" class="viewer report-element"></iframe>
            <p><a href="{native_viewer_unthresh_31_motor2}" target="_blank">Open Motor 2 Z=3.1 Viewer in New Tab</a></p>
            <h3>Language</h3>
            <iframe src="{native_viewer_unthresh_31_language}" class="viewer report-element"></iframe>
            <p><a href="{native_viewer_unthresh_31_language}" target="_blank">Open Language Z=3.1 Viewer in New Tab</a></p>
        </div>
        <div id="Native_235" class="thresh-tabcontent">
            <h2>Z-Maps with ROI Outlines (Native Space, Z=2.35)</h2>
            <img src="data:image/png;base64,{native_roi_img_235}" alt="Native ROI Plot Z=2.35" class="report-element">
            <h2>GLM Test Z-map ROI Statistics Table (Native Space, Z=2.35)</h2>
            <img src="data:image/png;base64,{native_table_img_zstat_235}" alt="Native Z-Stat Table Plot Z=2.35" class="report-element">
            <h2>Permutation Test T-map ROI Statistics Table (Native Space, p<0.05)</h2>
            <img src="data:image/png;base64,{native_table_img_tfce_235}" alt="Native TFCE Table Plot Z=2.35" class="report-element">
        </div>
    </div>

    <!-- MNI Space Content -->
    <div id="MNI" class="space-tabcontent">
        <div class="thresh-tab">
            <button class="thresh-tablinks" onclick="openThreshTab(event, 'MNI_31', 'MNI')" id="defaultThreshMNI">Cluster-Threshold Z=3.1</button>
            <button class="thresh-tablinks" onclick="openThreshTab(event, 'MNI_235', 'MNI')">Cluster-Threshold Z=2.35</button>
        </div>
        <div id="MNI_31" class="thresh-tabcontent">
            <h2>Z-Maps with ROI Outlines (MNI Space, Z=3.1)</h2>
            <img src="data:image/png;base64,{mni_roi_img_31}" alt="MNI ROI Plot Z=3.1" class="report-element">
            <h2>Z-Stat ROI Statistics Table (MNI Space, Z=3.1)</h2>
            <img src="data:image/png;base64,{mni_table_img_zstat_31}" alt="MNI Z-Stat Table Plot Z=3.1" class="report-element">
            <h2>Permutation Test T-map ROI Statistics Table (MNI Space, p<0.05)</h2>
            <img src="data:image/png;base64,{mni_table_img_tfce_31}" alt="MNI TFCE Table Plot Z=3.1" class="report-element">
        </div>
        <div id="MNI_235" class="thresh-tabcontent">
            <h2>Z-Maps with ROI Outlines (MNI Space, Z=2.35)</h2>
            <img src="data:image/png;base64,{mni_roi_img_235}" alt="MNI ROI Plot Z=2.35" class="report-element">
            <h2>GLM Test Z-map ROI Statistics Table (MNI Space, Z=2.35)</h2>
            <img src="data:image/png;base64,{mni_table_img_zstat_235}" alt="MNI Z-Stat Table Plot Z=2.35" class="report-element">
            <h2>Permutation Test T-map ROI Statistics Table (MNI Space, p<0.05)</h2>
            <img src="data:image/png;base64,{mni_table_img_tfce_235}" alt="MNI TFCE Table Plot Z=2.35" class="report-element">
        </div>
    </div>

    <script>
        function openSpaceTab(evt, spaceName) {{
            var i, spaceTabcontent, spaceTablinks;
            spaceTabcontent = document.getElementsByClassName("space-tabcontent");
            for (i = 0; i < spaceTabcontent.length; i++) {{
                spaceTabcontent[i].style.display = "none";
            }}
            spaceTablinks = document.getElementsByClassName("space-tablinks");
            for (i = 0; i < spaceTablinks.length; i++) {{
                spaceTablinks[i].className = spaceTablinks[i].className.replace(" active", "");
            }}
            document.getElementById(spaceName).style.display = "block";
            evt.currentTarget.className += " active";
            document.getElementById("defaultThresh" + spaceName).click();
        }}

        function openThreshTab(evt, threshName, spaceName) {{
            var i, threshTabcontent, threshTablinks;
            threshTabcontent = document.getElementsByClassName("thresh-tabcontent");
            for (i = 0; i < threshTabcontent.length; i++) {{
                if (threshTabcontent[i].parentElement.id === spaceName) {{
                    threshTabcontent[i].style.display = "none";
                }}
            }}
            threshTablinks = document.getElementsByClassName("thresh-tablinks");
            for (i = 0; i < threshTablinks.length; i++) {{
                if (threshTablinks[i].parentElement.parentElement.id === spaceName) {{
                    threshTablinks[i].className = threshTablinks[i].className.replace(" active", "");
                }}
            }}
            document.getElementById(threshName).style.display = "block";
            evt.currentTarget.className += " active";
        }}

        document.getElementById("defaultSpaceOpen").click();
    </script>
</body>
</html>
"""