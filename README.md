# 🤖 WhatsApp AI Bot - Educational Support System

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-0.1.0-green.svg)](https://langchain.com/)
[![FAISS](https://img.shields.io/badge/FAISS-1.7.4-orange.svg)](https://github.com/facebookresearch/faiss)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An intelligent WhatsApp automation bot powered by **LangChain**, **FAISS vector store**, and **GPT-4** for providing 24/7 educational support to university students.

---

## 🌟 Features

### 🧠 **AI-Powered Responses**
- **RAG (Retrieval-Augmented Generation)** using LangChain + FAISS
- Semantic search over FAQ database with document chunking
- Context-aware responses using GPT-4
- Confidence scoring for answer quality

### 💬 **Multi-Modal Support**
- ✅ Text messages (FAQ, student queries)
- 📷 Image processing (OCR, remittance detection)
- 📄 Document handling (PDF, DOCX, PPTX)
- 🎨 Non-text content (emojis, GIFs, stickers)

### 📊 **Student-Specific Features**
- Invoice/fee inquiries from database
- Academic data retrieval (courses, grades)
- Personalized salutations
- Conversation history tracking

### 🔄 **Automation**
- Selenium-based WhatsApp Web automation
- Multi-bot management
- Automatic unread message processing
- Task creation in TConnect system

---

## 🏗️ Architecture

```
┌─────────────────┐
│  WhatsApp Web   │
└────────┬────────┘
         │ Selenium
┌────────▼────────────────────────────────────┐
│          Bot Manager Layer                  │
│  - Message Processing                       │
│  - Media Extraction                         │
└────────┬────────────────────────────────────┘
         │
┌────────▼────────────────────────────────────┐
│          RAG Engine (LangChain)             │
│  - Document Chunking                        │
│  - FAISS Vector Store                       │
│  - Similarity Search                        │
│  - RetrievalQA Chain                        │
└────────┬────────────────────────────────────┘
         │
┌────────▼────────────────────────────────────┐
│          LLM (GPT-4o-mini)                  │
│  - Answer Generation                        │
│  - Context Understanding                    │
└────────┬────────────────────────────────────┘
         │
┌────────▼────────────────────────────────────┐
│          Database & Logging                 │
│  - Student Data                             │
│  - Conversation Logs                        │
└─────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- MySQL database
- OpenAI API key
- Chrome browser + ChromeDriver
- WhatsApp account

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-org/whatsapp-ai-bot.git
cd whatsapp-ai-bot

# 2. Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment variables
cp .env.example .env
# Edit .env with your credentials

# 5. Setup database
mysql -u root -p < database/schema.sql

# 6. Build FAISS index
python scripts/build_faiss_index.py build

# 7. Run the bot
python main.py
```

---

## ⚙️ Configuration

### Environment Variables (`.env`)

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini

# Database
DB_HOST=localhost
DB_NAME=whatsapp_bot_db
DB_USER=your_user
DB_PASSWORD=your_password

# WhatsApp
CHROME_DRIVER_PATH=C:/chromedriver/chromedriver.exe
BOT_1_USER_DATA_PATH=C:/WhatsApp_UserData/Bot1

# RAG Settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
SIMILARITY_THRESHOLD=0.65
```

### FAQ Database Format

Create `data/faq_database.csv`:

```csv
Question,Answer,Category,Interface
How do I reset my password?,Go to Settings > Security > Reset Password,Technical,CMS
What is the fee structure?,Visit CMS portal > Finance > Fee Details,Finance,CMS
How to submit assignment?,Login to LMS > Course > Assignment Upload,Academic,LMS
```

---

## 📖 Usage

### Starting the Bot

```bash
# Start with default configuration
python main.py

# Enable debug mode
LOG_LEVEL=DEBUG python main.py
```

### Building/Updating FAISS Index

```bash
# Initial build
python scripts/build_faiss_index.py build

# Update with new FAQs
python scripts/build_faiss_index.py update
```

### Testing RAG Engine

```python
from src.rag.rag_engine import get_rag_engine

rag = get_rag_engine()
rag.load_vector_store()

answer, confidence, sources = rag.query(
    "How do I check my fees?",
    salutation="Student"
)

print(f"Answer: {answer}")
print(f"Confidence: {confidence}")
print(f"Sources: {sources}")
```

---

## 🗂️ Project Structure

```
whatsapp-ai-bot/
├── main.py                      # Entry point
├── requirements.txt             # Dependencies
├── .env.example                 # Environment template
│
├── src/
│   ├── bot/                     # Bot automation
│   │   ├── bot_manager.py
│   │   ├── message_processor.py
│   │   └── whatsapp_automation.py
│   │
│   ├── rag/                     # RAG implementation
│   │   ├── rag_engine.py        # LangChain + FAISS
│   │   └── document_loader.py
│   │
│   ├── database/                # Database layer
│   │   ├── db_manager.py
│   │   └── student_repository.py
│   │
│   ├── media/                   # Media processing
│   │   ├── image_processor.py
│   │   └── pdf_processor.py
│   │
│   └── utils/                   # Utilities
│       ├── logger.py
│       └── message_helpers.py
│
├── data/
│   ├── faq_database.csv         # FAQ source
│   └── faiss_index/             # Vector store
│
└── scripts/
    └── build_faiss_index.py     # Index builder
```

---

## 🧪 Testing

```bash
# Run unit tests
pytest tests/

# Run specific test
pytest tests/test_rag_engine.py -v

# With coverage
pytest --cov=src tests/
```

---

## 📊 Monitoring

### Bot Logs

```bash
# View logs
tail -f logs/bot_primary.log

# Error logs
tail -f logs/error.log
```

### Database Queries

```sql
-- Recent conversations
SELECT * FROM AI_Conversation_Log 
ORDER BY Timestamp DESC 
LIMIT 10;

-- Bot performance
SELECT 
    BotName,
    AVG(ConfidenceLevel) as avg_confidence,
    COUNT(*) as total_messages
FROM AI_Conversation_Log
GROUP BY BotName;
```

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

---

## 👥 Authors

- **Your Name** - *Initial work* - [YourGitHub](https://github.com/yourusername)

---

## 🙏 Acknowledgments

- [LangChain](https://langchain.com/) for RAG framework
- [FAISS](https://github.com/facebookresearch/faiss) for vector search
- [OpenAI](https://openai.com/) for GPT models
- [Selenium](https://www.selenium.dev/) for automation

---

## 📧 Support

For support, email latha.r@texila.org or open an issue.

---

## 🔮 Roadmap

- [ ] Add voice message support
- [ ] Implement multi-language support
- [ ] Create web dashboard for analytics
- [ ] Add A/B testing for responses
- [ ] Integrate with more LMS platforms

---

**Made with ❤️ for Texila American University Students**
