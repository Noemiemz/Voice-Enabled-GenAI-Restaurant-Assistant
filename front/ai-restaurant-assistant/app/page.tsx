"use client";

import { useState, useRef, useEffect } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleMicClick = () => {
    if (!isRecording) {
      // Start recording
      setIsRecording(true);
      // Simulate recording for 2 seconds
      setTimeout(() => {
        setIsRecording(false);
        // Simulate user message
        const userMessage = "Hello, I'd like to make a reservation.";
        setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
        
        // Simulate LLM response with speaking animation
        setTimeout(() => {
          setIsSpeaking(true);
          setTimeout(() => {
            const assistantMessage =
              "Of course! I'd be happy to help you with a reservation. For how many people?";
            setMessages((prev) => [
              ...prev,
              { role: "assistant", content: assistantMessage },
            ]);
            // Keep speaking animation for 2 seconds
            setTimeout(() => {
              setIsSpeaking(false);
            }, 2000);
          }, 500);
        }, 500);
      }, 2000);
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
                      <p>{message.content}</p>
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
