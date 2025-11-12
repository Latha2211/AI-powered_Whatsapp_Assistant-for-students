# 📘 Setup Guide - WhatsApp AI Bot

Complete step-by-step guide to set up the WhatsApp AI Bot with RAG capabilities.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [System Requirements](#system-requirements)
3. [Installation Steps](#installation-steps)
4. [Database Setup](#database-setup)
5. [FAQ Configuration](#faq-configuration)
6. [FAISS Index Creation](#faiss-index-creation)
7. [WhatsApp Setup](#whatsapp-setup)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)

---

## 🔧 Prerequisites

### Required Software

- **Python 3.9+** - [Download](https://www.python.org/downloads/)
- **MySQL 8.0+** - [Download](https://dev.mysql.com/downloads/)
- **Chrome Browser** - [Download](https://www.google.com/chrome/)
- **ChromeDriver** - [Download](https://chromedriver.chromium.org/)
- **Git** - [Download](https://git-scm.com/downloads)

### Required Accounts

- **OpenAI Account** - [Sign up](https://platform.openai.com/)
- **WhatsApp** - Active phone number
- **Database** - MySQL server access

---

## 💻 System Requirements

### Minimum
- **OS**: Windows 10, Linux (Ubuntu 20.04+), macOS 11+
- **RAM**: 4GB
- **Storage**: 2GB free space
- **Internet**: Stable connection

### Recommended
- **OS**: Windows 11, Ubuntu 22.04, macOS 13+
- **RAM**: 8GB+
- **Storage**: 10GB free space
- **CPU**: 4+ cores

---

## 📦 Installation Steps

### Step 1: Clone Repository

```bash
git clone https://github.com/your-org/whatsapp-ai-bot.git
cd whatsapp-ai-bot
```

### Step 2: Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Verify installation
pip list
```

### Step 4: Setup Environment Variables

```bash
# Copy template
cp .env.example .env

# Edit .env (use your preferred editor)
nano .env  # Linux/Mac
notepad .env  # Windows
```

**Required Variables:**

```bash
# OpenAI
OPENAI_API_KEY=sk-your-actual-api-key-here

# Database
DB_HOST=localhost
DB_PORT=3306
DB_NAME=whatsapp_bot_db
DB_USER=root
DB_PASSWORD=your-mysql-password

# Chrome Driver
CHROME_DRIVER_PATH=C:/chromedriver/chromedriver.exe  # Windows
# CHROME_DRIVER_PATH=/usr/local/bin/chromedriver  # Linux/Mac

# Bot Config
BOT_1_USER_DATA_PATH=C:/WhatsApp_UserData/Bot1
```

---

## 🗄️ Database Setup

### Step 1: Create Database

```sql
-- Login to MySQL
mysql -u root -p

-- Create database
CREATE DATABASE whatsapp_bot_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Use database
USE whatsapp_bot_db;
```

### Step 2: Create Tables

**Student Details Table:**
```sql
CREATE TABLE Student_Details (
    ApplicationNumber VARCHAR(50) PRIMARY KEY,
    Salutation VARCHAR(10),
    FullName VARCHAR(255),
    ContactNumber VARCHAR(20),
    Email VARCHAR(255),
    ProgramName VARCHAR(255),
    Status VARCHAR(50),
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Invoice Table:**
```sql
CREATE TABLE Invoice_Line (
    InvoiceID INT AUTO_INCREMENT PRIMARY KEY,
    application_No VARCHAR(50),
    InvoiceNumber VARCHAR(50),
    InvoiceDate DATE,
    TotalAmount DECIMAL(10,2),
    PaidAmount DECIMAL(10,2),
    BalanceAmount DECIMAL(10,2),
    DueDate DATE,
    Status VARCHAR(50),
    PaymentMethod VARCHAR(50),
    FOREIGN KEY (application_No) REFERENCES Student_Details(ApplicationNumber)
);
```

**Academic Details Table:**
```sql
CREATE TABLE Student_Academic_Details (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    Application_Number VARCHAR(50),
    CourseName VARCHAR(255),
    CourseCode VARCHAR(50),
    EnrollmentDate DATE,
    Status VARCHAR(50),
    Grade VARCHAR(10),
    Credits INT,
    Mentor VARCHAR(255),
    FOREIGN KEY (Application_Number) REFERENCES Student_Details(ApplicationNumber)
);
```

**Conversation Log Table:**
```sql
CREATE TABLE AI_Conversation_Log (
    LogID INT AUTO_INCREMENT PRIMARY KEY,
    ContactID VARCHAR(50),
    WhatsAppName VARCHAR(255),
    ReceivedMessage TEXT,
    ResponseFromBot TEXT,
    MessageType VARCHAR(50),
    MediaType VARCHAR(50),
    Category VARCHAR(50),
    ConfidenceLevel FLOAT,
    FAQQuestion TEXT,
    BotName VARCHAR(50),
    Timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_contact (ContactID),
    INDEX idx_timestamp (Timestamp)
);
```

### Step 3: Insert Sample Data

```sql
-- Sample student
INSERT INTO Student_Details VALUES 
('APP001', 'Mr.', 'John Doe', '+919876543210', 'john@example.com', 'MBA', 'Active', NOW());

-- Sample invoice
INSERT INTO Invoice_Line (application_No, InvoiceNumber, InvoiceDate, TotalAmount, PaidAmount, BalanceAmount, DueDate, Status) VALUES
('APP001', 'INV001', '2024-01-01', 5000.00, 2000.00, 3000.00, '2024-12-31', 'Partial');

-- Sample academic record
INSERT INTO Student_Academic_Details (Application_Number, CourseName, CourseCode, EnrollmentDate, Status, Grade, Credits, Mentor) VALUES
('APP001', 'Business Analytics', 'MBA101', '2024-01-15', 'In Progress', 'A', 4, 'Dr. Smith');
```

---

## 📚 FAQ Configuration

### Step 1: Create FAQ CSV

Create `data/faq_database.csv`:

```csv
Question,Answer,Category,Interface
How do I reset my password?,Go to Settings > Security > Reset Password. Click 'Forgot Password' and follow email instructions.,Technical,CMS
What is the fee structure?,"Tuition: $5000/semester, Registration: $200, Books: $300. Total per semester: $5500",Finance,CMS
How to submit assignment?,Login to LMS > Select Course > Assignments > Upload File > Submit,Academic,LMS
Who is my academic mentor?,Check CMS > Academic > My Mentor section for assigned mentor details,Academic,CMS
How to download study materials?,LMS > Course > Resources > Download Materials,Academic,LMS
```

### Step 2: Validate FAQ Format

```python
import pandas as pd

df = pd.read_csv('data/faq_database.csv')
print(df.head())
print(f"\nTotal FAQs: {len(df)}")
print(f"Categories: {df['Category'].unique()}")
```

---

## 🔍 FAISS Index Creation

### Step 1: Verify OpenAI API

```python
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Test API
response = client.embeddings.create(
    model="text-embedding-3-small",
    input="Test embedding"
)
print("✅ OpenAI API working!")
```

### Step 2: Build FAISS Index

```bash
python scripts/build_faiss_index.py build
```

**Expected Output:**
```
============================================================
FAISS Index Builder
WhatsApp AI Bot - Texila American University
============================================================

INFO - Loading FAQ data from: data/faq_database.csv
INFO - Loaded 50 FAQ entries
INFO - Initializing RAG engine...
INFO - Loading and chunking documents...
INFO - Created 75 document chunks
INFO - Creating FAISS vector store...
INFO - FAISS index created successfully!
INFO - Index saved to: data/faiss_index
```

### Step 3: Test Index

```python
from src.rag.rag_engine import get_rag_engine

rag = get_rag_engine()
rag.load_vector_store()

# Test query
answer, confidence, sources = rag.query(
    "How do I reset my password?",
    salutation="Student"
)

print(f"Answer: {answer}")
print(f"Confidence: {confidence:.2f}")
print(f"Sources: {sources}")
```

---

## 📱 WhatsApp Setup

### Step 1: Setup Chrome User Data Directory

```bash
# Windows
mkdir C:\WhatsApp_UserData\Bot1

# Linux/Mac
mkdir -p ~/WhatsApp_UserData/Bot1
```

### Step 2: ChromeDriver Setup

**Windows:**
1. Download ChromeDriver matching your Chrome version
2. Extract to `C:\chromedriver\`
3. Update `.env`: `CHROME_DRIVER_PATH=C:/chromedriver/chromedriver.exe`

**Linux:**
```bash
# Install ChromeDriver
sudo apt-get update
sudo apt-get install chromium-chromedriver

# Update .env
CHROME_DRIVER_PATH=/usr/bin/chromedriver
```

**Mac:**
```bash
# Install via Homebrew
brew install chromedriver

# Update .env
CHROME_DRIVER_PATH=/usr/local/bin/chromedriver
```

### Step 3: First Run (QR Scan)

```bash
python main.py
```

**What happens:**
1. Chrome opens with WhatsApp Web
2. Scan QR code with your phone
3. Bot saves session to user data directory
4. Future runs won't require QR scan

---

## ✅ Testing

### Test 1: Database Connection

```bash
python -c "from src.database.db_manager import get_db_manager; print('✅ DB OK' if get_db_manager().test_connection() else '❌ DB FAIL')"
```

### Test 2: RAG Engine

```bash
python -c "from src.rag.rag_engine import get_rag_engine; rag = get_rag_engine(); rag.load_vector_store(); print('✅ RAG OK')"
```

### Test 3: Full Integration

```bash
pytest tests/ -v
```

---

## 🐛 Troubleshooting

### Issue: "OpenAI API key not found"

**Solution:**
```bash
# Verify .env file exists
cat .env | grep OPENAI_API_KEY

# Test API key
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('OPENAI_API_KEY')[:10])"
```

### Issue: "ChromeDriver version mismatch"

**Solution:**
```bash
# Check Chrome version
google-chrome --version  # Linux
# Chrome > Help > About Google Chrome  # Windows/Mac

# Download matching ChromeDriver
# https://chromedriver.chromium.org/downloads
```

### Issue: "Database connection failed"

**Solution:**
```bash
# Test MySQL connection
mysql -u root -p -h localhost

# Verify credentials in .env
cat .env | grep DB_

# Check if database exists
mysql -u root -p -e "SHOW DATABASES LIKE 'whatsapp_bot_db';"
```

### Issue: "FAISS index not found"

**Solution:**
```bash
# Rebuild index
python scripts/build_faiss_index.py build

# Verify index files exist
ls -la data/faiss_index/
```

### Issue: "WhatsApp Web not loading"

**Solution:**
1. Clear Chrome user data: `rm -rf C:/WhatsApp_UserData/Bot1/*`
2. Update ChromeDriver
3. Check internet connection
4. Try incognito mode manually first

---

## 📞 Support

If issues persist:
- Check logs: `logs/bot_primary.log`
- Enable debug: `LOG_LEVEL=DEBUG python main.py`
- Open issue: [GitHub Issues](https://github.com/your-org/whatsapp-ai-bot/issues)
- Email: latha.r@texila.org

---

**✨ You're all set! Run `python main.py` to start the bot.**
