# Restaurant Assistant API

This is the Flask API that connects the frontend with the agent system and database.

## Overview

The API provides RESTful endpoints for the Voice-Enabled GenAI Restaurant Assistant. It integrates:

- **Agent System**: For intelligent query processing
- **MongoDB**: For data storage (with mock fallback)
- **Mistral LLM**: For natural language responses
- **Frontend**: Via REST API endpoints

## API Endpoints

### Base URL
```
http://localhost:5000
```

### Endpoints

#### GET `/`
**Home endpoint**
Returns API information and available endpoints

**Response:**
```json
{
  "status": "running",
  "service": "Restaurant Assistant API",
  "version": "1.0.0",
  "endpoints": ["/query", "/menu", "/dishes", "/reservations", "/info"]
}
```

#### POST `/query`
**Handle user queries**
Processes both text and audio queries through the agent system

**Request:**
```json
{
  "query": "user message"
}
```

**Response:**
```json
{
  "response": "agent response",
  "agent_processing": true,
  "history": [
    {
      "role": "user",
      "content": "user message",
      "timestamp": "ISO timestamp"
    },
    {
      "role": "assistant",
      "content": "agent response",
      "timestamp": "ISO timestamp"
    }
  ],
  "timestamp": "ISO timestamp"
}
```

#### GET `/menu`
**Get restaurant menu**
Returns the complete restaurant menu with categories

**Response:**
```json
{
  "categories": [
    {
      "name": "Entrées",
      "items": [
        {
          "name": "Terrine de campagne",
          "price": "12€",
          "description": "Maison avec pain grillé",
          "available": true
        }
      ]
    }
  ]
}
```

#### GET `/dishes`
**Get all dishes by category**
Returns dishes grouped by category with detailed information

**Response:**
```json
{
  "Entrées": [
    {
      "_id": "dish_id",
      "name": "Terrine de campagne",
      "category": "Entrées",
      "ingredients": [],
      "is_vegetarian": false,
      "price": 12.0
    }
  ]
}
```

#### POST `/reservations`
**Create a new reservation**
Creates a reservation in the database

**Request:**
```json
{
  "name": "John Doe",
  "phone": "+33 6 00 00 00 00",
  "date": "2023-12-01",
  "time": "19:00",
  "guests": 2,
  "specialRequests": "Window seat"
}
```

**Response:**
```json
{
  "success": true,
  "reservation": {
    "name": "John Doe",
    "phone": "+33 6 00 00 00 00",
    "date": "2023-12-01",
    "time": "19:00",
    "guests": 2,
    "specialRequests": "Window seat",
    "createdAt": "ISO timestamp",
    "updatedAt": "ISO timestamp",
    "status": "confirmed"
  }
}
```

#### GET `/info`
**Get restaurant information**
Returns basic restaurant information

**Response:**
```json
{
  "name": "Les Pieds dans le Plat",
  "address": "1 Avenue des Champs-Élysées, 75008 Paris, France",
  "phone": "+33 1 23 45 67 89",
  "openingHours": "11:00 AM - 01:00 AM",
  "description": "Restaurant description"
}
```

#### GET `/health`
**Health check**
Returns API health status

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "ISO timestamp",
  "database": "connected" or "mock",
  "llm": "connected" or "mock"
}
```

#### POST `/reset`
**Reset conversation history**
Clears the agent's conversation history

**Response:**
```json
{
  "success": true,
  "message": "Conversation history reset"
}
```

## Frontend Integration

The API is designed to work with the frontend located in `front/resto-ai-voice/`.

### Example Usage

```javascript
// Send text message
const response = await axios.post('http://localhost:5000/query', {
  query: "Bonjour, je voudrais voir le menu"
});

// Get menu
const menu = await axios.get('http://localhost:5000/menu');

// Create reservation
const reservation = await axios.post('http://localhost:5000/reservations', {
  name: "John Doe",
  phone: "+33 6 00 00 00 00",
  date: "2023-12-01",
  time: "19:00",
  guests: 2
});
```

## Configuration

### Environment Variables

Create a `.env` file in the `back/src` directory:

```env
# API Configuration
PORT=5000

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=restaurant_assistant

# Mistral LLM Configuration
MISTRAL_API_KEY=your_api_key_here
```

### Dependencies

```bash
pip install flask flask-cors
```

## Running the API

### Development

```bash
cd back/src
python run/app.py
```

### Production

```bash
cd back/src
export FLASK_ENV=production
export PORT=5000
python run/app.py
```

## Testing

Run the test script:

```bash
cd back/src
python test_api.py
```

## Features

- **CORS Support**: Enabled for all origins
- **Error Handling**: Comprehensive error handling
- **Mock Data**: Falls back to mock data if database not available
- **Agent Integration**: Full integration with the restaurant agent system
- **Conversation History**: Maintains conversation context

## Architecture

```
Frontend → Flask API → Restaurant Agent → LLM/MongoDB → Response → Frontend
```

## Error Handling

The API handles errors gracefully and returns appropriate HTTP status codes:

- `200 OK`: Success
- `400 Bad Request`: Missing or invalid parameters
- `404 Not Found`: Endpoint not found
- `500 Internal Server Error`: Server-side errors

## Future Enhancements

- Add authentication for reservations
- Implement rate limiting
- Add more sophisticated error recovery
- Support for audio file uploads
- WebSocket support for real-time updates

The API is fully functional and ready to integrate with the frontend application.