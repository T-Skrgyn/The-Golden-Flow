# The Golden Flow

## Overview
The Golden Flow is a Python-based system that processes delivery orders by checking real-time weather conditions and flagging potential delays.

## Features
- Parallel API calls using asyncio
- Weather-based delay detection
- AI-generated apology messages
- Robust error handling for invalid cities
- Secure API key management using .env

## Tech Stack
- Python
- asyncio + aiohttp
- OpenWeatherMap API
- NVIDIA AI API

## Workflow
1. Load orders from JSON
2. Fetch weather data in parallel
3. Check conditions (Rain, Snow, Extreme)
4. Mark orders as delayed
5. Generate AI-based apology message
6. Save updated orders
