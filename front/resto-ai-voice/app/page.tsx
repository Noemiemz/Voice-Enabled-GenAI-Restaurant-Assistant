"use client";

import { useState, useRef, useEffect } from 'react'
import Image from "next/image"
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import api, { DishesByCategory } from './services/api'

export default function Home() {
  const [isRecording, setIsRecording] = useState(false)
  const [conversation, setConversation] = useState<{role: string, content: string, timestamp: string}[]>([])
  const [isListening, setIsListening] = useState(false)
  const [activeSection, setActiveSection] = useState<'menu' | 'dishes' | 'reservation' | null>(null)
  const [menuData, setMenuData] = useState<{
    categories: Array<{
      name: string;
      items: Array<{
        name: string;
        price: string;
        description: string;
      }>;
    }>;
  } | null>(null)
  const [dishesData, setDishesData] = useState<DishesByCategory | null>(null)
  const [isLoadingMenu, setIsLoadingMenu] = useState(false)
  const [isLoadingDishes, setIsLoadingDishes] = useState(false)
  const [menuError, setMenuError] = useState<string | null>(null)
  const [dishesError, setDishesError] = useState<string | null>(null)
  const [textInput, setTextInput] = useState('')
  const [isSendingText, setIsSendingText] = useState(false)
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  
  // Fetch menu from backend API
  const fetchMenu = async () => {
    // If already showing, toggle off
    if (activeSection === 'menu') {
      setActiveSection(null)
      return
    }
    
    // Switch to menu section immediately
    setActiveSection('menu')
    
    // If we already have data, don't refetch
    if (menuData) return
    
    try {
      setIsLoadingMenu(true)
      setMenuError(null)
      
      const menu = await api.getMenu()
      setMenuData(menu)
      
    } catch (error) {
      console.error('Error fetching menu:', error)
      setMenuError('Failed to load menu. Please try again.')
    } finally {
      setIsLoadingMenu(false)
    }
  }

  // Fetch dishes from backend API
  const fetchDishes = async () => {
    // If already showing, toggle off
    if (activeSection === 'dishes') {
      setActiveSection(null)
      return
    }
    
    // Switch to dishes section immediately
    setActiveSection('dishes')
    
    // If we already have data, don't refetch
    if (dishesData) return
    
    try {
      setIsLoadingDishes(true)
      setDishesError(null)
      
      const dishes = await api.getDishes()
      setDishesData(dishes)
      
    } catch (error) {
      console.error('Error fetching dishes:', error)
      setDishesError('Failed to load dishes. Please try again.')
    } finally {
      setIsLoadingDishes(false)
    }
  }
  
  const startRecording = async () => {
    try {
      // Request audio with better quality settings
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1,
          sampleRate: 16000, // Optimal for speech recognition
          sampleSize: 16
        }
      })
      
      // Use WAV format explicitly
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/wav',
        audioBitsPerSecond: 128000
      })
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }
      
      mediaRecorder.onstop = async () => {
        if (audioChunksRef.current.length === 0) {
          const errorResponse = {
            role: 'assistant',
            content: 'Désolé, je n\'ai pas capté votre message. Veuillez parler pendant l\'enregistrement.',
            timestamp: new Date().toLocaleTimeString()
          }
          setConversation(prev => [...prev, errorResponse])
          return
        }
        
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' })
        
        // Check audio blob size
        if (audioBlob.size < 1024) { // Less than 1KB
          const errorResponse = {
            role: 'assistant',
            content: 'Désolé, votre message est trop court. Veuillez parler plus longtemps.',
            timestamp: new Date().toLocaleTimeString()
          }
          setConversation(prev => [...prev, errorResponse])
          return
        }
        
        // Add user message to conversation
        const newMessage = {
          role: 'user',
          content: 'Enregistrement envoyé...',
          timestamp: new Date().toLocaleTimeString()
        }
        setConversation(prev => [...prev, newMessage])
        
        try {
          // Send audio to backend API
          const { textResponse } = await api.sendAudioRecording(audioBlob)
          
          // Add assistant response to conversation
          const assistantResponse = {
            role: 'assistant',
            content: textResponse,
            timestamp: new Date().toLocaleTimeString()
          }
          setConversation(prev => [...prev, assistantResponse])
          
        } catch (error) {
          console.error('Error processing audio:', error)
          let errorMessage = 'Désolé, je n\'ai pas pu traiter votre demande. Veuillez réessayer.'
          
          // Extract more specific error message if available
          if (
            typeof error === 'object' &&
            error !== null &&
            'response' in error &&
            typeof (error as any).response === 'object' &&
            (error as any).response !== null &&
            'data' in (error as any).response &&
            typeof (error as any).response.data === 'object' &&
            (error as any).response.data !== null &&
            'error' in (error as any).response.data
          ) {
            const backendError = (error as any).response.data.error
            if (typeof backendError === 'string') {
              if (backendError.includes('Empty audio file') || backendError.includes('Audio file too short')) {
                errorMessage = 'Désolé, je n\'ai pas entendu votre message. Veuillez parler plus fort et plus longtemps.'
              } else if (backendError.includes('Could not transcribe audio')) {
                errorMessage = 'Désolé, je n\'ai pas compris votre message. Veuillez parler plus clairement.'
              } else if (backendError.includes('Invalid audio file type')) {
                errorMessage = 'Désolé, il y a un problème avec l\'enregistrement audio. Veuillez réessayer.'
              } else {
                errorMessage = `Désolé, une erreur est survenue: ${backendError}`
              }
            }
          } else if (
            typeof error === 'object' &&
            error !== null &&
            'message' in error &&
            typeof (error as any).message === 'string' &&
            (error as any).message.includes('Network Error')
          ) {
            errorMessage = 'Désolé, il semble y avoir un problème de connexion. Veuillez vérifier votre connexion internet.'
          }
          
          const errorResponse = {
            role: 'assistant',
            content: errorMessage,
            timestamp: new Date().toLocaleTimeString()
          }
          setConversation(prev => [...prev, errorResponse])
        }
      }
      
      mediaRecorder.start()
      setIsRecording(true)
      setIsListening(true)
      
      // Stop recording after 5 seconds (or when user stops)
      setTimeout(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
          mediaRecorderRef.current.stop()
          stream.getTracks().forEach(track => track.stop())
          setIsRecording(false)
          setIsListening(false)
        }
      }, 5000)
      
    } catch (error) {
      console.error('Error accessing microphone:', error)
      alert('Microphone access denied. Please enable microphone permissions.')
    }
  }
  
  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop()
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop())
      setIsRecording(false)
      setIsListening(false)
    }
  }
  
  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!textInput.trim()) return
    
    const userMessage = {
      role: 'user',
      content: textInput,
      timestamp: new Date().toLocaleTimeString()
    }
    setConversation(prev => [...prev, userMessage])
    setTextInput('')
    setIsSendingText(true)
    
    try {
      const { textResponse } = await api.sendTextMessage(textInput, conversation)
      
      const assistantResponse = {
        role: 'assistant',
        content: textResponse,
        timestamp: new Date().toLocaleTimeString()
      }
      setConversation(prev => [...prev, assistantResponse])
      
    } catch (error) {
      console.error('Error sending text message:', error)
      let errorMessage = 'Désolé, je n\'ai pas pu traiter votre demande. Veuillez réessayer.'
      
      if (
        typeof error === 'object' &&
        error !== null &&
        'response' in error &&
        typeof (error as any).response === 'object' &&
        (error as any).response !== null &&
        'data' in (error as any).response &&
        typeof (error as any).response.data === 'object' &&
        (error as any).response.data !== null &&
        'error' in (error as any).response.data
      ) {
        const backendError = (error as any).response.data.error
        if (typeof backendError === 'string') {
          errorMessage = `Désolé, une erreur est survenue: ${backendError}`
        }
      } else if (
        typeof error === 'object' &&
        error !== null &&
        'message' in error &&
        typeof (error as any).message === 'string' &&
        (error as any).message.includes('Network Error')
      ) {
        errorMessage = 'Désolé, il semble y avoir un problème de connexion. Veuillez vérifier votre connexion internet.'
      }
      
      const errorResponse = {
        role: 'assistant',
        content: errorMessage,
        timestamp: new Date().toLocaleTimeString()
      }
      setConversation(prev => [...prev, errorResponse])
    } finally {
      setIsSendingText(false)
    }
  }
  
  const handleReservationSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    const form = e.target as HTMLFormElement
    const formData = new FormData(form)
    
    const reservationData = {
      name: formData.get('name') as string,
      phone: formData.get('phone') as string,
      date: formData.get('date') as string,
      time: formData.get('time') as string,
      guests: parseInt(formData.get('guests') as string)
    }
    
    try {
      const response = await api.createReservation(reservationData)
      
      const reservationMessage = {
        role: 'user',
        content: `Réservation confirmée pour ${reservationData.guests} personnes le ${reservationData.date} à ${reservationData.time}.`,
        timestamp: new Date().toLocaleTimeString()
      }
      setConversation(prev => [...prev, reservationMessage])
      
      const assistantResponse = {
        role: 'assistant',
        content: "Merci pour votre réservation ! Nous vous attendons avec plaisir.",
        timestamp: new Date().toLocaleTimeString()
      }
      setConversation(prev => [...prev, assistantResponse])
      
      setActiveSection(null)
    } catch (error) {
      console.error('Error creating reservation:', error)
      const errorResponse = {
        role: 'assistant',
        content: "Désolé, nous n'avons pas pu traiter votre réservation. Veuillez réessayer.",
        timestamp: new Date().toLocaleTimeString()
      }
      setConversation(prev => [...prev, errorResponse])
    }
  }
  
  const getCurrentTime = () => {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  
  const clearConversation = () => {
    setConversation([])
  }
  
  // Load restaurant info on component mount
  useEffect(() => {
    const loadRestaurantInfo = async () => {
      try {
        const info = await api.getRestaurantInfo()
        console.log('Restaurant info:', info)
      } catch (error) {
        console.error('Failed to load restaurant info:', error)
      }
    }
    
    loadRestaurantInfo()
  }, [])
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 to-orange-100 font-sans">
      <div className="max-w-4xl mx-auto p-4">
        {/* Restaurant Header */}
        <header className="text-center py-8">
          <div className="flex justify-center mb-4">
            <Image
              src="/restaurant-logo.svg"
              alt="Les Pieds dans le Plat Logo"
              width={120}
              height={120}
              className="mx-auto"
            />
          </div>
          <h1 className="text-4xl font-bold text-orange-800 mb-2">Les Pieds dans le Plat</h1>
          <p className="text-lg text-orange-600 italic">L&#39;art culinaire à Paris</p>
          <div className="mt-4 flex justify-center items-center space-x-4">
            <span className="text-sm text-orange-500">📍 1 Avenue des Champs-Élysées, 75008 Paris</span>
            <span className="text-sm text-orange-500">⏰ Ouvert de 11h à 1h</span>
          </div>
        </header>
        
        {/* Main Content */}
        <main className="bg-white rounded-lg shadow-lg p-6 mb-6">
          {/* Conversation Area */}
          <div className="mb-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-semibold text-orange-700">Conversation</h2>
              {conversation.length > 0 && (
                <button
                  onClick={clearConversation}
                  className="bg-red-100 hover:bg-red-200 text-red-700 py-2 px-4 rounded-lg transition-colors flex items-center gap-2 text-sm font-medium"
                  title="Effacer la conversation"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  <span>Effacer</span>
                </button>
              )}
            </div>
            <div className="border border-orange-200 rounded-lg p-4 h-96 overflow-y-auto bg-orange-50">
              {conversation.length === 0 ? (
                <div className="text-center py-8 text-orange-400">
                  <p>Bienvenue chez Les Pieds dans le Plat !</p>
                  <p className="mt-2">Appuyez sur le microphone pour commencer.</p>
                </div>
              ) : (
                conversation.map((message, index) => (
                  <div key={index} className={`mb-4 p-3 rounded-lg ${message.role === 'user' ? 'bg-orange-100 ml-auto max-w-xs' : 'bg-blue-100 mr-auto max-w-xs'}`}>
                    <div className="flex justify-between items-start mb-1">
                      <span className="font-medium text-sm capitalize text-gray-800">{message.role}</span>
                      <span className="text-xs text-gray-500">{message.timestamp}</span>
                    </div>
                    {message.role === 'assistant' ? (
                      <div className="text-sm text-gray-900 prose prose-sm max-w-none prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
                      </div>
                    ) : (
                      <p className="text-sm text-gray-900">{message.content}</p>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
          
          {/* Voice Control */}
          <div className="flex justify-center mb-6">
            <button
              onClick={isRecording ? stopRecording : startRecording}
              className={`w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300 ${isRecording ? 'bg-red-500 scale-110' : 'bg-orange-500 hover:bg-orange-600'}`}
              disabled={isListening && !isRecording}
            >
              {isRecording ? (
                <svg className="w-10 h-10 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1zm4 0a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="w-10 h-10 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 017 8a5 5 0 015 5v1.93a1 1 0 102 0V8a7 7 0 00-7-7h-1a7 7 0 00-7 7v8.93a1 1 0 102 0V8a5 5 0 015-5h1a5 5 0 015 5v1.93z" clipRule="evenodd" />
                </svg>
              )}
            </button>
          </div>
          
          {/* Text Input */}
          <form onSubmit={handleTextSubmit} className="mb-6">
            <div className="flex gap-2">
              <input
                type="text"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="Tapez votre message..."
                disabled={isSendingText}
                className="flex-1 p-3 border border-orange-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-300 text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
              />
              <button
                type="submit"
                disabled={isSendingText || !textInput.trim()}
                className="bg-orange-500 hover:bg-orange-600 text-white py-3 px-6 rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isSendingText ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Envoi...</span>
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
                    </svg>
                    <span>Envoyer</span>
                  </>
                )}
              </button>
            </div>
          </form>
          
          {/* Status */}
          {isListening && (
            <div className="text-center mb-4">
              <div className="flex items-center justify-center space-x-2">
                <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                <span className="text-orange-600 font-medium">Écoute en cours...</span>
              </div>
            </div>
          )}
          
          {/* Quick Actions */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <button
              onClick={fetchMenu}
              disabled={isLoadingMenu}
              className={`bg-orange-100 hover:bg-orange-200 text-orange-700 py-3 px-4 rounded-lg transition-colors flex items-center justify-center space-x-2 ${isLoadingMenu ? 'opacity-70 cursor-not-allowed' : ''}`}
            >
              <span>🍽️</span>
              <span>{isLoadingMenu ? 'Chargement...' : 'Voir le Menu'}</span>
            </button>
            <button
              onClick={fetchDishes}
              disabled={isLoadingDishes}
              className={`bg-orange-100 hover:bg-orange-200 text-orange-700 py-3 px-4 rounded-lg transition-colors flex items-center justify-center space-x-2 ${isLoadingDishes ? 'opacity-70 cursor-not-allowed' : ''}`}
            >
              <span>🍕</span>
              <span>{isLoadingDishes ? 'Chargement...' : 'Nos Plats'}</span>
            </button>
            <button
              onClick={() => setActiveSection(activeSection === 'reservation' ? null : 'reservation')}
              className="bg-orange-100 hover:bg-orange-200 text-orange-700 py-3 px-4 rounded-lg transition-colors flex items-center justify-center space-x-2"
            >
              <span>📅</span>
              <span>Réserver</span>
            </button>
          </div>
          
          {/* Dishes Section */}
          {activeSection === 'dishes' && (
            <div className="mb-6 border-t border-orange-200 pt-4">
              <h3 className="text-xl font-semibold text-orange-700 mb-4">Nos Plats</h3>
              
              {dishesError && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                  <p className="text-red-600 text-center">{dishesError}</p>
                  <button
                    onClick={fetchDishes}
                    disabled={isLoadingDishes}
                    className="mt-2 bg-orange-100 hover:bg-orange-200 text-orange-700 py-2 px-4 rounded-lg transition-colors text-sm"
                  >
                    Réessayer
                  </button>
                </div>
              )}
              
              {isLoadingDishes ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500 mx-auto mb-4"></div>
                  <p className="text-orange-600">Chargement des plats...</p>
                </div>
              ) : dishesData ? (
                <div className="space-y-6">
                  {Object.entries(dishesData).sort(([catA], [catB]) => {
                    const order = ['Starter', 'Main', 'Dessert', 'Drink'];
                    return order.indexOf(catA) - order.indexOf(catB);
                  }).map(([category, dishes]) => (
                    <div key={category} className="border border-orange-100 rounded-lg p-4">
                      <h4 className="font-medium text-orange-600 mb-3 text-lg">
                        {category === 'Starter' ? '🥗 Entrées' : 
                         category === 'Main' ? '🍖 Plats' : 
                         category === 'Dessert' ? '🍰 Desserts' : 
                         category === 'Drink' ? '🥤 Boissons' : category}
                      </h4>
                      <div className="space-y-3">
                        {dishes.map((dish) => (
                          <div key={dish._id} className="border-l-4 border-orange-300 pl-3 py-2">
                            <div className="flex justify-between items-start mb-1">
                              <p className="font-medium text-orange-800 flex items-center gap-2">
                                {dish.name}
                                {dish.is_vegetarian && <span className="text-green-600 text-xs">🌱 Végétarien</span>}
                              </p>
                              <span className="font-bold text-orange-700">{dish.price}€</span>
                            </div>
                            <div className="text-xs text-orange-500 mt-1">
                              <p className="mb-1">
                                <strong>Ingrédients:</strong> {dish.ingredients.map(ing => ing.name).join(', ')}
                              </p>
                              {dish.ingredients.some(ing => ing.is_allergen) && (
                                <p className="text-red-600">
                                  <strong>⚠️ Allergènes:</strong> {dish.ingredients.filter(ing => ing.is_allergen).map(ing => ing.allergen_type).join(', ')}
                                </p>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : !dishesError && (
                <div className="text-center py-8 text-orange-400">
                  <p>Aucun plat disponible</p>
                </div>
              )}
            </div>
          )}
          
          {/* Menu Section */}
          {activeSection === 'menu' && (
            <div className="mb-6 border-t border-orange-200 pt-4">
              <h3 className="text-xl font-semibold text-orange-700 mb-4">Notre Menu</h3>
              
              {menuError && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                  <p className="text-red-600 text-center">{menuError}</p>
                  <button
                    onClick={fetchMenu}
                    disabled={isLoadingMenu}
                    className="mt-2 bg-orange-100 hover:bg-orange-200 text-orange-700 py-2 px-4 rounded-lg transition-colors text-sm"
                  >
                    Réessayer
                  </button>
                </div>
              )}
              
              {isLoadingMenu ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500 mx-auto mb-4"></div>
                  <p className="text-orange-600">Chargement du menu...</p>
                </div>
              ) : menuData ? (
                <div className="space-y-6">
                  {menuData.categories && menuData.categories.map((category, catIndex) => (
                    <div key={catIndex} className="border border-orange-100 rounded-lg p-4">
                      <h4 className="font-medium text-orange-600 mb-3">{category.name}</h4>
                      <div className="space-y-3">
                        {category.items && category.items.map((item, itemIndex) => (
                          <div key={itemIndex} className="flex justify-between items-start">
                            <div>
                              <p className="font-medium text-orange-800">{item.name}</p>
                              <p className="text-sm text-orange-500">{item.description}</p>
                            </div>
                            <span className="font-bold text-orange-700">{item.price}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : !menuError && (
                <div className="text-center py-8 text-orange-400">
                  <p>Aucun menu disponible</p>
                </div>
              )}
            </div>
          )}
          
          {/* Reservation Form */}
          {activeSection === 'reservation' && (
            <div className="border-t border-orange-200 pt-4">
              <h3 className="text-xl font-semibold text-orange-700 mb-4">Réservation</h3>
              <form onSubmit={handleReservationSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="name" className="block text-sm font-medium text-orange-700 mb-1">Nom</label>
                    <input id="name" name="name" type="text" className="w-full p-2 border border-orange-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-300 text-gray-900" required />
                  </div>
                  <div>
                    <label htmlFor="phone" className="block text-sm font-medium text-orange-700 mb-1">Téléphone</label>
                    <input id="phone" name="phone" type="tel" className="w-full p-2 border border-orange-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-300 text-gray-900" required />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label htmlFor="date" className="block text-sm font-medium text-orange-700 mb-1">Date</label>
                    <input id="date" name="date" type="date" className="w-full p-2 border border-orange-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-300 text-gray-900" required />
                  </div>
                  <div>
                    <label htmlFor="time" className="block text-sm font-medium text-orange-700 mb-1">Heure</label>
                    <input id="time" name="time" type="time" className="w-full p-2 border border-orange-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-300 text-gray-900" required />
                  </div>
                  <div>
                    <label htmlFor="guests" className="block text-sm font-medium text-orange-700 mb-1">Personnes</label>
                    <input id="guests" name="guests" type="number" min="1" max="20" defaultValue="2" className="w-full p-2 border border-orange-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-300 text-gray-900" required />
                  </div>
                </div>
                <button type="submit" className="w-full bg-orange-500 hover:bg-orange-600 text-white py-3 px-4 rounded-lg transition-colors font-medium">
                  Confirmer Réservation
                </button>
              </form>
            </div>
          )}
        </main>
        
        {/* Performance Dashboard Link (Admin) */}
        <div className="fixed bottom-4 right-4">
          <button
            onClick={() => window.location.href = '/performance'}
            className="bg-orange-500 hover:bg-orange-600 text-white py-2 px-4 rounded-lg transition-colors flex items-center gap-2 text-sm font-medium shadow-lg"
            title="Performance Dashboard"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Performance</span>
          </button>
        </div>

        {/* Footer */}
        <footer className="text-center text-sm text-orange-500 py-4">
          <p>© {new Date().getFullYear()} Les Pieds dans le Plat. Tous droits réservés.</p>
        </footer>
      </div>
    </div>
  )
}