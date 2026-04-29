import asyncio
import websockets
import sys
import json

async def test_websocket(job_id):
    uri = f"ws://localhost:8000/ws/analyze/{job_id}"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected! Waiting for messages...")
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    print(f"\n[EVENT] Status: {data.get('status')}, Progress: {data.get('progress')}%")
                    print(f"Message: {data.get('message')}")
                    
                    if data.get("status") in ["completed", "failed"]:
                        print(f"\nJob finished with status: {data.get('status')}")
                        break
                except websockets.exceptions.ConnectionClosed:
                    print("\nConnection closed by server.")
                    break
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_ws.py <job_id>")
        sys.exit(1)
    
    target_job_id = sys.argv[1]
    asyncio.run(test_websocket(target_job_id))
