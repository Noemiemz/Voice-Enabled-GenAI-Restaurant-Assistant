"use client";

import { useState, useRef, useEffect } from "react";
import { io, Socket } from "socket.io-client";

interface Message {
  role: "user" | "assistant";
  content: string | { text?: string; [key: string]: any };
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const socketRef = useRef<Socket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);

  useEffect(() => {
    // Initialize socket connection
    socketRef.current = io("http://localhost:5000");

    socketRef.current.on("transcription_result", (data: { text: string, language: string }) => {
      console.log("Transcription:", data.text);
      setMessages((prev) => [...prev, { role: "user", content: data.text }]);
      
      // Send messages to get LLM response
      const allMessages = [...messages, { role: "user", content: data.text }];
      console.log("Sending to LLM:", { messages: allMessages, language: data.language });
      socketRef.current?.emit("synthesize_speech", { messages: allMessages, language: data.language });
      setIsSpeaking(true);
    });

    socketRef.current.on("llm_text_response", (data: { text: string }) => {
      console.log("LLM Response:", data.text);
      setMessages((prev) => [...prev, { role: "assistant", content: data.text }]);
    });

    socketRef.current.on("llm_audio_chunk", async (data: { audio: string; sample_rate: number }) => {
      console.log("Received audio chunk");
      // Play audio chunk
      if (!audioContextRef.current) {
        audioContextRef.current = new AudioContext();
      }
      
      try {
        // Decode base64 audio data
        const binaryString = atob(data.audio);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        
        // Convert bytes to Int16Array (PCM audio format)
        const int16Array = new Int16Array(bytes.buffer);
        
        // Create audio buffer with the correct sample rate
        const audioBuffer = audioContextRef.current.createBuffer(
          1, // mono
          int16Array.length,
          data.sample_rate
        );
        
        // Convert int16 to float32 and fill the buffer
        const channelData = audioBuffer.getChannelData(0);
        for (let i = 0; i < int16Array.length; i++) {
          channelData[i] = int16Array[i] / 32768.0; // Normalize to -1.0 to 1.0
        }
        
        // Play the audio
        const source = audioContextRef.current.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContextRef.current.destination);
        source.start();
        
        source.onended = () => {
          setIsSpeaking(false);
        };
      } catch (error) {
        console.error("Error playing audio:", error);
        setIsSpeaking(false);
      }
    });

    return () => {
      socketRef.current?.disconnect();
    };
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        
        // Decode WebM to raw PCM audio
        if (!audioContextRef.current) {
          audioContextRef.current = new AudioContext({ sampleRate: 16000 });
        }
        
        const arrayBuffer = await audioBlob.arrayBuffer();
        const audioBuffer = await audioContextRef.current.decodeAudioData(arrayBuffer);
        
        // Get raw float32 PCM data
        const pcmData = audioBuffer.getChannelData(0); // mono audio
        
        // Convert Float32Array to base64 for transmission
        const uint8Array = new Uint8Array(pcmData.buffer);
        
        // Convert to base64 in chunks to avoid call stack size exceeded
        let binary = '';
        const chunkSize = 0x8000; // 32KB chunks
        for (let i = 0; i < uint8Array.length; i += chunkSize) {
          const chunk = uint8Array.subarray(i, i + chunkSize);
          binary += String.fromCharCode(...chunk);
        }
        const base64Audio = btoa(binary);
        
        socketRef.current?.emit("transcribe_audio", { audio_data: base64Audio });
        
        // Stop all tracks
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error("Error accessing microphone:", error);
      alert("Please allow microphone access to use this feature");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleMicClick = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <div className="flex h-screen bg-orange-50 overflow-hidden">
      {/* Left Column - LLM Animation */}
      <div className="flex-1 flex items-center justify-center p-8">
        <LLMAnimation isSpeaking={isSpeaking} />
      </div>

      {/* Middle Column - Chat */}
      <div className="flex-1 flex flex-col p-8">
        <div className="flex flex-col h-full bg-white/60 backdrop-blur-sm rounded-2xl shadow-lg border border-slate-200">
          <h2 className="text-2xl font-bold text-slate-700 p-6 pb-4">Conversation</h2>
          <div className="flex-1 overflow-y-auto px-6 pb-6">
            <div className="space-y-4">
              {messages.length === 0 ? (
                <div className="text-center text-slate-400 mt-20">
                  <p className="text-lg">Click the microphone to start talking</p>
                </div>
              ) : (
                messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${
                      message.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div
                      className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                        message.role === "user"
                          ? "bg-sky-400/80 text-white shadow-sm"
                          : "bg-amber-100/70 text-slate-700 shadow-sm"
                      }`}
                    >
                      <p className="text-sm font-medium mb-1">
                        {message.role === "user" ? "You" : "Assistant"}
                      </p>
                      <p>{typeof message.content === 'string' ? message.content : message.content.text || JSON.stringify(message.content)}</p>
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>
        </div>
      </div>

      {/* Right Column - Microphone */}
      <div className="flex-1 flex items-center justify-center p-8">
        <MicrophoneButton isRecording={isRecording} onClick={handleMicClick} />
      </div>
    </div>
  );
}

// LLM Animation Component
function LLMAnimation({ isSpeaking }: { isSpeaking: boolean }) {
  return (
    <div className="relative w-48 h-48">
      <div className="absolute inset-0 flex items-center justify-center">
        {/* Central circle */}
        <div className="absolute w-32 h-32 bg-gradient-to-br from-amber-100 to-orange-100 rounded-full shadow-md shadow-amber-300/30" />
      </div>
      
      {/* Outer glow ring */}
      <div
        className={`absolute inset-0 rounded-full border-4 border-amber-300/40 transition-all duration-300 ${
          isSpeaking ? "scale-110 border-amber-400/60" : "scale-100"
        }`}
      />
    </div>
  );
}

// Microphone Button Component
function MicrophoneButton({
  isRecording,
  onClick,
}: {
  isRecording: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`relative w-32 h-32 rounded-full transition-all duration-300 shadow-lg ${
        isRecording
          ? "bg-rose-400 scale-110 shadow-rose-400/40"
          : "bg-sky-400 hover:bg-sky-500 shadow-sky-400/40"
      }`}
    >
      {/* Microphone Icon */}
      <div className="flex items-center justify-center h-full">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={2}
          stroke="currentColor"
          className="w-12 h-12 text-white"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z"
          />
        </svg>
      </div>
      
      {/* Recording pulse animation */}
      {isRecording && (
        <div className="absolute inset-0 rounded-full bg-red-500 animate-ping opacity-75" />
      )}
    </button>
  );
}
