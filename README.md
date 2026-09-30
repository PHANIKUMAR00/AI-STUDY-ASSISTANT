<<<<<<< HEAD

# 📚 My Personal Chatbot — AI Study Assistant

An AI-powered study assistant built with **Python and Streamlit** that helps students understand study materials, summarize PDFs, prepare for exams, and interact with an AI model through text and voice.

The application supports **Ollama with local Gemma models** and the **Groq API** for cloud-based AI responses.

## ✨ Features

- **AI Chatbot:** Ask questions and receive explanations in a conversational interface.
- **PDF Upload:** Upload multiple PDF documents simultaneously.
- **PDF Summarization:** Generate structured summaries, key concepts, definitions, and revision notes.
- **Question Answering:** Ask questions based on uploaded study materials.
- **RAG-Based Retrieval:** Retrieve relevant document sections using TF-IDF similarity.
- **Source References:** Display PDF filenames and page numbers for relevant information.
- **MCQ Generation:** Generate multiple-choice questions with answers and explanations.
- **Flashcard Generation:** Create question-and-answer flashcards for revision.
- **Exam Preparation:** Generate important short-answer and long-answer questions.
- **Voice Input:** Record questions and convert speech into text.
- **Text-to-Speech:** Listen to AI-generated answers and study materials.
- **Difficulty Levels:** Choose Beginner, Intermediate, or Advanced explanations.
- **Dynamic Model Discovery:** Automatically discover installed Ollama models or available Groq models.
- **Conversation History:** Maintain recent messages during a session.
- **Continuous Chat:** Continue asking questions until you type `exit`, `quit`, or `bye`.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| Streamlit | Web interface |
| Ollama | Run AI models locally |
| Gemma | Local language model |
| Groq API | Cloud-based AI inference |
| PyPDF | Extract text from PDF documents |
| Scikit-learn | TF-IDF vectorization and similarity search |
| Requests | Communicate with the Ollama API |
| python-dotenv | Load environment variables |
| Groq Whisper | Cloud-based speech recognition |
| faster-whisper | Local speech recognition |
| gTTS | Convert text into speech |

## 📁 Project Structure

```text
my_personal_chatbot/
│
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── .env                # API keys and configuration
├── .env.example        # Example configuration
├── .gitignore          # Files excluded from Git
└── README.md           # Project documentation
```

## ⚙️ Requirements

Before running the application, install the following:

- Python 3.10 or a compatible newer version
- pip
- A web browser
- Either Ollama with an installed model or a Groq API key
- Internet access for Groq, gTTS, and initial package/model downloads

## 🚀 Installation and Setup

### Step 1: Clone or Download the Project

Open PowerShell or the VS Code terminal and navigate to your project directory.

```powershell
cd path\to\my_personal_chatbot
```

### Step 2: Create a Virtual Environment

```powershell
py -m venv .venv
```

Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks environment activation, you can use the environment's Python executable directly.

### Step 3: Install Dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root.

**Option A: Local AI with Ollama and Gemma**

```env
DEFAULT_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
GROQ_API_KEY=
```

**Option B: Cloud AI with Groq**

```env
DEFAULT_PROVIDER=groq
OLLAMA_BASE_URL=http://localhost:11434
GROQ_API_KEY=your_actual_groq_api_key
```

Replace the placeholder with your own Groq API key if you use the cloud provider.

**Security:** Never upload your real API key to GitHub or share it publicly.

### Step 5: Install and Configure Ollama (Local AI)

Download Ollama from:

https://ollama.com/download/windows

Open PowerShell and download the Gemma model:

```powershell
ollama pull gemma3:1b
```

Verify that the model is installed:

```powershell
ollama list
```

Start the Ollama server if it is not already running:

```powershell
ollama serve
```

Keep the server running while using the chatbot.

Verify the local API:

```powershell
Invoke-RestMethod http://localhost:11434/api/tags
```

If this command returns the installed models, the local API is reachable.

### Step 6: Run the Application

From your project directory, run:

```powershell
streamlit run app.py
```

The application should open in your default browser. If it does not, open:

http://localhost:8501

## 📖 How to Use the Application

1. Launch the application.
2. Select your preferred AI provider in the sidebar.
3. Choose an available model.
4. Upload one or more PDF study materials.
5. Preview the extracted text to confirm that the documents were read correctly.
6. Select one of the study tools:
   - Summarize PDFs
   - Generate MCQs
   - Generate flashcards
   - Important questions
7. Enter questions in the chatbot to learn concepts from your PDFs.
8. Select a difficulty level to adjust explanations.
9. Record a voice question if you want to use speech input.
10. Enable spoken answers or use the audio option to listen to generated study material.
11. Type `exit`, `quit`, or `bye` to end the conversation.

## 🧠 How It Works

### 1. Document Processing

