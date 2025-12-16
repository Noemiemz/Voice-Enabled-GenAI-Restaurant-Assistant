# Voice-Enabled GenAI Restaurant Assistant

## Overview
This project is a voice-enabled web application designed to assist users in ordering food online from a restaurant named "Les pieds dans le plat". The application leverages modern AI technologies to provide a seamless voice interaction experience.

## Features
- **Voice Command Interface**: Users can interact with the application using voice commands.
- **AI-Powered Assistance**: Utilizes AI models for speech-to-text, text-to-speech, and natural language processing.
- **Web Application**: Built with a modern frontend and backend architecture.

## Project Structure

```
Voice-Enabled-GenAI-Restaurant-Assistant/
├── back/
│   ├── src/
│   │   ├── data/
│   │   │   ├── audio/
│   │   │   ├── db/
│   │   │   ├── json_schemas/
│   │   │   └── prompts/
│   │   ├── models/
│   │   │   ├── llm.py
│   │   │   ├── mongodb.py
│   │   │   ├── stt.py
│   │   │   └── tts.py
│   │   ├── run/
│   │   │   └── app.py
│   │   ├── supertonic/
│   │   │   ├── assets/
│   │   │   ├── helper.py
│   │   │   └── inference.py
│   │   └── test_app.py
│   ├── .env
│   ├── .env-example
│   ├── .gitignore
│   ├── output.wav
│   ├── plan.md
│   ├── README.md
│   ├── requirements.txt
│   ├── test_Lorrain.ipynb
│   └── tests_Noémie.ipynb
└── front/
    └── resto-ai-voice/
        ├── app/
        │   ├── favicon.ico
        │   ├── globals.css
        │   ├── layout.tsx
        │   └── page.tsx
        ├── public/
        │   ├── file.svg
        │   ├── globe.svg
        │   ├── next.svg
        │   ├── vercel.svg
        │   └── window.svg
        ├── .gitignore
        ├── eslint.config.mjs
        ├── next-env.d.ts
        ├── next.config.ts
        ├── package-lock.json
        ├── package.json
        ├── postcss.config.mjs
        ├── README.md
        └── tsconfig.json
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
- Python 3.8+
- Node.js 16+
- MongoDB

### Installation

#### Backend
1. Navigate to the `back` directory.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up the environment variables by copying `.env-example` to `.env` and filling in the required values.

#### Frontend
1. Navigate to the `front/resto-ai-voice` directory.
2. Install the required dependencies:
   ```bash
   npm install
   ```

### Running the Application

#### Backend
1. Navigate to the `back` directory.
2. Run the application:
   ```bash
   python src/run/app.py
   ```

#### Frontend
1. Navigate to the `front/resto-ai-voice` directory.
2. Start the development server:
   ```bash
   npm run dev
   ```

## Usage
1. Open the web application in your browser.
2. Use the voice command interface to interact with the assistant.
3. Place your order by speaking your requests.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License
This project is licensed under the MIT License.

## Contact
For any questions or feedback, please contact the project maintainers.
