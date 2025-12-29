# PokerPro - Professional Poker Training Platform

A comprehensive poker training application that guides players from beginner to professional level through structured learning, GTO training, AI opponents, hand analysis, and mental game development.

## 🎯 Features

- **Personalized Onboarding** - Skill assessment and customized learning paths
- **Structured Academy** - Theory, strategy, and pro-level content
- **GTO Engine** - Interactive solver with range visualization
- **AI Opponents** - Practice against different player types
- **Hand Analyzer** - Import and analyze your hands with leak detection
- **Bankroll Management** - Track bankroll and get stake recommendations
- **Mental Game** - Tilt detection and mental performance tracking
- **Progress Tracking** - KPIs, trends, and objective feedback
- **Challenges & Certifications** - Prove your skill level
- **AI Coach** - Get personalized advice and answers

## 🛠️ Tech Stack

### Backend
- **Python 3.11+** with FastAPI
- **PostgreSQL** - Database
- **Redis** - Caching and sessions
- **SQLAlchemy** - ORM
- **Alembic** - Database migrations
- **Pydantic** - Data validation

### Frontend (Web)
- **React 18** with TypeScript
- **Vite** - Build tool
- **React Router** - Navigation
- **Zustand** - State management
- **TailwindCSS** - Styling
- **Axios** - API calls

## 📁 Project Structure

```
pokerpro/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── database.py             # Database connection
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   ├── api/                    # API endpoints
│   ├── gto/                    # GTO engine
│   ├── ai/                     # AI models
│   ├── academy/                # Learning content
│   ├── hand_parser/            # Hand history parser
│   └── bankroll/               # Bankroll management
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── screens/            # Page components
│   │   ├── services/           # API services
│   │   ├── store/              # State management
│   │   └── App.tsx             # Main app component
│   └── public/
├── docker-compose.yml
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 7+

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
alembic upgrade head

# Run development server
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Docker Setup (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📚 API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📖 Development Roadmap

### Phase 1: MVP (Current)
- [x] Project setup
- [ ] User authentication
- [ ] Basic onboarding
- [ ] Simple academy (5-10 lessons)
- [ ] Preflop GTO ranges
- [ ] Basic hand parser
- [ ] Minimal frontend

### Phase 2: Core Features
- [ ] Postflop GTO solver
- [ ] Interactive practice mode
- [ ] Hand analyzer ML
- [ ] AI opponents
- [ ] Bankroll management
- [ ] Progress tracking

### Phase 3: Advanced Features
- [ ] Mental game module
- [ ] AI coach chatbot
- [ ] Challenge system
- [ ] Certifications
- [ ] Community features

### Phase 4: Polish & Launch
- [ ] UI/UX refinement
- [ ] Performance optimization
- [ ] Beta testing
- [ ] Production deployment

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please read CONTRIBUTING.md for details.

## 📧 Contact

For questions or support, please open an issue on GitHub.
