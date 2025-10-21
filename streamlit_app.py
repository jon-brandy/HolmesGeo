import streamlit as st
import subprocess
import os
import tempfile
import pandas as pd
from datetime import datetime
import io
import sys
import re

# Page configuration
st.set_page_config(
    page_title="HolmesGeo - IP Geolocation Checker",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    .upload-section {
        background-color: #f0f2f6;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# # Header
# st.markdown('<p class="main-header">HolmesGeo</p>', unsafe_allow_html=True)
# st.markdown('<p class="sub-header">A Simple Tool for IP Geolocation Check</p>', unsafe_allow_html=True)
# st.markdown("---")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Keys configuration
    st.subheader("API Key")
    vt_api_key = st.text_input("VirusTotal API Key", type="password", 
                                help="Optional: Add your VirusTotal API key for malicious IP detection")
    
    use_virustotal = st.checkbox("Enable VirusTotal Check", 
                                  value=False,
                                  help="Check IPs against VirusTotal database")
    
    use_rdns = st.checkbox("Enable Reverse DNS", 
                           value=False,
                           help="Perform reverse DNS lookup for IPs")
    
    no_output = st.checkbox("Disable Auto-Save", value=False, help="To disable save output")
    
    st.markdown("---")
    
    # About section
    st.subheader("About")
    st.markdown("""
    **HolmesGeo** extracts and analyzes IP addresses from:
    - Apache log files
    - CSV files
    - Plain text (IP lists)
    - Direct text input
    
    **Output includes:**
    - IP Category
    - City
    - City Latitude
    - City Longitude
    - Country
    - Country Code
    - Continent
    - ASN Number
    - ASN Organization
    - Network
    - Reverse DNS
    - Certificate CN
    - Domain Registrar URL
    - User Agent
    """)
    
    st.markdown("---")
    # st.caption("Part of ArteMon")

# Main content area with tabs
tab1, tab2, tab3, tab4 = st.tabs(["Apache Logs", "CSV Files", "Text Input", "IP List File"])

def run_holmesgeo(input_type, input_data, filename=None, column_name=None):
    try:
        # Create temporary file if needed
        temp_file = None
        if input_type in ['apache', 'csv', 'check']:
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, 
                                                     suffix=f'.{input_type}')
            temp_file.write(input_data)
            temp_file.close()
            input_path = temp_file.name
        else:
            input_path = None
        
        # Build command
        cmd = ['python3', '-m', 'holmesMod.main']
        
        if input_type == 'apache':
            cmd.extend(['--apache', input_path])
        elif input_type == 'csv':
            cmd.extend(['--csv', input_path])
            if column_name:
                cmd.extend(['--column', column_name])
        elif input_type == 'check':
            cmd.extend(['--check', input_path])
        elif input_type == 'stdin':
            # For stdin, we'll pass data directly
            pass
        
        # Add optional flags
        if use_virustotal and vt_api_key:
            # Set environment variable for VT API key
            os.environ['VT_API_KEY'] = vt_api_key
            cmd.append('--virtot')
        
        if not use_rdns:
            cmd.append('--no-rdns')
            
        if no_output:
            cmd.append('--no-output')
            
        # Execute command
        if input_type == 'stdin':
            process = subprocess.Popen(
                ['python3', '-m', 'holmesMod.main'] + 
                (['--virtot'] if use_virustotal and vt_api_key else []) +
                (['--no-rdns'] if not use_rdns else []),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=input_data)
        else:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            stdout = process.stdout
            stderr = process.stderr
        
        # Clean up temp file
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        
        return stdout, stderr, process.returncode if input_type != 'stdin' else process.returncode
        
    except Exception as e:
        return None, str(e), 1

def display_results(stdout, stderr, returncode):
    if returncode != 0:
        st.error(f"Error running HolmesGeo:\n{stderr}")
        return None
    
    # removing ansii codes, khusus untuk stdin output soalnya ini -> Kita g mw whole terminal printed.
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    clean_stdout = ansi_escape.sub('', stdout)
    
    # Split into lines and filter for CSV data only
    lines = clean_stdout.split('\n')
    csv_lines = []
    header_found = False
    
    for line in lines:
        line = line.strip()
        # Skip empty lines
        if not line:
            continue
        # Skip the ASCII art and instruction lines
        if any(skip_pattern in line for skip_pattern in [
            '====', '|', '.----', 'ITSEC', 'ASIA', 'Please provide',
            'Usage Example:', 'python3 -m', './chk.sh', 'cat ', 'echo',
            '[STAGE-1]', '[!]', 'Processing completed'
        ]):
            continue
        
        # Check if this is the header line (starts with "IP Address")
        if line.startswith('IP Address'):
            header_found = True
            csv_lines.append(line)
        # After header is found, collect data lines (contains commas and looks like CSV)
        elif header_found and ',' in line and not line.startswith('['):
            csv_lines.append(line)
    
    if not csv_lines:
        st.warning("⚠️ No results found in the output.")
        # Show raw output for debugging
        with st.expander("Debug: Raw Console Output", expanded=False):
            st.code(stdout)
        return None
    
    # Display clean console output (CSV format only)
    with st.expander("Console Output (CSV Format)", expanded=True):
        st.code('\n'.join(csv_lines))
    
    # Try to parse as DataFrame
    try:
        # Join CSV lines and parse with proper quoting
        csv_content = '\n'.join(csv_lines)
        
        # Try multiple parsing strategies
        df = None
        parsing_errors = []
        
        # Strategy 1: Standard CSV parsing
        try:
            df = pd.read_csv(io.StringIO(csv_content))
        except Exception as e1:
            parsing_errors.append(f"Standard parsing: {str(e1)}")
            
            # Strategy 2: Skip bad lines (pandas >= 1.3.0)
            try:
                df = pd.read_csv(io.StringIO(csv_content), on_bad_lines='skip')
                st.warning("⚠️ Some lines were skipped due to formatting issues.")
            except Exception as e2:
                parsing_errors.append(f"Skip bad lines: {str(e2)}")
                
                # Strategy 3: Use Python engine with different separator handling
                try:
                    df = pd.read_csv(io.StringIO(csv_content), engine='python', on_bad_lines='skip')
                except Exception as e3:
                    parsing_errors.append(f"Python engine: {str(e3)}")
                    
                    # Strategy 4: Manual parsing line by line
                    try:
                        lines_data = []
                        header = None
                        for i, line in enumerate(csv_lines):
                            parts = line.split(',')
                            if i == 0:
                                header = parts
                                expected_cols = len(header)
                            else:
                                # If line has extra commas, try to handle it
                                if len(parts) > expected_cols:
                                    # Merge extra parts (likely from fields with commas)
                                    merged_parts = parts[:expected_cols-1] + [','.join(parts[expected_cols-1:])]
                                    lines_data.append(merged_parts)
                                elif len(parts) == expected_cols:
                                    lines_data.append(parts)
                                # Skip lines with too few columns
                        
                        if header and lines_data:
                            df = pd.DataFrame(lines_data, columns=header)
                            st.info("Data parsed with manual line processing.")
                    except Exception as e4:
                        parsing_errors.append(f"Manual parsing: {str(e4)}")
        
        if df is None:
            raise Exception("All parsing strategies failed:\n" + "\n".join(parsing_errors))
        
        st.success(f"✅ Analysis complete! Found {len(df)} IP addresses.")
        
        # Display dataframe
        st.subheader("Results Table")
        st.dataframe(df, use_container_width=True)
        
        # Download buttons
        col1, col2, col3 = st.columns(3)
        
        # Prepare CSV data
        csv_data = df.to_csv(index=False)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Prepare Excel data
        xlsx_data = None
        try:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='HolmesGeo Results')
            xlsx_data = output.getvalue()
        except Exception as e:
            st.error(f"Error creating Excel file: {str(e)}")
        
        with col1:
            # CSV download
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"holmesgeo_results_{timestamp}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            # Excel download
            if xlsx_data:
                st.download_button(
                    label="Download Excel",
                    data=xlsx_data,
                    file_name=f"holmesgeo_results_{timestamp}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            else:
                st.button("Download Excel", disabled=True, use_container_width=True)
        
        with col3:
            # Download both as ZIP
            if xlsx_data:
                import zipfile
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    # Add CSV
                    zip_file.writestr(f"holmesgeo_results_{timestamp}.csv", csv_data)
                    # Add Excel
                    zip_file.writestr(f"holmesgeo_results_{timestamp}.xlsx", xlsx_data)
                
                st.download_button(
                    label="Download Both (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name=f"holmesgeo_results_{timestamp}.zip",
                    mime="application/zip",
                    use_container_width=True
                )
            else:
                st.button("Download Both (ZIP)", disabled=True, use_container_width=True)
        
        # Display summary statistics
        st.subheader("Summary Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total IPs", len(df))
        
        with col2:
            unique_countries = df['Country'].nunique() if 'Country' in df.columns else 0
            st.metric("Unique Countries", unique_countries)
        
        with col3:
            unique_asn = df['ASN Organization'].nunique() if 'ASN Organization' in df.columns else 0
            st.metric("Unique ASNs", unique_asn)
        
        with col4:
            categorized = len(df[df['IP Category'] != 'N/A']) if 'IP Category' in df.columns else 0
            st.metric("Categorized IPs", categorized)
        
        # Show country distribution if available
        if 'Country' in df.columns:
            st.subheader("Country Distribution")
            country_counts = df['Country'].value_counts().head(10)
            st.bar_chart(country_counts, color="#F25912")
        
        return df
        
    except Exception as e:
        st.error(f"Error parsing results: {str(e)}")
        with st.expander("Debug: Parsed CSV Lines", expanded=False):
            st.code('\n'.join(csv_lines))
        return None

# Tab 1: Apache Logs
with tab1:
    st.header("Apache Log File Analysis")
    st.markdown("Upload an Apache log file to extract and analyze IP addresses.")
    
    apache_file = st.file_uploader("Upload Apache Log File", type=['log', 'txt'], key='apache')
    
    if apache_file is not None:
        st.info(f"File uploaded: {apache_file.name} ({apache_file.size} bytes)")
        
        # Preview
        with st.expander("Preview (first 20 lines)"):
            content = apache_file.getvalue().decode('utf-8')
            lines = content.split('\n')[:20]
            st.code('\n'.join(lines))
        
        if st.button("Analyze Apache Log", key='analyze_apache'):
            with st.spinner("Analyzing Apache log file..."):
                apache_file.seek(0)  # Reset file pointer
                content = apache_file.getvalue().decode('utf-8')
                stdout, stderr, returncode = run_holmesgeo('apache', content, apache_file.name)
                display_results(stdout, stderr, returncode)

# Tab 2: CSV Files
with tab2:
    st.header("CSV File Analysis")
    st.markdown("Upload a CSV file containing IP addresses.")
    
    csv_file = st.file_uploader("Upload CSV File", type=['csv'], key='csv')
    
    if csv_file is not None:
        st.info(f"File uploaded: {csv_file.name} ({csv_file.size} bytes)")
        
        # Read CSV to show columns
        try:
            df_preview = pd.read_csv(csv_file)
            csv_file.seek(0)  # Reset file pointer
            
            # Preview
            with st.expander("Preview (first 10 rows)"):
                st.dataframe(df_preview.head(10))
            
            # Column selection
            columns = df_preview.columns.tolist()
            
            if len(columns) > 1:
                st.subheader("Column Selection")
                col_option = st.radio(
                    "How would you like to process the CSV?",
                    ["Extract from all columns", "Extract from specific column"],
                    key='csv_option'
                )
                
                selected_column = None
                if col_option == "Extract from specific column":
                    selected_column = st.selectbox("Select the column containing IP addresses:", columns)
            else:
                selected_column = None
            
            if st.button("Analyze CSV", key='analyze_csv'):
                with st.spinner("Analyzing CSV file..."):
                    csv_file.seek(0)
                    content = csv_file.getvalue().decode('utf-8')
                    stdout, stderr, returncode = run_holmesgeo('csv', content, csv_file.name, selected_column)
                    display_results(stdout, stderr, returncode)
                    
        except Exception as e:
            st.error(f"Error reading CSV file: {str(e)}")

# Tab 3: Text Input
with tab3:
    st.header("Direct Text Input")
    st.markdown("Paste IP addresses directly (one per line or comma-separated).")
    
    text_input = st.text_area(
        "Enter IP addresses:",
        height=200,
        placeholder="8.8.8.8\n1.1.1.1\n192.168.1.1",
        key='text_input'
    )
    
    if st.button("Analyze IPs", key='analyze_text'):
        if text_input.strip():
            with st.spinner("Analyzing IP addresses..."):
                stdout, stderr, returncode = run_holmesgeo('stdin', text_input)
                display_results(stdout, stderr, returncode)
        else:
            st.warning("Please enter at least one IP address.")

# Tab 4: IP List File
with tab4:
    st.header("IP List File")
    st.markdown("Upload a text file with IP addresses (one per line).")
    
    ip_file = st.file_uploader("Upload IP List File", type=['txt'], key='iplist')
    
    if ip_file is not None:
        st.info(f"File uploaded: {ip_file.name} ({ip_file.size} bytes)")
        
        # Preview
        with st.expander("Preview (first 20 IPs)"):
            content = ip_file.getvalue().decode('utf-8')
            lines = content.split('\n')[:20]
            st.code('\n'.join(lines))
        
        if st.button("Analyze IP List", key='analyze_iplist'):
            with st.spinner("Analyzing IP list..."):
                ip_file.seek(0)
                content = ip_file.getvalue().decode('utf-8')
                stdout, stderr, returncode = run_holmesgeo('check', content, ip_file.name)
                display_results(stdout, stderr, returncode)

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p><strong>Part of ArteMon</strong></p>
    </div>
""", unsafe_allow_html=True)
