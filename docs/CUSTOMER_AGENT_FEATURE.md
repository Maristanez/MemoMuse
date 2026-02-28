# Customer Agent Feature (Voicemail Copilot)

**MemoMuse** includes an AI-powered **Customer Agent** experience called **Voicemail Copilot**: a support inbox that analyzes customer voicemails for Shopify-like online stores and suggests replies (with optional voice generation).

---

## Overview

- **Purpose**: Help support teams handle voicemails by transcribing them, classifying intent/sentiment/urgency, summarizing the message, and suggesting a reply. Users can optionally generate a voice reply (TTS) to call the customer back.
- **Audience**: Shopify-style brands that receive customer support voicemails (orders, returns, questions, complaints).
- **Entry point**: Navigate to **Voicemail Copilot** from the main app nav, or go to `/voicemail`.

---

## User Flow

1. **Open Voicemail Copilot**  
   Visit `/voicemail` (or click “Voicemail Copilot” in the nav). The app shows a sidebar and an empty state.

2. **Add a voicemail**  
   - **Upload**: Drag-and-drop or click to upload an audio file (MP3, WAV, M4A, OGG, WebM, etc.).  
   - **Demo**: Use one of the demo examples (e.g. “Angry Customer — Late Order”, “Return Request”, “Shipping Question”) to see pre-filled analysis without calling the API.

3. **Analyze**  
   With a file selected, click **Analyze Voicemail**. The backend sends the audio to Gemini and returns structured JSON (transcript, intent, sentiment, urgency, summary, suggested reply). A new “ticket” appears in the inbox.

4. **Review ticket**  
   Click a ticket to see:
   - Summary and classification chips (intent, sentiment, urgency)
   - Original voicemail playback (if from upload)
   - Full transcript (expand/collapse)
   - Suggested reply in an editable textarea

5. **Edit reply & generate voice (optional)**  
   Edit the suggested reply, then click **Generate Voice Reply**. The app calls the TTS API and attaches an MP3 to the ticket. Users can play the AI voice reply (e.g. for callbacks).

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/voicemail` | Serves the Voicemail Copilot SPA (`static/voicemail.html`). |
| `POST` | `/api/voicemail/analyze` | Analyzes an uploaded voicemail audio file. **Body**: `multipart/form-data` with `file` (audio). **Returns**: JSON with `transcript`, `intent`, `sentiment`, `urgency`, `summary`, `suggestedReply`. |
| `POST` | `/api/voicemail/tts` | Generates speech from reply text. **Body**: `application/json` with `{ "text": "…" }`. **Returns**: Raw MP3 bytes. |

---

## Analysis Output (Structured JSON)

The **analyze** endpoint returns exactly these fields (enforced by the Gemini system prompt):

| Field | Type | Description |
|-------|------|-------------|
| `transcript` | string | Full text of the voicemail. |
| `intent` | enum | One of: `ORDER_STATUS`, `RETURN`, `GENERAL_QUESTION`, `COMPLAINT`, `OTHER`. |
| `sentiment` | enum | One of: `POSITIVE`, `NEUTRAL`, `NEGATIVE`. |
| `urgency` | enum | One of: `LOW`, `MEDIUM`, `HIGH`. |
| `summary` | string | Short summary of the message. |
| `suggestedReply` | string | AI-suggested reply text for the support agent. |

The backend strips markdown/code fences from the model output and parses the result as JSON before returning.

---

## Backend Implementation

- **Analyze** (`main.py`): Uses **Google Gemini** (`genai.Client`, model `gemini-2.5-flash`) with a system prompt that defines the JSON schema and allowed enum values. Audio is sent as a `Part.from_bytes(..., mime_type=...)`; supported MIME types include `audio/mpeg`, `audio/wav`, `audio/ogg`, `audio/webm`, `audio/mp4`, `audio/x-m4a` (others fall back to `audio/mpeg`).
- **TTS** (`main.py`): Uses **ElevenLabs** (`elevenlabs` Python SDK). Voice ID comes from `ELEVENLABS_VOICE_ID` (default `21m00Tcm4TlvDq8ikWAM`). Model: `eleven_multilingual_v2`. Response is streamed and concatenated into a single MP3 response.

---

## Frontend (Voicemail Copilot)

- **File**: `static/voicemail.html` (single-page app, no framework).
- **State**: In-memory only: `tickets[]`, `selectedId`, `selectedFile`, `audioPreviewUrl`, `isAnalyzing`, `analyzeError`, `transcriptExpanded`, `currentReplyText`, `isGeneratingTTS`, `ttsError`.
- **UI**:
  - **Sidebar**: Logo, “Upload Voicemail” zone, file preview/audio, Analyze button, Demo examples, ticket count.
  - **Ticket list**: Cards with summary, urgency badge, intent label, relative time; left bar color by sentiment.
  - **Detail panel**: Summary, intent/sentiment/urgency chips, original audio, transcript (collapsible), suggested reply textarea, “Generate Voice Reply” button, and optional AI voice reply player.
- **Demo data**: Three built-in examples (late order, return request, shipping question) with pre-filled analysis so the feature can be tried without API keys.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes (for analyze) | Google AI Studio key for Gemini. |
| `ELEVENLABS_API_KEY` | Yes (for TTS) | ElevenLabs API key. |
| `ELEVENLABS_VOICE_ID` | No | Voice ID for TTS (default: `21m00Tcm4TlvDq8ikWAM`). |

---

## Summary

The **Customer Agent** feature is the **Voicemail Copilot**: upload or demo voicemails → analyze with Gemini (transcript + intent/sentiment/urgency + summary + suggested reply) → review in a ticket inbox → edit reply and optionally generate a voice reply with ElevenLabs. It is designed for Shopify-style stores and lives alongside the main MemoMuse music-generation pipeline.
