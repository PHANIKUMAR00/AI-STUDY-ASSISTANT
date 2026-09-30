
import io
import os
import re
import tempfile
from typing import Any

import requests
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from pypdf import PdfReader
from gtts import gTTS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

load_dotenv()

APP_NAME = "My Personal Chatbot"
OLLAMA_URL = os.getenv(
    "OLLAMA_BASE_URL", "http://localhost:11434"
).rstrip("/")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "ollama").lower()

st.set_page_config(
    page_title=APP_NAME,
    page_icon="📚",
    layout="wide"
)

# --------------------------------------------------
# 1. DYNAMIC MODEL DISCOVERY
# --------------------------------------------------

def discover_ollama_models() -> list[str]:
    """Discover models installed in the local Ollama server."""
    try:
        response = requests.get(
            f"{OLLAMA_URL}/api/tags", timeout=5
        )
        response.raise_for_status()
        models = response.json().get("models", [])
        return [
            item["name"]
            for item in models
            if item.get("name")
        ]
    except (requests.RequestException, ValueError, KeyError):
        return []


def discover_groq_models() -> list[str]:
    """Discover models available through the Groq API."""
    if not GROQ_API_KEY:
        return []

    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.models.list()
        return sorted(
            item.id
            for item in response.data
            if getattr(item, "id", None)
        )
    except Exception:
        return []


# --------------------------------------------------
# 2. LLM INTEGRATION
# --------------------------------------------------

def generate_response(
    provider: str,
    model: str,
    messages: list[dict[str, str]]
) -> str:
    """Use the compatible chat-generation endpoint."""

    if provider == "ollama":
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
            },
            timeout=180,
        )
        response.raise_for_status()
        answer = response.json().get(
            "message", {}
        ).get("content", "")

    elif provider == "groq":
        if not GROQ_API_KEY:
            raise RuntimeError(
                "Add GROQ_API_KEY to your .env file."
            )

        client = Groq(api_key=GROQ_API_KEY)
        result = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
        )
        answer = result.choices[0].message.content or ""

    else:
        raise ValueError("Unsupported LLM provider.")

    answer = answer.strip()
    if not answer:
        raise RuntimeError("The model returned an empty response.")

    return answer


# --------------------------------------------------
# 3. PDF EXTRACTION
# --------------------------------------------------

def extract_pdf_pages(files) -> list[dict[str, Any]]:
    """Extract text from every uploaded PDF page."""
    extracted_pages = []

    for uploaded_file in files or []:
        try:
            reader = PdfReader(
                io.BytesIO(uploaded_file.getvalue())
            )

            for page_number, page in enumerate(
                reader.pages, start=1
            ):
                text = (page.extract_text() or "").strip()

                if text:
                    extracted_pages.append({
                        "source": uploaded_file.name,
                        "page": page_number,
                        "text": re.sub(r"\s+", " ", text),
                    })

        except Exception as exc:
            st.warning(
                f"Could not read {uploaded_file.name}: {exc}"
            )

    return extracted_pages


# --------------------------------------------------
# 4. DOCUMENT CHUNKING AND RETRIEVAL
# --------------------------------------------------

def create_chunks(
    pages: list[dict[str, Any]],
    chunk_size: int = 1200,
    overlap: int = 180
) -> list[dict[str, Any]]:
    """Split extracted pages into overlapping text chunks."""
    chunks = []

    for page in pages:
        text = page["text"]
        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))
            content = text[start:end].strip()

            if content:
                chunks.append({
                    "source": page["source"],
                    "page": page["page"],
                    "text": content,
                })

            if end >= len(text):
                break

            start = max(start + 1, end - overlap)

    return chunks


def retrieve_relevant_chunks(
    question: str,
    chunks: list[dict[str, Any]],
    top_k: int = 5
) -> list[dict[str, Any]]:
    """Find document chunks related to the user's question."""
    if not chunks:
        return []

    documents = [chunk["text"] for chunk in chunks]

    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2)
        )
        matrix = vectorizer.fit_transform(
            documents + [question]
        )
        scores = cosine_similarity(
            matrix[-1], matrix[:-1]
        ).ravel()

        indices = scores.argsort()[::-1][:top_k]

        return [
            chunks[index]
            for index in indices
            if scores[index] > 0
        ]

    except ValueError:
        return []


