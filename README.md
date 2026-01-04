# Voice-Enabled GenAI Restaurant Assistant

## Overview
This project is a voice-enabled web application designed to assist users in ordering food online from a restaurant named "Les pieds dans le plat". The application leverages modern AI technologies to provide a seamless voice interaction experience.

## Features
- **Voice Command Interface**: Users can interact with the application using voice commands.
- **AI-Powered Assistance**: Utilizes AI models for speech-to-text, text-to-speech, and natural language processing.
- **Web Application**: Built with a modern frontend and backend architecture.
- **Docker Support**: Fully containerized application for easy deployment.

## Project Structure

```
Voice-Enabled-GenAI-Restaurant-Assistant/
│
├── docker-compose.yml
├── .env.example
├── DOCKER.md
│
├── back/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt
│   ├── todo.md
│   └── src/
│       ├── pathseeker.py
│       ├── settings.py
│       ├── data/
│       │   ├── mongodb.py
│       │   ├── table_schemas.py
│       │   └── prompts/
│       │       ├── info_agent_prompt.txt
│       │       ├── order_agent_prompt.txt
│       │       ├── reservation_agent_prompt.txt
│       │       └── supervisor_prompt.txt
│       ├── models/
│       │   ├── stt.py
│       │   ├── tts.py
│       │   └── agents/
│       │       ├── __init__.py
│       │       ├── info_agent.py
│       │       ├── order_agent.py
│       │       ├── reservation_agent.py
│       │       └── supervisor.py
│       └── run/
│           ├── api.py
│           └── test_st_app.py
│
└── front/
    └── ai-restaurant-assistant/
        ├── Dockerfile
        ├── .dockerignore
        ├── package.json
        ├── next.config.ts
        ├── tsconfig.json
        ├── eslint.config.mjs
        ├── postcss.config.mjs
        ├── README.md
        ├── app/
        │   ├── globals.css
        │   ├── layout.tsx
        │   └── page.tsx
        └── public/
```

## Backend
The backend is built with Python and includes the following components:

- **Speech-to-Text (STT)**: Converts voice commands to text.
- **Text-to-Speech (TTS)**: Converts text responses to speech.
- **Language Model (LLM)**: Processes user commands and generates responses.
- **Database Integration**: Manages data storage and retrieval.

## Frontend
The frontend is built with Next.js and provides a user-friendly interface for interacting with the voice assistant.

## Getting Started

### Prerequisites

#### For Docker (Recommended)
- Docker Desktop
- Docker Compose

#### For Manual Setup
- Python 3.8+
- Node.js 16+
- MongoDB (local or cloud instance)

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone https://github.com/Noemiemz/Voice-Enabled-GenAI-Restaurant-Assistant
   cd Voice-Enabled-GenAI-Restaurant-Assistant
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your configuration:
   - `MONGODB_URI`: Your MongoDB connection string
   - `MISTRAL_API_KEY`: Your Mistral AI API key

3. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000

5. **Stop the application**
   ```bash
   docker-compose down
   ```

For more detailed Docker instructions, see [DOCKER.md](DOCKER.md).

### Manual Installation

#### Backend
1. Navigate to the `back` directory.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up the environment variables by copying `.env-example` to `.env` and filling in the required values.

#### Frontend
1. Navigate to the `front/ai-restaurant-assistant` directory.
2. Install the required dependencies:
   ```bash
   npm install
   ```

### Running the Application Manually

#### Backend
1. Navigate to the `back` directory.
2. Run the application:
   ```bash
   python src/run/api.py
   ```

#### Frontend
1. Navigate to the `front/ai-restaurant-assistant` directory.
2. Start the development server:
   ```bash
   npm run dev
   ```

## Usage
1. Open the web application in your browser.
2. Use the voice command interface to interact with the assistant.
3. Place your order by speaking your requests.

## Docker Architecture

The application uses a multi-container Docker setup:
- **Frontend Container**: Next.js application (port 3000)
- **Backend Container**: Flask API with AI models (port 5000)
- **MongoDB Container** (optional): Local database (port 27017)

All containers communicate via a Docker network and can be managed with a single `docker-compose` command.
