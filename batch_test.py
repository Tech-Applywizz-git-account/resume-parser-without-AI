import os
import json
import time
import sys

# Ensure UTF-8 output even on Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

from parser import ResumeParser, extract_text_from_file

PUBLIC_DIR = "public"
RESULTS_FILE = "batch_test_results.json"

def run_batch_test():
    if not os.path.exists(PUBLIC_DIR):
        print(f"Error: {PUBLIC_DIR} directory not found.")
        return

    files = [f for f in os.listdir(PUBLIC_DIR) if f.lower().endswith(('.pdf', '.docx'))]
    print(f"Starting Batch Test on {len(files)} resumes...")
    print("-" * 50)
    
    results = []
    success_count = 0
    start_time = time.time()

    for idx, filename in enumerate(files):
        file_path = os.path.join(PUBLIC_DIR, filename)
        # Use simple print without emojis for terminal safety
        print(f"[{idx+1}/{len(files)}] Processing: {filename}...")
        
        try:
            # 1. Extract
            text, links = extract_text_from_file(file_path)
            
            # 2. Parse
            parser = ResumeParser(text, links=links)
            data = parser.parse()
            
            # 3. Store metadata for report
            results.append({
                "filename": filename,
                "status": "success",
                "parsed_data": data
            })
            success_count += 1
            name = f"{data['first_name']} {data['last_name']}"
            print(f"   Done: {name} ({data['predicted_job_title']})")
            
        except Exception as e:
            print(f"   Failed: {str(e)}")
            results.append({
                "filename": filename,
                "status": "error",
                "error": str(e)
            })

    # Save detailed results
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    end_time = time.time()
    print("-" * 50)
    print(f"BATCH TEST COMPLETE")
    print(f"Successful: {success_count}/{len(files)}")
    print(f"Total Time: {end_time - start_time:.2f}s")
    print(f"Results saved to: {RESULTS_FILE}")

if __name__ == "__main__":
    run_batch_test()
