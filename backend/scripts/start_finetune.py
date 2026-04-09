import os
import json
from openai import OpenAI
from dotenv import load_dotenv

def main():
    # Load environment variables
    dotenv_path = os.path.join(os.path.dirname(__file__), '../../.env')
    load_dotenv(dotenv_path)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in .env")
        return
        
    client = OpenAI(api_key=api_key)
    file_path = os.path.join(os.path.dirname(__file__), '../data/llm_finetuning_dataset.jsonl')
    
    print("\n--- Starting Fine-Tuning Process ---")
    print("1. Uploading training data to OpenAI...")
    
    try:
        # Upload the file
        with open(file_path, "rb") as f:
            uploaded_file = client.files.create(
                file=f,
                purpose="fine-tune"
            )
        print(f"File uploaded successfully! File ID: {uploaded_file.id}")
        
    except Exception as e:
        print(f"\n❌ Error uploading file: {e}")
        return

    print("\n2. Triggering Fine-Tuning Job...")
    try:
        # Start the fine-tuning job
        job = client.fine_tuning.jobs.create(
            training_file=uploaded_file.id,
            model="gpt-3.5-turbo",
            suffix="talent-match-normalizer"
        )
        print(f"✅ Success! Fine-tuning job started.")
        print(f"Job ID: {job.id}")
        print(f"Status: {job.status}")
        print(f"You can monitor this job programmatically or the CTO can view it in the dashboard.")
        
    except Exception as e:
        print(f"\n❌ Error starting job: {e}")
        return

if __name__ == "__main__":
    main()
