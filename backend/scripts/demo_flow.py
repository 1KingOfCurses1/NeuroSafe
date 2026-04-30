import urllib.request
import urllib.parse
import json
import time
import sys
import os

BASE_URL = "http://localhost:8001"

def submit_youtube(url):
    print(f"\n[1/3] Submitting YouTube URL: {url}")
    data = json.dumps({"url": url}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/analyze/youtube",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode("utf-8"))
        job_id = res["job_id"]
        print(f"Job created: {job_id}")
        return job_id

def submit_upload(filename):
    print(f"\n[1/3] Submitting Upload: {filename}")
    
    # Create a small dummy file if it doesn't exist
    if not os.path.exists(filename):
        with open(filename, "wb") as f:
            f.write(b"fake mp4 content for demo")
            
    # Simple multipart form-data manual construction
    boundary = "----NeuroSafeBoundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(filename)}"\r\n'
        "Content-Type: video/mp4\r\n\r\n"
        "fake mp4 content for demo\r\n"
        f"--{boundary}--\r\n"
    ).encode("utf-8")

    req = urllib.request.Request(
        f"{BASE_URL}/api/analyze/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode("utf-8"))
        job_id = res["job_id"]
        print(f"Job created: {job_id}")
        return job_id

def poll_job(job_id):
    print(f"\n[2/3] Polling Job Status: {job_id}")
    while True:
        with urllib.request.urlopen(f"{BASE_URL}/api/analyze/{job_id}") as response:
            job = json.loads(response.read().decode("utf-8"))
            status = job["status"]
            progress = job["progress"]
            message = job["message"]
            
            print(f"[{status.upper()}] {progress}% - {message}")
            
            if status in ["completed", "failed"]:
                return job
            
            time.sleep(1.0)

def print_result(job):
    print("\n[3/3] Analysis Result Summary")
    print("-" * 30)
    result = job.get("result")
    if not result:
        print(f"Error: {job.get('error', 'No result data found')}")
        return

    print(f"Job ID:      {result['job_id']}")
    print(f"Status:      {result['status']}")
    print(f"Danger Score: {result['danger_score']}/100")
    print(f"Severity:    {result['summary']['severity'].upper()}")
    print(f"Segments:    {result['summary']['segments_detected']}")
    
    if result['danger_segments']:
        seg = result['danger_segments'][0]
        print(f"First Danger: {seg['roi']} at {seg['start_time']}s (Peak: {seg['activation_level']})")
        
    if result['brain_visualization']['frames']:
        frame = result['brain_visualization']['frames'][0]
        print(f"First Frame: {frame['timestamp']}s (Max Activation: {frame['max_activation']})")
        
    print(f"Report:      {result['gemini_report']['headline']}")
    print("-" * 30)

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "youtube"
    
    try:
        if mode == "youtube":
            url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            job_id = submit_youtube(url)
        elif mode == "upload":
            job_id = submit_upload("demo_test.mp4")
        else:
            print("Usage: python scripts/demo_flow.py [youtube|upload]")
            return

        final_job = poll_job(job_id)
        print_result(final_job)
        
    except Exception as e:
        print(f"\nError during demo flow: {e}")

if __name__ == "__main__":
    main()
