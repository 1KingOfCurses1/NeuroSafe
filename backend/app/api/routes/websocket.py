from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

@router.websocket("/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await websocket.accept()
    try:
        await websocket.send_json({
            "job_id": job_id,
            "status": "scaffolded",
            "progress": 0,
            "message": "WebSocket scaffold ready. Real progress streaming will be implemented later."
        })
        # Keep connection open briefly or close immediately as per scaffold req
        await websocket.close()
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        pass
