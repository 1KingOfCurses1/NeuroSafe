"""Test script: submit flash video + calm video, compare danger scores."""
import requests, time, sys

API = "http://127.0.0.1:8000"

# --- Test 1: Epilepsy flash video (SHOULD be dangerous) ---
print("=" * 60)
print("TEST 1: Epilepsy flash video (pDEdiyU1i70)")
print("=" * 60)
r1 = requests.post(f"{API}/api/analyze/youtube", json={"url": "https://www.youtube.com/watch?v=pDEdiyU1i70"})
job1 = r1.json()["job_id"]
print(f"Job ID: {job1}")

# --- Test 2: Calm nature video (SHOULD be safe) ---
print()
print("=" * 60)
print("TEST 2: Calm video (Lo-fi hip hop radio)")
print("=" * 60)
r2 = requests.post(f"{API}/api/analyze/youtube", json={"url": "https://www.youtube.com/watch?v=jfKfPfyJRdk"})
job2 = r2.json()["job_id"]
print(f"Job ID: {job2}")

# --- Poll both jobs ---
for attempt in range(60):
    time.sleep(2)
    s1 = requests.get(f"{API}/api/analyze/{job1}").json()
    s2 = requests.get(f"{API}/api/analyze/{job2}").json()
    
    done1 = s1["status"] in ("completed", "failed")
    done2 = s2["status"] in ("completed", "failed")
    
    print(f"  [{attempt*2}s] Job1={s1['status']}({s1.get('progress',0)}%) | Job2={s2['status']}({s2.get('progress',0)}%)")
    
    if done1 and done2:
        break

# --- Print results ---
print()
print("=" * 60)
print("RESULTS")
print("=" * 60)

for label, job_id in [("FLASH VIDEO", job1), ("CALM VIDEO", job2)]:
    res = requests.get(f"{API}/api/analyze/{job_id}").json()
    if res["status"] == "completed" and res.get("result"):
        r = res["result"]
        print(f"\n  {label}:")
        print(f"    Danger Score : {r['danger_score']}")
        print(f"    Severity     : {r['summary']['severity']}")
        print(f"    Segments     : {r['summary']['segments_detected']}")
        print(f"    Duration     : {r['video']['duration_seconds']}s")
        print(f"    Resolution   : {r['video']['resolution']}")
        brain_frames = len([f for f in r.get("brain_visualization", {}).get("frames", []) if f.get("image_b64")])
        print(f"    Brain Frames : {brain_frames}")
    else:
        print(f"\n  {label}: {res['status']} — {res.get('error', 'unknown')}")

print()
