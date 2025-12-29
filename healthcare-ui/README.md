# Healthcare UI - React + Vite

Modern chatbot interface for Healthcare Bridge with beautiful, responsive design.

## Run Development Server

```bash
npm run dev
```

Runs on http://localhost:3000

## Build for Production

```bash
npm run build
npm run preview
```

## Features

- **Flexible Input**: Auto-expanding textarea (up to 150px height)
- **Smart Bubbles**: Message width adapts to content
- **Markdown Support**: ReactMarkdown for formatting AI responses
- **Loading States**: Typing indicator while AI responds
- **Gradient Design**: Modern purple gradient background
- **Responsive**: Works on desktop and mobile

## Configuration

All configuration is managed via `.env` file:

```bash
VITE_API_URL=http://127.0.0.1:8000
VITE_APP_NAME=Healthcare Bridge
VITE_APP_SUBTITLE=Assistente Cure Domiciliari
```

**Setup**: Copy `.env.example` to `.env` and update the values as needed.

**Note**: In Vite, all environment variables must be prefixed with `VITE_` to be accessible in the browser.

Additional configuration:
- Port configured in `vite.config.js` (port 3000)
- Styles in `src/Chatbot.css`

## Key Components

- **Chatbot.jsx**: Main chatbot logic and UI
- **Chatbot.css**: All styles for messages, input, header
- **App.jsx**: Simple wrapper component
- **main.jsx**: React entry point

See main README.md for full setup instructions.
