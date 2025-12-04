# 🎨 HR AI Assistant - Frontend

Premium React + TypeScript frontend for the RAG Chatbot system.

## ✨ Features

- 🎨 **Premium UI/UX** - Beautiful, modern interface with dark mode support
- ⚡ **Real-time Chat** - Instant responses with typing indicators
- 📚 **Source Citations** - View sources for AI answers with confidence scores
- 💾 **Chat History** - Persistent chat sessions with localStorage
- 👍 **Feedback System** - Rate responses as helpful/not helpful
- 📱 **Responsive Design** - Works perfectly on desktop, tablet, and mobile
- 🔒 **API Key Auth** - Secure authentication with backend
- ⚙️ **Session Management** - Automatic session tracking and history

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm/yarn/pnpm
- Backend API running on `http://localhost:8000`
- API key from backend

### Installation

```bash
# Navigate to frontend folder
cd frontend

# Install dependencies
npm install
# or
yarn install
# or
pnpm install
```

### Configuration

1. Create `.env` file from example:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API key:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_KEY=hr_rag_your_api_key_here
```

### Development

```bash
# Start development server
npm run dev

# Open browser at http://localhost:3000
```

### Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   └── ChatInterface.tsx      # Main chat component
│   ├── services/
│   │   ├── api.ts                 # Backend API service
│   │   └── storage.ts             # LocalStorage service
│   ├── types/
│   │   └── chat.ts                # TypeScript types
│   ├── App.tsx                    # Root component
│   ├── main.tsx                   # Entry point
│   └── index.css                  # Global styles
├── public/                        # Static assets
├── index.html                     # HTML template
├── package.json                   # Dependencies
├── vite.config.ts                 # Vite config
├── tailwind.config.js             # Tailwind CSS config
└── tsconfig.json                  # TypeScript config
```

## 🎯 Features Explained

### Chat Interface

- **Message Display**: Beautiful message bubbles with user/assistant avatars
- **Thinking Indicator**: Animated dots while AI is processing
- **Source Cards**: Expandable source citations with scores
- **Markdown Support**: Properly formatted code blocks and text

### Sidebar

- **Chat History**: View all previous conversations
- **Session Management**: Switch between different chat sessions
- **Delete Chats**: Remove unwanted conversations
- **New Chat**: Start fresh conversations instantly

### Feedback System

- **Thumbs Up/Down**: Rate answer quality
- **Copy Response**: Copy AI answers to clipboard
- **Auto-Submit**: Feedback sent automatically to backend

### State Management

- **LocalStorage**: Chat history persists across browser sessions
- **Session IDs**: Unique session tracking for conversation context
- **Auto-Save**: Messages saved automatically after each exchange

## 🔧 API Integration

### Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/chat` | POST | Send message and get AI response |
| `/feedback` | POST | Submit feedback on answers |
| `/health` | GET | Check backend status |
| `/usage` | GET | Get usage statistics |

### Request Format

```typescript
// Chat request
{
  query: "How to add employee?",
  session_id: "session_123",
  max_iterations: 3
}

// Feedback request
{
  query: "original question",
  answer: "AI response",
  rating: 5,
  helpful: true,
  comment: "optional comment"
}
```

### Response Format

```typescript
// Chat response
{
  answer: "Navigate to...",
  sources: [{
    question: "...",
    answer: "...",
    metadata: {...},
    score: 0.95
  }],
  confidence: 0.92,
  iterations: 2,
  session_id: "session_123"
}
```

## 🎨 Styling

### Tailwind CSS

- Utility-first CSS framework
- Dark mode support with `dark:` prefix
- Responsive design with `md:`, `lg:` prefixes
- Custom animations for thinking indicator

### Color Scheme

- **Primary**: Blue (#3B82F6)
- **Secondary**: Purple (#9333EA)
- **Success**: Green (#22C55E)
- **Error**: Red (#EF4444)
- **Background (Light)**: White, Gray-50, Gray-100
- **Background (Dark)**: Gray-950, Gray-900, Gray-800

## 🔒 Security

- **API Keys**: Stored in environment variables (never committed)
- **CORS**: Backend configured for frontend origin
- **Rate Limiting**: Handled by backend
- **Input Validation**: Client-side validation before API calls

## 📱 Responsive Design

### Breakpoints

- **Mobile**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

### Mobile Features

- Collapsible sidebar with overlay
- Touch-friendly buttons (44px minimum)
- Optimized font sizes
- Swipe gestures (coming soon)

## 🚀 Performance

### Optimizations

- **Code Splitting**: Vite automatic code splitting
- **Tree Shaking**: Unused code removed in production
- **Lazy Loading**: Components loaded on demand
- **Image Optimization**: Compressed assets
- **Caching**: API responses cached when appropriate

### Bundle Size

- Main bundle: ~150KB (gzipped)
- Vendor bundle: ~200KB (gzipped)
- Total initial load: ~350KB

## 🧪 Testing

```bash
# Run tests (when implemented)
npm run test

# Run linter
npm run lint
```

## 📦 Deployment

### Static Hosting (Recommended)

```bash
# Build production bundle
npm run build

# Deploy to Vercel
vercel deploy

# Or Netlify
netlify deploy --prod

# Or any static hosting service
```

### Docker

```bash
# Build Docker image
docker build -t rag-frontend .

# Run container
docker run -p 3000:80 rag-frontend
```

### Environment Variables for Production

```env
VITE_API_BASE_URL=https://api.yourdomain.com
VITE_API_KEY=production_api_key_here
```

## 🐛 Troubleshooting

### Common Issues

**"Cannot connect to backend"**
- Check if backend is running on port 8000
- Verify API_BASE_URL in .env
- Check CORS settings in backend

**"Invalid API key"**
- Generate new API key from backend
- Update VITE_API_KEY in .env
- Restart dev server after .env changes

**"Rate limit exceeded"**
- Wait 60 seconds before retrying
- Check backend rate limit settings
- Verify you're not making too many requests

**"Chat history not saving"**
- Check browser localStorage permissions
- Clear browser cache and try again
- Check browser console for errors

## 📚 Documentation

- **Backend API**: See `/workspace/PRODUCTION_ARCHITECTURE.md`
- **Security**: See `/workspace/SECURITY_IMPLEMENTATION_COMPLETE.md`
- **Deployment**: See `/workspace/DEPLOY_NOW.md`

## 🤝 Contributing

1. Follow TypeScript best practices
2. Use Tailwind CSS for styling (no custom CSS unless necessary)
3. Keep components small and focused
4. Add proper TypeScript types
5. Test on multiple browsers and devices

## 📄 License

Same as the main project.

---

**Built with ❤️ using React + TypeScript + Vite + Tailwind CSS**