def format_document_context(
    chunks: list[dict[str, Any]]
) -> str:
    return "\n\n".join(
        f"[Source: {chunk['source']}, "
        f"page {chunk['page']}]\n{chunk['text']}"
        for chunk in chunks
    )


# --------------------------------------------------
# 5. SPEECH-TO-TEXT
# --------------------------------------------------

def transcribe_audio(
    audio_bytes: bytes,
    provider: str
) -> str:
    """Use Groq Whisper or local faster-whisper."""
    if provider == "groq":
        if not GROQ_API_KEY:
            raise RuntimeError(
                "Groq STT requires GROQ_API_KEY in .env."
            )

        client = Groq(api_key=GROQ_API_KEY)
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "recording.wav"

        result = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3-turbo",
            response_format="text",
        )
        return str(result).strip()

    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "Install local transcription with: "
            "pip install faster-whisper"
        ) from exc

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False
        ) as temporary_file:
            temporary_file.write(audio_bytes)
            temporary_path = temporary_file.name

        whisper_model = WhisperModel(
            "base",
            device="cpu",
            compute_type="int8"
        )
        segments, _ = whisper_model.transcribe(
            temporary_path
        )

        return " ".join(
            segment.text.strip()
            for segment in segments
        ).strip()

    finally:
        if (
            temporary_path
            and os.path.exists(temporary_path)
        ):
            os.remove(temporary_path)


# --------------------------------------------------
# 6. TEXT-TO-SPEECH
# --------------------------------------------------

def text_to_speech(
    text: str,
    language: str = "en"
) -> bytes:
    """Convert assistant text to MP3 audio."""
    audio_buffer = io.BytesIO()

    speech = gTTS(
        text=text[:4500],
        lang=language
    )
    speech.write_to_fp(audio_buffer)

    return audio_buffer.getvalue()


# --------------------------------------------------
# 7. STREAMLIT INTERFACE
# --------------------------------------------------

st.title("📚 My Personal Chatbot")
st.caption(
    "Your personal AI study assistant for PDFs, "
    "exam preparation, and voice conversations."
)

with st.sidebar:
    st.header("⚙️ Settings")

    provider_options = ["ollama", "groq"]
    default_provider = (
        DEFAULT_PROVIDER
        if DEFAULT_PROVIDER in provider_options
        else "ollama"
    )

    provider = st.selectbox(
        "LLM provider",
        provider_options,
        index=provider_options.index(default_provider),
        format_func=lambda value: (
            "Ollama + Gemma (local)"
            if value == "ollama"
            else "Groq API"
        )
    )

    available_models = (
        discover_ollama_models()
        if provider == "ollama"
        else discover_groq_models()
    )

    if available_models:
        if provider == "ollama":
            preferred_index = next(
                (
                    i for i, name in enumerate(available_models)
                    if "gemma3:1b" in name.lower()
                ),
                None
            )

            if preferred_index is None:
                preferred_index = next(
                    (
                        i for i, name in enumerate(available_models)
                        if "gemma" in name.lower()
                    ),
                    0
                )
        else:
            preferred_index = 0

        model = st.selectbox(
            "Available models",
            available_models,
            index=preferred_index
        )

    else:
        fallback_model = (
            "gemma3:1b"
            if provider == "ollama"
            else "llama-3.3-70b-versatile"
        )

        model = st.text_input(
            "Model name",
            value=fallback_model
        )

        if provider == "ollama":
            st.info(
                "No models discovered. Start Ollama and "
                "install a model."
            )
        elif not GROQ_API_KEY:
            st.warning(
                "Configure GROQ_API_KEY in your .env file."
            )

    difficulty = st.selectbox(
        "Explanation difficulty",
        ["Beginner", "Intermediate", "Advanced"]
    )

    voice_language = st.selectbox(
        "TTS language",
        ["en", "hi", "es", "fr", "de", "it", "pt"]
    )

    speak_answers = st.checkbox(
        "Speak assistant answers",
        value=False
    )

    if st.button("Clear conversation"):
        st.session_state.chat_history = []
        st.rerun()


