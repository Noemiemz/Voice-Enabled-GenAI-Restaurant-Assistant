# Project description
This project aims to develop a voice-interactive Generative AI assistant that acts as a virtual receptionist for a restaurant. The system should be capable of engaging in natural two-way spoken conversations with customers, understanding their voice queries, interpreting intent, and responding with generated speech in real time.

The assistant will handle multiple receptionist-style tasks such as:

- Table reservations: taking booking details (name, date, time, number of guests) and confirming availability.
- Order handling: taking take-away or delivery orders, confirming menu items, and repeating orders for validation.
- Menu information: answering questions about dishes, ingredients, allergens, or promotions.
- General inquiries: providing restaurant location, opening hours, or special offers.

The result will be a fully voice-driven AI receptionist that simulates a real conversational restaurant assistant, capable of operating offline (using local models via Ollama) or online (using APIs such as Google AI SDK).

# Steps
- [ ] TTS
- [ ] STT
- [ ] LLM for intent recognition and response generation
  - [ ] faire gaffe à l'historique des conversations
- [ ] Integrate components for two-way voice conversation

# Brainstorm
**Local** vs **cloud models** (API) ?
- _Local models_ (Ollama)
	- **Pros**: Privacy, offline capability, no API costs
    - **Cons**: Limited model size, latency, hardware requirements
- _Cloud models_ (Mistral, OpenAI)
    - **Pros**: State-of-the-art performance, scalability, easy updates
    - **Cons**: Privacy concerns, latency, ongoing costs
--> on part plutot sur du cloud pour l'instant

Databases ? 
- **PostgreSQL** or **MongoDB** ?
	- mongo pratique : json
	- postgreSQL 
--> **MongoDB**

Models ? 
- TTS (Kokoro (local ou peut etre hugging face faut voir) / ElevenLabs)
- STT / ASR (whisper, Voxstral)
- LLM for intent recognition and response generation (Google, Mistral ou quoi + LangChain)


## List tables : 

- Plat (entree plat ...)
	- name
	- type (entree, plat, boisson ou dessert)
	- ingredients (_cacahuète_)
		- isAllergen
		- nameAllergen (_Arrachides_)
	- price
- Menu
	- List [Plats]
	- reduction (en %)
- Table a manger
	- nb seats
	- List [Reservations]
	- location (close to the window, outside ...)
- Reservation (sur place)
	- id
	- date
	- name client
	- nb person
	- [Table a manger] (id)
- Order (take away)
	- id
	- name client
	- address for delivery
	- phone number
	- List [Menu]
	- List [Plat]

# Milestones
- Chat with a fake assistant
	- record voice
	- send voice to STT into LLM into TTS 
    	- avoir un LLM de fou, avec un vrai prompt
	- play new voice
- Connect to database (MCP)
	- make reservations
	- see availability
	- see menu
		- allergens
		- ingredients
		- prices