Uploaded PDFs are processed using PyPDF. The application extracts selectable text page by page and records the filename and page number.

### 2. Text Chunking

Extracted text is divided into smaller, overlapping chunks. This helps the application search through documents without sending the entire document for every question.

### 3. Relevant Information Retrieval

Scikit-learn's TF-IDF vectorizer converts document chunks and the user's question into numerical representations. Cosine similarity identifies relevant chunks.

### 4. AI Response Generation

The retrieved information is included in the prompt sent to the selected language model.

- **Ollama:** Sends requests to a locally running model through the Ollama API.
- **Groq:** Sends requests to a supported cloud model through the Groq API.

The model generates explanations, answers, summaries, or study materials.

### 5. Speech Processing

Voice input can be transcribed using Groq Whisper or local faster-whisper. The gTTS library converts generated text into audio.

## 🏗️ System Architecture

```text
             Student
                |
                v
       Streamlit Web Interface
                |
       +--------+---------+
       |                  |
       v                  v
   PDF Upload          Chat / Voice
       |                  |
       v                  v
   PyPDF Text         Speech-to-Text
   Extraction              |
       |                  |
       v                  |
   Text Chunking           |
       |                  |
       v                  |
   TF-IDF Retrieval <------+
       |
       v
   Relevant Context
       |
       v
   AI Model Selection
       |
       +-------------------+
       |                   |
       v                   v
   Ollama + Gemma       Groq API
       |                   |
       +---------+---------+
                 |
                 v
          Generated Answer
                 |
          +------+------+
          |             |
          v             v
      Text Output    Text-to-Speech
```

## 🔧 Troubleshooting

### Problem 1: Connection Refused on Port 11434

Example error:

```text
HTTPConnectionPool(host='localhost', port=11434):
Max retries exceeded with url: /api/chat
```

**Solution:**

1. Confirm Ollama is installed.
2. Open PowerShell.
3. Run `ollama list`.
4. Start the server with `ollama serve` if necessary.
5. Check `http://localhost:11434/api/tags`.
6. Restart Streamlit after confirming the connection.

### Problem 2: No Models Found

For Ollama, install a model:

```powershell
ollama pull gemma3:1b
```

For Groq, verify that your API key is correctly configured in `.env`.

### Problem 3: Groq API Authentication Error

Check that the API key is valid, has no extra spaces, and is configured as:

```env
GROQ_API_KEY=your_actual_groq_api_key
```

Restart Streamlit after changing `.env`.

### Problem 4: PDF Contains No Extracted Text

Some PDFs contain scanned images rather than selectable text. These documents may require OCR before they can be processed by this application.

### Problem 5: Speech Recognition Errors

For local speech recognition, install the dependencies:

```powershell
pip install faster-whisper
```

For Groq-based speech recognition, verify the API key and your network connection.

### Problem 6: Text-to-Speech Errors

The gTTS library requires an internet connection. Check your network connection if speech generation fails.

## 🔐 Security and Privacy

- Keep `.env` out of version control.
- Never commit API keys to GitHub.
- Local Ollama inference sends model prompts to your local Ollama server.
- Groq requests are processed through the cloud API.
- The application uses in-memory session state for chat history; it does not implement persistent chat-history storage.
- PDF retrieval uses TF-IDF and cosine similarity, not a persistent vector database.

## ⚠️ Current Limitations

- Scanned PDFs may need OCR.
- TF-IDF retrieval is a lightweight search approach and may miss semantically related passages.
- Local response speed depends on available hardware and model size.
- Local faster-whisper transcription may require additional model downloads.
- gTTS requires internet access.
- Model availability depends on the selected provider and its installed or accessible models.

## 🔮 Future Enhancements

- Persistent conversation history
- OCR support for scanned PDFs
- Advanced semantic search using embeddings
- Vector database integration with FAISS or Chroma
- User authentication and multiple user profiles
- Export summaries and flashcards to PDF
- More speech languages
- Improved source citations and retrieval accuracy

## 🎯 Project Objective

The objective of **My Personal Chatbot** is to make studying more interactive and efficient by combining document understanding, conversational AI, exam preparation tools, and voice interaction in one application.

The project demonstrates practical use of large language models, API integration, document processing, information retrieval, and web application development.

## 👨‍💻 License

This project is intended for educational and personal learning purposes. Add a license file if you plan to distribute the project publicly.
```
=======
# AI-STUDY-ASSISTANT
Developed an AI Study Assistant using Python, Streamlit, Ollama (Gemma), and Groq API. Implemented PDF summarization, RAG-based question answering using TF-IDF and cosine similarity, MCQ and flashcard generation, speech-to-text with Whisper, and text-to-speech using gTTS for interactive, personalized learning
>>>>>>> 6bdfcafec2dc22c6155826bb9fa9296c248eb6ab
