import os
import logging
import yt_dlp
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class YouTubeDownloaderService:
    """
    Service for downloading YouTube videos using yt-dlp.
    """

    def download(self, url: str, job_id: str, output_dir: Optional[str] = None) -> str:
        """
        Downloads a YouTube video and returns the path to the downloaded file.
        Raises RuntimeError if download fails.
        """
        if output_dir is None:
            output_dir = settings.UPLOAD_DIR

        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # Output template: job_<id>_youtube.ext
        output_template = os.path.join(output_dir, f"job_{job_id}_youtube.%(ext)s")

        ydl_opts = {
            'format': 'mp4/best[ext=mp4]/best',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Starting YouTube download for job {job_id}: {url}")
                info = ydl.extract_info(url, download=True)
                
                # Construct the actual filename (yt-dlp might have added an extension)
                ext = info.get('ext', 'mp4')
                downloaded_path = os.path.join(output_dir, f"job_{job_id}_youtube.{ext}")
                
                if not os.path.exists(downloaded_path):
                    # Sometimes yt-dlp returns info but the file is named slightly differently
                    # or it's still processing. We'll do a quick check for the most likely name.
                    logger.warning(f"Expected file {downloaded_path} not found immediately after download.")
                
                return downloaded_path

        except Exception as e:
            logger.error(f"YouTube download failed for job {job_id}: {str(e)}")
            raise RuntimeError(f"Failed to download YouTube video: {str(e)}")

youtube_downloader_service = YouTubeDownloaderService()
