# NeuroSafe 🧠⚡

*Built for ConHacks 2026.*

NeuroSafe is a web application that screens videos for epileptic seizure triggers before they reach an audience. Instead of relying on rigid frame-rate rules, we use Meta AI's state-of-the-art neuroscience foundation model to predict actual brain activity in real-time.

## The Problem
65 million people globally live with epilepsy, and nearly 2 million of those have photosensitive epilepsy. That means flashing lights or rapid visual patterns can literally send them to the hospital. Despite this, **no major content platform automatically screens for seizure-triggering content before publishing.** 

The current standard (WCAG 2.1) requires content to stay under 3 flashes per second, but compliance is manual, slow, and rarely enforced. Existing tools are expensive, proprietary, and only measure pixel-level flicker—they tell you nothing about what is actually happening in the human brain.

## What It Does
NeuroSafe changes that. Anyone can upload a video file or paste a YouTube URL and receive a timestamped seizure risk report in under a minute. 

Our app runs the video through our pipeline and identifies exactly which moments are dangerous, which specific regions of the visual cortex are overstimulated, and what to do about it. The output is:
- A timestamped danger report with a severity score.
- An animated 3D brain visualization showing cortical spikes in real time.
- A **Gemini-generated**, plain-English clinical summary that any content creator, platform, or medical professional can act on instantly.

## How We Built It
NeuroSafe is powered by some seriously heavy-lifting tech:
- **Brain Model:** We built on top of **TRIBE v2** (`facebook/tribev2`), Meta AI's foundation model trained on fMRI data from over 700 healthy volunteers. It returns predicted cortical activation across 20,480 vertices for any video input.
- **ROI Mapping & Scoring:** We use custom Python algorithms to isolate the visual cortex ROIs (V1, V2, V3, V4, and MT+) and calculate an activation rate-of-change to flag dangerous spikes.
- **Backend:** A **FastAPI** server orchestrates the inference worker, video ingestion (via FFmpeg and yt-dlp), and streams the results to the frontend via WebSockets.
- **Frontend:** Built with **React** and **TypeScript**, featuring a synchronized HTML5 video player, a **D3.js** activation waveform timeline, and a live 3D brain visualization.
- **AI Report:** We leverage **Gemini 1.5 Flash** to translate complex neural tensor data into a simple, actionable safety summary.
- **Deployment:** Hosted on a **DigitalOcean Droplet**.

## Challenges We Ran Into
Working with in-silico neuroscience models at a hackathon is no joke! Handling the sheer volume of data—a continuous tensor stream of 20,480 brain vertices per second of video—required us to heavily optimize our memory usage and WebSocket streaming. We also had to account for hemodynamic lag (the ~5-second delay between neural activity and blood-oxygen BOLD signals in fMRI data) to ensure our timeline synced perfectly with the video frames.

## What's Next for NeuroSafe
We believe this tool shouldn't just be a hackathon project; it should be a web standard. 
- **Platform Integrations:** We want to build an open API for platforms like YouTube, TikTok, and Twitch to auto-screen content during the upload process.
- **Browser Extension:** A real-time extension that preemptively blocks or dims dangerous video segments before they auto-play on social feeds.
- **Clinical Partnerships:** Partnering with hospitals to further refine our danger scoring algorithms against real-world seizure-triggering stimuli.

---
*NeuroSafe is an accessibility tool designed for creators and is not intended for medical diagnosis.*