# --------------------------------------------------
# 8. MULTIPLE PDF UPLOADS
# --------------------------------------------------

st.subheader("📄 Upload study materials")

uploaded_files = st.file_uploader(
    "Choose one or more PDF files",
    type=["pdf"],
    accept_multiple_files=True
)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_study_output" not in st.session_state:
    st.session_state.last_study_output = ""

if uploaded_files:
    signature = tuple(
        (file.name, len(file.getvalue()))
        for file in uploaded_files
    )

    if st.session_state.get("pdf_signature") != signature:
        with st.spinner("Extracting PDF text..."):
            pages = extract_pdf_pages(uploaded_files)
            chunks = create_chunks(pages)

            st.session_state.pdf_pages = pages
            st.session_state.pdf_chunks = chunks
            st.session_state.pdf_signature = signature

    pages = st.session_state.get("pdf_pages", [])
    chunks = st.session_state.get("pdf_chunks", [])

    st.success(
        f"Loaded {len(uploaded_files)} PDF(s), "
        f"extracted {len(pages)} text pages."
    )

    if not pages:
        st.warning(
            "No selectable text found. Scanned PDFs may "
            "need OCR before uploading."
        )

    with st.expander("Preview extracted text"):
        if pages:
            st.caption(
                f"{pages[0]['source']} — page {pages[0]['page']}"
            )
            st.write(pages[0]["text"][:1800])

else:
    pages = []
    chunks = []
    st.session_state.pdf_pages = []
    st.session_state.pdf_chunks = []
    st.session_state.pdf_signature = None


# --------------------------------------------------
# 9. PDF SUMMARIZATION AND EXAM TOOLS
# --------------------------------------------------

st.subheader("📝 Study tools")

col1, col2, col3, col4 = st.columns(4)

summarize_clicked = col1.button(
    "Summarize PDFs",
    disabled=not pages,
    use_container_width=True
)
mcq_clicked = col2.button(
    "Generate MCQs",
    disabled=not chunks,
    use_container_width=True
)
flashcards_clicked = col3.button(
    "Generate flashcards",
    disabled=not chunks,
    use_container_width=True
)
exam_clicked = col4.button(
    "Important questions",
    disabled=not chunks,
    use_container_width=True
)

task = None
material = ""

if summarize_clicked:
    material = "\n\n".join(
        f"[{page['source']}, page {page['page']}]\n"
        f"{page['text']}"
        for page in pages
    )[:24000]

    task = (
        "Create a structured study summary with headings, "
        "definitions, key concepts, and revision points."
    )

elif any([
    mcq_clicked,
    flashcards_clicked,
    exam_clicked
]):
    material = format_document_context(
        chunks[:12]
    )[:18000]

    if mcq_clicked:
        task = (
            "Generate 10 MCQs, each with four options, "
            "the correct answer, and a short explanation."
        )

    elif flashcards_clicked:
        task = (
            "Create 10 flashcards in Question and Answer format."
        )

    else:
        task = (
            "Generate important short-answer and long-answer "
            "exam questions with brief answer outlines."
        )

if task:
    study_prompt = (
        f"Task: {task}\n"
        f"Difficulty: {difficulty}\n"
        "Use the supplied study material as the primary source. "
        "Do not invent facts. Include source and page references "
        "where possible.\n\n"
        f"Study material:\n{material}"
    )

    with st.spinner("Generating study material..."):
        try:
            output = generate_response(
                provider,
                model,
                [
                    {
                        "role": "system",
                        "content": (
                            f"You are {APP_NAME}, a careful study tutor."
                        )
                    },
                    {
                        "role": "user",
                        "content": study_prompt
                    }
                ]
            )

            st.markdown(output)
            st.session_state.last_study_output = output

        except Exception as exc:
            st.error(
                f"Could not generate study material: {exc}"
            )

