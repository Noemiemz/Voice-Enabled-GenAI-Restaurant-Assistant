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
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcriptionError, setTranscriptionError] = useState<string>("");
  const [userLanguage, setUserLanguage] = useState<string>("en");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const socketRef = useRef<Socket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<AudioBuffer[]>([]);
  const isPlayingRef = useRef(false);
  const hasInitializedSocket = useRef(false);

  const playNextAudioChunk = () => {
    if (!audioContextRef.current || audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      setIsSpeaking(false);
      setIsProcessing(false);
      return;
    }

    isPlayingRef.current = true;
    setIsSpeaking(true);

    const audioBuffer = audioQueueRef.current.shift()!;
    const source = audioContextRef.current.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContextRef.current.destination);
    
    source.onended = () => {
      playNextAudioChunk(); // Play next chunk when current one finishes
    };
    
    source.start();
  };

  useEffect(() => {
    // Prevent double initialization from React Strict Mode
    if (hasInitializedSocket.current) {
      return;
    }
    
    hasInitializedSocket.current = true;

    // Initialize socket connection
    socketRef.current = io("http://localhost:5000");
    const socket = socketRef.current;

    socket.on("transcription_result", (data: { text: string, language: string, error: string | null }) => {
      console.log("Transcription:", data.text);
      if (data.error) {
        setTranscriptionError(data.error);
      } else {
        setTranscriptionError("");
      }
      if (data.text === "") {
        setIsProcessing(false);
        return;
      }
      
      setMessages((prev) => [
        ...prev,
        { role: "user" as const, content: data.text }
      ]);

      setUserLanguage(data.language);
      
      setIsSpeaking(true);
    });

    socket.on("llm_text_response", (data: { text: string }) => {
      console.log("LLM Response:", data.text);
      setMessages((prev) => [...prev, { role: "assistant", content: data.text }]);
    });

    socket.on("llm_audio_chunk", async (data: { audio: string; sample_rate: number }) => {
      console.log("Received audio chunk");
      // Initialize audio context if needed
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
        
        // Add to queue
        audioQueueRef.current.push(audioBuffer);
        
        // Start playing if not already playing
        if (!isPlayingRef.current) {
          playNextAudioChunk();
        }
      } catch (error) {
        console.error("Error processing audio chunk:", error);
      }
    });

    return () => {
      // Disconnect on unmount
      socket.disconnect();
    };
  }, []);

  useEffect(() => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.role === "user") {
        console.log("Sending to LLM:", { messages, language: userLanguage });
        socketRef.current?.emit("synthesize_speech", { messages, language: userLanguage });
        setIsSpeaking(true);
      }
    }
  }, [messages]); // Only re-run if messages changes

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const startRecording = async () => {
    try {
      setTranscriptionError(""); // Clear any previous errors
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
      setIsProcessing(true);
    }
  };

  const handleMicClick = () => {
    // Don't allow recording while processing or LLM is speaking
    if ((isProcessing || isSpeaking) && !isRecording) {
      return;
    }
    
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const clearHistory = async () => {
    try {
      const response = await fetch("http://localhost:5000/clear_history", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });
      
      if (response.ok) {
        setMessages([]);
        console.log("History cleared successfully");
      } else {
        console.error("Failed to clear history");
      }
    } catch (error) {
      console.error("Error clearing history:", error);
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
          {messages.length > 0 && (
            <div className="px-6 pb-4">
              <button
                onClick={clearHistory}
                className="w-full py-2 px-4 bg-red-400/80 hover:bg-red-500 text-white rounded-lg transition-colors duration-200 font-medium text-sm"
              >
                Clear History
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Right Column - Microphone */}
      <div className="flex-1 flex flex-col items-center justify-center p-8">
        <MicrophoneButton isRecording={isRecording} isSpeaking={isSpeaking} isProcessing={isProcessing} onClick={handleMicClick} />
        {transcriptionError && (
          <div className="mt-4 text-red-500 text-center max-w-md">
            <p className="text-sm font-medium">{transcriptionError}</p>
          </div>
        )}
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
  isSpeaking,
  isProcessing,
  onClick,
}: {
  isRecording: boolean;
  isSpeaking: boolean;
  isProcessing: boolean;
  onClick: () => void;
}) {
  const isDisabled = (isProcessing || isSpeaking) && !isRecording;
  
  return (
    <button
      onClick={onClick}
      disabled={isDisabled}
      className={`relative w-32 h-32 rounded-full transition-all duration-300 shadow-lg ${
        isRecording
          ? "bg-rose-400 scale-110 shadow-rose-400/40"
          : isDisabled
          ? "bg-gray-400 cursor-not-allowed shadow-gray-400/40"
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
