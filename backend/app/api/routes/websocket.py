import asyncio
import logging
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.job_store import job_store
from app.schemas import JobStatus, ProgressEvent

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time job progress streaming.
    Polls the job_store and sends ProgressEvent updates to the client.
    """
    await websocket.accept()
    logger.info(f"WebSocket connection accepted for job: {job_id}")

    try:
        # 1. Validate Job Existence
        job = job_store.get_job(job_id)
        if not job:
            await websocket.send_json({
                "job_id": job_id,
                "status": "error",
                "progress": 0,
                "message": f"Job {job_id} not found."
            })
            await websocket.close(code=1000)
            return

        # 2. Progress Streaming Loop
        last_progress = -1
        last_status = None
        
        while True:
            job = job_store.get_job(job_id)
            if not job:
                break

            # Send update only if status or progress changed
            if job.status != last_status or job.progress != last_progress:
                event = ProgressEvent(
                    job_id=job.job_id,
                    status=job.status,
                    progress=job.progress,
                    message=job.message,
                    timestamp=datetime.utcnow()
                )
                
                # Optional: Include first brain frame if job is completed
                if job.status == JobStatus.COMPLETED and job.result:
                    if job.result.brain_visualization and job.result.brain_visualization.frames:
                        event.brain_frame = job.result.brain_visualization.frames[0]

                await websocket.send_json(event.model_dump(mode="json"))
                
                last_status = job.status
                last_progress = job.progress

            # Terminate loop if job is finished
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                logger.info(f"Job {job_id} reached terminal state {job.status}. Closing WebSocket.")
                break

            # Poll every 100ms
            await asyncio.sleep(0.1)

        # Final wait to ensure client receives the last message before closing
        await asyncio.sleep(0.1)
        await websocket.close(code=1000)

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected for job: {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
        try:
            await websocket.send_json({"error": str(e)})
            await websocket.close(code=1011)
        except:
            pass