if st.session_state.last_study_output:
    if st.button("🔊 Listen to study output"):
        try:
            audio = text_to_speech(
                st.session_state.last_study_output,
                voice_language
            )
            st.audio(audio, format="audio/mp3")
        except Exception as exc:
            st.error(f"TTS error: {exc}")


# --------------------------------------------------
# 10. CHAT HISTORY AND VOICE INPUT
# --------------------------------------------------

st.divider()
st.subheader("💬 Chat with My Personal Chatbot")
st.caption(
    "Ask questions about your PDFs or other subjects. "
    "Type exit, quit, or bye to end the session."
)

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message.get("sources"):
            st.caption(
                "PDF sources: " + "; ".join(message["sources"])
            )

audio_recording = st.audio_input(
    "Optional: record a voice question"
)

if audio_recording is not None:
    if st.button("Transcribe voice recording"):
        try:
            with st.spinner("Transcribing audio..."):
                transcript = transcribe_audio(
                    audio_recording.getvalue(),
                    provider
                )

            st.session_state.transcribed_text = transcript
            st.session_state.transcript_edit = transcript

        except Exception as exc:
            st.error(f"STT error: {exc}")

if st.session_state.get("transcribed_text"):
    st.text_area(
        "Recognized speech (edit if needed)",
        key="transcript_edit"
    )

    if st.button("Send recognized text"):
        st.session_state.pending_question = (
            st.session_state.get("transcript_edit", "")
        )
        st.session_state.transcribed_text = ""
        st.rerun()


# --------------------------------------------------
# 11. CONTINUOUS CONVERSATION
# --------------------------------------------------

typed_question = st.chat_input(
    "Ask a question, or type exit..."
)

pending_question = st.session_state.pop(
    "pending_question", None
)

question = typed_question or pending_question

if question:
    if question.strip().lower() in {
        "exit", "quit", "bye"
    }:
        st.session_state.chat_history.append({
            "role": "user",
            "content": question
        })

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": (
                "Goodbye! Your study session has ended. "
                "You can start another conversation whenever "
                "you are ready."
            )
        })

        st.rerun()

    st.session_state.chat_history.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    relevant_chunks = (
        retrieve_relevant_chunks(question, chunks)
        if chunks
        else []
    )

    source_labels = list(dict.fromkeys(
        f"{item['source']} (page {item['page']})"
        for item in relevant_chunks
    ))

    context = format_document_context(relevant_chunks)

    messages = [{
        "role": "system",
        "content": (
            f"You are {APP_NAME}, a friendly and accurate "
            f"study assistant. Explain at {difficulty} level. "
            "Give examples and step-by-step explanations when useful. "
            "When PDF context is supplied, prioritize it and cite "
            "the filename and page. If the PDF does not answer the "
            "question, clearly say so."
        )
    }]

    # Keep recent turns to control prompt size.
    for item in st.session_state.chat_history[-12:]:
        if item["role"] in {"user", "assistant"}:
            messages.append({
                "role": item["role"],
                "content": item["content"]
            })

    if context:
        messages.append({
            "role": "system",
            "content": (
                "Relevant excerpts from uploaded study documents:\n"
                + context
            )
        })

    with st.chat_message("assistant"):
        try:
            with st.spinner("Thinking..."):
                answer = generate_response(
                    provider,
                    model,
                    messages
                )

            st.markdown(answer)

            if source_labels:
                st.caption(
                    "PDF sources: " + "; ".join(source_labels)
                )

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": answer,
                "sources": source_labels
            })

            if speak_answers:
                try:
                    audio = text_to_speech(
                        answer,
                        voice_language
                    )
                    st.audio(audio, format="audio/mp3")
                except Exception as exc:
                    st.warning(f"Could not create speech: {exc}")

        except Exception as exc:
            error_message = (
                f"Could not generate a response: {exc}"
            )
            st.error(error_message)

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": error_message
            })