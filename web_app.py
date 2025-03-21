import streamlit as st
import pandas as pd
from telecom_analyzer import main, validate_traffic_file, validate_tags_file
import os

st.title("Telecom Testing Number Analyzer")

with st.expander("⚠️ REQUIRED FILE FORMATS", expanded=True):
    st.markdown("""
    **Traffic File Must Contain:**
    - Client Name
    - Destination Number
    - Content
    - Sender ID

    **Tags File Must Contain:**
    - Tag values (column with known testing numbers)
    """)

traffic_file = st.file_uploader("Upload Traffic Data (.xlsx)", type="xlsx")
tags_file = st.file_uploader("Upload Known Testing Numbers (.xlsx)", type="xlsx")

if st.button("Analyze"):
    if traffic_file and tags_file:
        try:
            # Validate files before processing
            traffic_df = pd.read_excel(traffic_file)
            tags_df = pd.read_excel(tags_file)
            
            traffic_issues = validate_traffic_file(traffic_df)
            tags_issues = "Tag values" not in tags_df.columns
            
            if traffic_issues or tags_issues:
                error_msg = []
                if traffic_issues:
                    error_msg.append(f"Missing in Traffic File: {', '.join(traffic_issues)}")
                if tags_issues:
                    error_msg.append("Missing 'Tag values' column in Tags File")
                st.error("\n".join(error_msg))
                raise ValueError("Invalid file format")

            # Save temporary files
            TRAFFIC_PATH = "temp_traffic.xlsx"
            TAGS_PATH = "temp_tags.xlsx"
            
            with open(TRAFFIC_PATH, "wb") as f:
                f.write(traffic_file.getvalue())
            with open(TAGS_PATH, "wb") as f:
                f.write(tags_file.getvalue())

            # Run analysis
            main(traffic_file=TRAFFIC_PATH, tags_file=TAGS_PATH)
            
            # Offer download
            with open("testing_numbers_analysis.xlsx", "rb") as f:
                st.download_button(
                    label="📥 Download Report",
                    data=f,
                    file_name="testing_analysis_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
        except Exception as e:
            st.error(f"Analysis failed: {str(e)}")
        finally:
            # Cleanup
            if os.path.exists(TRAFFIC_PATH):
                os.remove(TRAFFIC_PATH)
            if os.path.exists(TAGS_PATH):
                os.remove(TAGS_PATH)
    else:
        st.warning("Please upload both files first!")