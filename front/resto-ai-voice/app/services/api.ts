import axios from 'axios'

// Base URL for the backend API
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'

export interface Message {
  role: string
  content: string
  timestamp?: string
}

export type ConversationHistory = Message[];

export interface Ingredient {
  name: string
  is_allergen: boolean
  allergen_type: string | null
}

export interface Dish {
  _id: string
  name: string
  category: string
  ingredients: Ingredient[]
  is_vegetarian: boolean
  price: number
}

export interface DishesByCategory {
  [category: string]: Dish[]
}

class RestaurantAPI {
  private static instance: RestaurantAPI
  
  private constructor() {}
  
  public static getInstance(): RestaurantAPI {
    if (!RestaurantAPI.instance) {
      RestaurantAPI.instance = new RestaurantAPI()
    }
    return RestaurantAPI.instance
  }
  
  // Send audio recording to backend for speech-to-text and processing
  async sendAudioRecording(audioBlob: Blob): Promise<{textResponse: string, history: ConversationHistory}> {
    try {
      // Note: The current backend doesn't have audio processing endpoint
      // For now, we'll simulate this by sending a text query
      // In production, you would need to add audio processing to the backend
      
      const response = await axios.post(`${API_BASE_URL}/query`, {
        query: "[Audio recording received - please describe what you heard]"
      })
      
      return {
        textResponse: response.data.response,
        history: response.data.agent_processing ? [
          { role: 'user', content: '[Audio recording]' },
          { role: 'assistant', content: response.data.response }
        ] : []
      }
    } catch (error) {
      console.error('Error sending audio to backend:', error)
      throw error
    }
  }
  
  // Send text message to backend
  async sendTextMessage(message: string, history: ConversationHistory = []): Promise<{textResponse: string, history: ConversationHistory}> {
    try {
      const response = await axios.post(`${API_BASE_URL}/query`, {
        query: message
      })
      
      return {
        textResponse: response.data.response,
        history: [
          { role: 'user', content: message },
          { role: 'assistant', content: response.data.response }
        ]
      }
    } catch (error) {
      console.error('Error sending message to backend:', error)
      throw error
    }
  }
  
  // Get restaurant menu
  async getMenu(): Promise<{
    categories: Array<{
      name: string;
      items: Array<{
        name: string;
        price: string;
        description: string;
      }>;
    }>;
  }> {
    try {
      const response = await axios.get(`${API_BASE_URL}/menu`)
      return response.data
    } catch (error) {
      console.error('Error fetching menu:', error)
      throw error
    }
  }

  // Get dishes grouped by category
  async getDishes(): Promise<DishesByCategory> {
    try {
      const response = await axios.get(`${API_BASE_URL}/dishes`)
      return response.data
    } catch (error) {
      console.error('Error fetching dishes:', error)
      throw error
    }
  }
  
  // Create reservation
  async createReservation(reservationData: {
    name: string
    phone: string
    date: string
    time: string
    guests: number
    specialRequests?: string
  }): Promise<{
    success: boolean;
    reservation?: {
      name: string;
      phone: string;
      date: string;
      time: string;
      guests: number;
      specialRequests?: string;
      createdAt: string;
      updatedAt: string;
      status: string;
    };
  }> {
    try {
      const response = await axios.post(`${API_BASE_URL}/reservations`, reservationData)
      return response.data
    } catch (error) {
      console.error('Error creating reservation:', error)
      throw error
    }
  }
  
  // Get restaurant information
  async getRestaurantInfo(): Promise<{
    name: string
    address: string
    phone: string
    openingHours: string
    description: string
  }> {
    try {
      const response = await axios.get(`${API_BASE_URL}/info`)
      return response.data
    } catch (error) {
      console.error('Error fetching restaurant info:', error)
      throw error
    }
  }
}

export default RestaurantAPI.getInstance()