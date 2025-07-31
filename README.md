# HTTP Flow

A powerful HTTP traffic interceptor and modifier with real-time rule-based request/response manipulation. Built with FastAPI backend and React frontend for modern web development workflows.

## 🚀 Features

- **Real-time HTTP Traffic Monitoring** - See all HTTP requests and responses as they happen
- **Rule-based Interception** - Create sophisticated filters and modification rules
- **Request/Response Modification** - Add, modify, or delete headers and body content
- **Live Traffic Dashboard** - Modern React-based UI for traffic visualization
- **High Performance** - Built with FastAPI and optimized for minimal latency
- **Cross-platform** - Works on Windows, macOS, and Linux

## 📁 Project Structure

```
http-flow/
├── package.json                    # Node.js project configuration with unified scripts
├── pyproject.toml                  # Python project configuration
├── requirements.txt                # Python dependencies
├── vite.config.js                  # Vite configuration for frontend
├── tailwind.config.js              # Tailwind CSS configuration
├── main.py                         # Application entry point
├── backend/                        # Python backend
│   ├── main.py                     # FastAPI application
│   ├── models/                     # Data models and schemas
│   │   ├── base_models.py          # Core business models
│   │   └── *.py                    # Generated FlatBuffer models
│   ├── services/                   # Business logic services
│   │   ├── addon.py                # MitmProxy addon
│   │   ├── proxy.py                # Proxy management
│   │   ├── storage.py              # Database operations
│   │   └── ws.py                   # WebSocket management
│   ├── utils/                      # Utilities and helpers
│   │   └── flat_utils.py           # FlatBuffer utilities
│   └── tests/                      # Backend tests
├── frontend/                       # React frontend
│   ├── src/                        # Source code
│   │   ├── components/             # React components
│   │   ├── hooks/                  # Custom React hooks
│   │   ├── services/               # API and WebSocket services
│   │   ├── store/                  # State management (Zustand)
│   │   ├── models/                 # TypeScript interfaces
│   │   └── main.tsx                # React application entry
│   ├── public/                     # Static assets
│   └── tests/                      # Frontend tests
├── schema/                         # FlatBuffer schema definitions
└── scripts/                        # Build and utility scripts
    ├── dev.py                      # Development server launcher
    └── setup.py                    # Project setup script
```

## 🚀 Quick Start

### Prerequisites
- Node.js (v16 or higher)
- Python (3.8 or higher)
- npm or yarn

### Setup
```bash
# Option 1: Use setup script
python scripts/setup.py

# Option 2: Manual setup
npm install
pip install -r requirements.txt
```

### Development

Run both frontend and backend simultaneously:
```bash
npm run dev:full
```

Run individually:
```bash
# Frontend only (React dev server)
npm run dev

# Backend only (FastAPI server)
npm run dev:backend
```

### Testing

```bash
# Run all tests
npm run test:all

# Frontend tests only
npm run test

# Backend tests only
npm run test:backend
```

### Building

```bash
# Build frontend for production
npm run build

# Build backend (compile check)
npm run build:backend
```

## 📜 Available Scripts

### Development
- `npm run dev` - Start frontend development server
- `npm run dev:backend` - Start backend development server  
- `npm run dev:full` - Start both frontend and backend
- `python scripts/dev.py` - Alternative full development launcher

### Testing
- `npm run test` - Run frontend tests with Vitest
- `npm run test:ui` - Run frontend tests with UI
- `npm run test:coverage` - Run frontend tests with coverage
- `npm run test:backend` - Run backend tests with pytest
- `npm run test:all` - Run all tests

### Building & Linting
- `npm run build` - Build frontend for production
- `npm run build:backend` - Compile-check backend code
- `npm run lint` - Lint frontend code with ESLint
- `npm run lint:backend` - Lint backend code with flake8

### Maintenance
- `npm run clean` - Clean build artifacts
- `npm run setup` - Full project setup
- `npm run install:backend` - Install Python dependencies

## 🏗️ Architecture

### Backend (FastAPI + Python)
- **FastAPI**: Modern web framework for building APIs
- **MitmProxy**: HTTP/HTTPS proxy for traffic interception
- **WebSockets**: Real-time communication with frontend
- **SQLite**: Local database for persistence
- **FlatBuffers**: Efficient serialization

### Frontend (React + TypeScript)  
- **React**: Modern UI library with hooks
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tool and dev server
- **Tailwind CSS**: Utility-first CSS framework
- **Zustand**: Lightweight state management
- **Vitest**: Fast unit testing framework

## 🔧 Configuration

### Backend Configuration
- `config.yaml` - Application configuration
- `pyproject.toml` - Python project settings
- `pytest.ini` - Test configuration

### Frontend Configuration  
- `vite.config.js` - Vite bundler settings
- `tailwind.config.js` - Tailwind CSS customization
- `tsconfig.json` - TypeScript compiler options

## 🧪 Testing Strategy

### Backend Tests (`backend/tests/`)
- Unit tests with pytest
- Async test support
- Coverage reporting
- Integration tests for services

### Frontend Tests (`frontend/tests/`)
- Component tests with React Testing Library
- Custom hook tests
- Service layer tests
- Mock WebSocket and API calls

## 📦 Dependencies

### Python Dependencies
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `mitmproxy` - HTTP proxy
- `flatbuffers` - Serialization
- `python-dateutil` - Date utilities

### Node.js Dependencies
- `react` - UI library
- `typescript` - Type safety
- `vite` - Build tool
- `tailwindcss` - CSS framework
- `zustand` - State management
- `vitest` - Testing framework

## 🤝 Contributing

We welcome contributions from the community! HTTP Flow is designed to be a collaborative project where developers worldwide can contribute to making HTTP traffic management better for everyone.

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow the established project structure
4. Write tests for your changes
5. Ensure all tests pass
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Guidelines

- Follow Python PEP 8 style guidelines for backend code
- Use TypeScript and React best practices for frontend code
- Write unit tests for new functionality
- Update documentation as needed
- Keep commits atomic and well-described

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### Why MIT License?

We chose the MIT License to ensure maximum freedom and adoption:
- ✅ **Commercial Use**: Use HTTP Flow in your commercial projects
- ✅ **Modification**: Modify the code to suit your needs
- ✅ **Distribution**: Share and distribute freely
- ✅ **Private Use**: Use in private/internal projects
- ✅ **No Restrictions**: Minimal limitations on usage

## 🌟 Support the Project

If you find HTTP Flow useful, please:
- ⭐ Star this repository
- 🐛 Report bugs and suggest features
- 🔄 Share with your network
- 🤝 Contribute code or documentation

## 📞 Contact & Community

- **Issues**: [GitHub Issues](https://github.com/your-username/http-flow/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/http-flow/discussions)
- **Documentation**: [Wiki](https://github.com/your-username/http-flow/wiki)

---

**HTTP Flow** - Control Your HTTP Traffic 🚀
2. Write tests for new features
3. Use TypeScript for frontend code
4. Follow Python PEP 8 for backend code
5. Run `npm run test:all` before committing

## 📄 License

This project is licensed under the MIT License.
