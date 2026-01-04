# Voice-Enabled GenAI Restaurant Assistant - Docker Setup

## Quick Start

1. **Copy the environment file and configure it:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your `MISTRAL_API_KEY`.

2. **Build and start all services:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000
   - MongoDB: localhost:27017

## Commands

### Start services
```bash
docker-compose up
```

### Start in detached mode (background)
```bash
docker-compose up -d
```

### Stop services
```bash
docker-compose down
```

### View logs
```bash
docker-compose logs -f
```

### Rebuild after code changes
```bash
docker-compose up --build
```

### Remove volumes (fresh database)
```bash
docker-compose down -v
```

## Service Details

- **MongoDB**: Port 27017, data persisted in Docker volume
- **Backend**: Port 5000, Flask + SocketIO API
- **Frontend**: Port 3000, Next.js application

## Environment Variables

See `.env.example` for all available configuration options.
