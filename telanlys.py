# telecom_analyzer.py
import pandas as pd
import re
from tqdm import tqdm
import os

# ========================
# CONFIGURATION (DEFAULTS)
# ========================
DEFAULT_TRAFFIC_FILE = "traffic_data.xlsx"
DEFAULT_TAGS_FILE = "Tags.xlsx"
OUTPUT_FILE = "testing_numbers_analysis.xlsx"
MIN_OCCURRENCES = 3

# ========================
# VALIDATION FUNCTIONS
# ========================
def validate_traffic_file(df):
    """Check for required columns in traffic data"""
    required = ["Client Name", "Destination Number", "Content", "Sender ID"]
    missing = [col for col in required if col not in df.columns]
    return missing

def validate_tags_file(df):
    """Verify Tags file structure"""
    return "Tag values" not in df.columns

# ========================
# ANALYSIS FUNCTIONS
# ========================
def analyze_messages(messages):
    """Identify template patterns with numeric identifiers"""
    patterns = []
    identifiers = []
    
    for msg in messages:
        numbers = re.findall(r'\d+', msg)
        if not numbers:
            return None
        
        identifier = max(numbers, key=lambda x: len(x))
        identifiers.append(identifier)
        pattern = re.sub(re.escape(identifier), '<ID>', msg)
        patterns.append(pattern.strip())
    
    return {'pattern': patterns[0], 'identifiers': identifiers} if len(set(patterns)) == 1 else None

def get_identifier_type(identifiers):
    """Classify identifier formats and lengths"""
    formats = set()
    for id in identifiers:
        if id.isdigit():
            formats.add(f"{len(id)}-digit numeric")
        elif id.isalnum():
            formats.add(f"{len(id)}-digit alphanumeric")
        else:
            formats.add("mixed formats")
    return " | ".join(sorted(formats))

# ========================
# MAIN PROCESSING FLOW
# ========================
def main(traffic_file=DEFAULT_TRAFFIC_FILE, tags_file=DEFAULT_TAGS_FILE):
    try:
        # Load and validate files
        traffic_df = pd.read_excel(traffic_file)
        tags_df = pd.read_excel(tags_file)
        
        # Perform validation
        missing_traffic = validate_traffic_file(traffic_df)
        missing_tags = validate_tags_file(tags_df)
        
        if missing_traffic or missing_tags:
            error_msg = []
            if missing_traffic:
                error_msg.append(f"Missing columns in traffic file: {', '.join(missing_traffic)}")
            if missing_tags:
                error_msg.append("Tags file missing 'Tag values' column")
            raise ValueError("\n".join(error_msg))
            
        # Rest of processing remains unchanged
        known_numbers = set(tags_df["Tag values"].astype(str).str.strip().str.lower())

        value_counts = traffic_df["Destination Number"].astype(str).str.lower().value_counts()
        candidates = value_counts[value_counts >= MIN_OCCURRENCES].index.tolist()
        candidates = [num for num in candidates if num not in known_numbers]

        detailed_results = []
        for number in tqdm(candidates, desc="Processing numbers"):
            records = traffic_df[traffic_df["Destination Number"].astype(str).str.lower() == number]
            messages = records["Content"].astype(str).tolist()
            
            pattern_data = analyze_messages(messages)
            if pattern_data and len(pattern_data['identifiers']) == len(messages):
                for idx, (_, row) in enumerate(records.iterrows()):
                    detailed_results.append({
                        "Client Name": row["Client Name"],
                        "Destination Number": row["Destination Number"],
                        "Content": row["Content"],
                        "Sender ID": row["Sender ID"],
                        "Occurrence Count": len(records),
                        "Message Pattern": pattern_data['pattern'],
                        "Identifier": pattern_data['identifiers'][idx]
                    })

        if not detailed_results:
            print("No testing patterns found")
            return

        detailed_df = pd.DataFrame(detailed_results)
        
        # Generate summary report
        summary_df = detailed_df.groupby('Destination Number').agg(
            Total_Occurrences=('Occurrence Count', 'max'),
            Unique_Clients=('Client Name', 'nunique'),
            Clients=('Client Name', lambda x: ', '.join(sorted(set(x)))),
            Sender_IDs=('Sender ID', lambda x: ', '.join(sorted(set(x)))),
            Message_Patterns=('Message Pattern', lambda x: '; '.join(sorted(set(x)))),
            Identifier_Format=('Identifier', lambda x: get_identifier_type(x))
        ).reset_index()

        # Save outputs
        with pd.ExcelWriter(OUTPUT_FILE) as writer:
            detailed_df.to_excel(writer, sheet_name='Detailed', index=False)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)

        print(f"Analysis complete. Results saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()