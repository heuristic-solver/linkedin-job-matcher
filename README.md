# AI Resume Matcher - Modern Web Interface

A sleek, minimalist web application that uses AI to match resumes with relevant job opportunities. Built with Flask backend and modern frontend design principles.

## ✨ Features

### 🎯 **Core Functionality**
- **AI-Powered Resume Analysis**: Extract and analyze resume content using Google's Gemini AI
- **Smart Job Matching**: Find relevant jobs from LinkedIn, Indeed, and CareerJet
- **Compatibility Scoring**: Get detailed match scores (0-100%) with explanations
- **Career Insights**: Receive AI-generated improvement recommendations

### 🎨 **Design Philosophy**
- **Minimalist Interface**: Extensive white space and clean layouts
- **Dynamic UX**: Smooth animations and micro-interactions
- **Responsive Design**: Mobile-first approach with seamless cross-device experience
- **Intuitive Navigation**: Consistent navigation with hover effects and blurred backgrounds

### 💡 **Technical Highlights**
- **File Support**: PDF, DOCX, and image files (with OCR)
- **Real-time Progress**: Live updates during processing
- **Background Processing**: Non-blocking job search and analysis
- **Performance Optimized**: Lazy loading and efficient rendering

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Tesseract OCR (for image processing)

### Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd /Users/a91788/Desktop/FYP
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Tesseract OCR**
   ```bash
   # macOS
   brew install tesseract

   # Ubuntu/Debian
   sudo apt install tesseract-ocr

   # Windows
   # Download from: https://github.com/UB-Mannheim/tesseract/wiki
   ```

4. **Set up your Google AI API Key**
   - Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Replace the API key in `linkedin_job_matcher.py` (line 13)
   - **Important**: Use environment variables in production

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open your browser**
   ```
   http://localhost:5000
   ```

## 🎯 How It Works

### 1. **Upload Resume**
- Drag & drop or browse for your resume file
- Supports PDF, DOCX, JPG, PNG, TIFF, BMP formats
- Real-time file validation and preview

### 2. **AI Analysis**
- Extracts text using advanced OCR if needed
- Analyzes skills, experience, education using Gemini AI
- Generates structured resume data

### 3. **Job Search**
- Customize search query and location
- Scrapes jobs from multiple sources
- Background processing with progress updates

### 4. **Smart Matching**
- AI compares resume with job descriptions
- Calculates compatibility scores
- Provides improvement recommendations

### 5. **Results Dashboard**
- Filter by match score (High/Medium/Low)
- Sort by score, date, or company
- Detailed insights for each position

## 🎨 Design System

### **Color Palette**
- **Primary**: #007AFF (Apple Blue)
- **Success**: #34C759 (Green)
- **Warning**: #FF9500 (Orange)
- **Error**: #FF3B30 (Red)
- **Neutrals**: Gray scale from #FAFAFA to #1C1C1E

### **Typography**
- **Font**: Inter (System fallback: SF Pro, Segoe UI)
- **Scale**: 0.75rem to 3rem (responsive)
- **Weights**: 300, 400, 500, 600, 700

### **Spacing**
- **8px Grid System**: Consistent spacing units
- **Generous White Space**: Enhances readability
- **Responsive Margins**: Adapts to screen size

### **Components**
- **Cards**: Rounded corners, subtle shadows
- **Buttons**: Gradient backgrounds, hover effects
- **Forms**: Clean inputs with focus states
- **Modals**: Blurred backgrounds, smooth transitions

## 📱 Responsive Breakpoints

- **Mobile**: < 480px
- **Tablet**: 481px - 768px
- **Desktop**: 769px - 1024px
- **Large**: > 1024px

## 🔧 API Endpoints

- `GET /` - Main application page
- `POST /upload` - Resume file upload
- `GET /analyze/<session_id>` - Resume analysis
- `POST /search-jobs` - Job search and matching
- `GET /progress/<session_id>` - Processing progress
- `GET /results/<session_id>` - Final results
- `GET /health` - Health check

## 🛠️ Project Structure

```
FYP/
├── app.py                 # Flask application
├── linkedin_job_matcher.py # Core matching logic
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Main template
├── static/
│   ├── css/
│   │   └── style.css     # Minimalist styles
│   └── js/
│       └── app.js        # Interactive functionality
└── uploads/              # Temporary file storage
```

## 🔒 Security Notes

- **API Keys**: Store in environment variables for production
- **File Upload**: Limited to 16MB, validated file types
- **Session Management**: Unique session IDs for user data
- **Data Privacy**: Files are processed locally

## 🚀 Performance Features

- **Lazy Loading**: Images and content load on demand
- **Debounced Inputs**: Reduced API calls
- **Background Processing**: Non-blocking operations
- **Optimized Assets**: Compressed CSS/JS
- **Caching**: Browser caching for static assets

## 🎯 Browser Support

- **Chrome**: 88+ ✅
- **Firefox**: 85+ ✅
- **Safari**: 14+ ✅
- **Edge**: 88+ ✅

## 📊 Features Comparison

| Feature | Original CLI | New Web UI |
|---------|-------------|------------|
| User Interface | Terminal | Modern Web UI |
| File Upload | Path Input | Drag & Drop |
| Progress Tracking | Print Statements | Real-time Progress Bar |
| Results Display | Text Output | Interactive Cards |
| Filtering | None | Advanced Filters |
| Mobile Support | None | Fully Responsive |
| User Experience | Basic | Premium |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

---

**Built with ❤️ using Flask, Google AI, and modern web technologies**
