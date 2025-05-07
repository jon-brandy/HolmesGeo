import os
import sys
from datetime import datetime

def get_output_path(input_source=None):
    from .config import RESULTS_DIR
    
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    if input_source is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(RESULTS_DIR, f"stdin_{timestamp}.csv")
    
    base_filename = os.path.basename(input_source)
    filename_without_ext = os.path.splitext(base_filename)[0]
    return os.path.join(RESULTS_DIR, f"{filename_without_ext}_ipinfo.csv")

def suppress_stdout():
    class NullWriter:
        def write(self, text):
            pass
        def flush(self):
            pass
    
    old_stdout = sys.stdout
    sys.stdout = NullWriter()
    
    try:
        yield
    finally:
        sys.stdout = old_stdout