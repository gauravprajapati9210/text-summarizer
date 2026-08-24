# TextSummarizer - Modern Text Summarization Web Application

A modern, responsive single-page web application for text summarization powered by a pre-trained transformer model. Built with FastAPI backend and vanilla HTML/CSS/JavaScript frontend.

## 🎯 Features

- **Single-Page Application**: Clean, focused interface for text summarization
- **Real-time Counters**: Character and word count updates as you type
- **Drag & Drop Support**: Drop text files directly into the input area
- **Responsive Design**: Fully responsive on desktop, tablet, and mobile
- **Professional UI**: Modern SaaS-style interface with smooth animations
- **Error Handling**: User-friendly error messages for all edge cases
- **Copy & Download**: Easy sharing and saving of summaries
- **Fast Processing**: GPU-accelerated summarization using PyTorch

## 📁 Project Structure

```
Text_summarizerCode/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── model.py             # Model loader and inference
│   ├── requirements.txt      # Python dependencies
│   └── .env                 # Environment configuration
├── frontend/
│   └── index.html           # Single-page application
└── saved_summary_model/     # Pre-trained model (existing)
    ├── config.json
    ├── generation_config.json
    ├── model.safetensors
    ├── tokenizer_config.json
    └── tokenizer.json
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Modern web browser (Chrome, Firefox, Safari, Edge)

### 1. Backend Setup

Navigate to the backend directory and install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

### 2. Start the Backend Server

```bash
python main.py
```

The server will start at `http://localhost:8000`

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete
✓ Model loaded from ../saved_summary_model on device: cuda
```

### 3. Open the Frontend

Option A: **Using Live Server** (Recommended for development)
- Install VS Code extension "Live Server" by Ritwick Dey
- Right-click on `frontend/index.html`
- Select "Open with Live Server"
- The app will open at `http://127.0.0.1:5500`

Option B: **Using Python's built-in server**
```bash
cd frontend
python -m http.server 8080
```
Then open `http://localhost:8080` in your browser

Option C: **Direct file access**
- Simply open `frontend/index.html` in your browser
- Works offline with local files, but API calls require backend running

### 4. Configure API Connection

The frontend automatically connects to `http://localhost:8000`. If your backend runs on a different address, configure it via browser console:

```javascript
localStorage.setItem('apiBaseUrl', 'http://your-backend-url:8000');
location.reload();
```

## 📋 API Documentation

### Health Check
```
GET /health
```
Returns: `{"status": "healthy", "service": "Text Summarizer API"}`

### Summarize Text
```
POST /api/summarize
Content-Type: application/json

{
  "text": "Your text here",
  "max_length": 150,      // Optional, default 150
  "min_length": 30        // Optional, default 30
}
```

Response:
```json
{
  "summary": "Generated summary",
  "original_length": 250,
  "summary_length": 45
}
```

### Error Responses
```json
{
  "detail": "Please enter some text before summarizing."
}
```

## 🎨 UI/UX Features

### Header
- Logo and site name
- Navigation items (Home, About)
- Clean, minimal design

### Hero Section
- Engaging heading and subheading
- Floating icon animation
- Clear value proposition

### Input Section
- Large, comfortable textarea
- Character and word counters
- Drag-and-drop file support
- Clear button to reset input
- Prominent "Summarize Text" button with loading state

### Output Section
- Generated summary display
- Summary word count
- Copy to clipboard button
- Download as .txt file button
- "Summarize New Text" button to reset

### Error Handling
- Empty input validation
- Minimum word count (10 words)
- Maximum word count (2000 words)
- API connection failure detection
- Model processing error handling
- User-friendly error messages (no technical jargon)

## 🎯 Functional Requirements Met

✅ Text input with placeholder
✅ Character counter
✅ Word counter
✅ Clear input button
✅ Summarization API call
✅ Loading state on button
✅ Summary display
✅ Summary word count
✅ Copy to clipboard
✅ Download summary
✅ Reset application
✅ Error handling
✅ API connection handling
✅ Responsive design (desktop, tablet, mobile)
✅ Drag-and-drop file support
✅ Success animation on summary display

## 🔧 Configuration

### Environment Variables (Backend)

Edit `backend/.env`:

```env
# Allowed frontend origins (CORS)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080,http://127.0.0.1:5500
```

Add more origins for production deployment:
```env
ALLOWED_ORIGINS=http://localhost:8000,https://yourdomain.com,https://www.yourdomain.com
```

### Model Configuration

The backend automatically loads the model from `../saved_summary_model`. To use a different model:

Edit `backend/model.py`:
```python
# Change this line:
model_path = os.path.join(Path(__file__).parent.parent, "saved_summary_model")

# To:
model_path = "/path/to/your/model"
```

## 📱 Responsive Breakpoints

- **Desktop** (> 768px): Centered content, large textarea, comfortable spacing
- **Tablet** (481px - 768px): Reduced margins, optimized card sizes
- **Mobile** (≤ 480px): Full-width elements, vertical stacking, optimized touch targets

## 🚀 Deployment

### Netlify frontend + Supabase visit counter

The frontend is ready for Netlify, while the FastAPI model service must run on a Python-capable host such as Render, Railway, Fly.io, or Azure Container Apps. Netlify's static hosting and serverless functions are not suitable for loading this PyTorch model.

1. In Supabase, open **SQL Editor** and run [`backend/supabase_schema.sql`](backend/supabase_schema.sql). This creates the `app_metrics` table and the atomic `increment_app_visits` RPC.
2. Deploy the backend from the repository root so the image can include `saved_summary_model`; use `backend/Dockerfile` and expose port `8000`.
3. Add these backend environment variables on that host:
  - `SUPABASE_URL`: your Supabase project URL
  - `SUPABASE_SERVICE_ROLE_KEY`: your Supabase service-role key
  - `ALLOWED_ORIGINS`: `https://YOUR-SITE.netlify.app`
4. In Netlify, import this repository and use the existing `netlify.toml` settings. Add the build environment variable `API_BASE_URL` with the deployed backend URL, for example `https://your-api.example.com`.
5. Deploy the site. Netlify runs `scripts/build-frontend-config.mjs`, which writes the backend URL to `frontend/config.js`. The browser then calls the backend's `/api/visits` endpoint, which stores the count in Supabase.

Never put `SUPABASE_SERVICE_ROLE_KEY` in Netlify variables or frontend files. It must only exist in the backend environment.

For local development, copy `backend/.env.example` to `backend/.env`, use the local frontend URL in `ALLOWED_ORIGINS`, and leave `API_BASE_URL` unset so the frontend uses `http://localhost:8000`.

### Docker Deployment (Optional)

Create `backend/Dockerfile`:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t textsummarizer-backend .
docker run -p 8000:8000 textsummarizer-backend
```

### Production Deployment

For production, deploy the backend to a server (AWS, GCP, Azure, Heroku) and update:

1. `ALLOWED_ORIGINS` in `.env` to include your domain
2. API URL in frontend localStorage (or change hardcoded default)
3. Consider using environment variables for sensitive config

Example for Heroku backend:
```javascript
localStorage.setItem('apiBaseUrl', 'https://your-app.herokuapp.com');
```

## 🛠️ Development

### Adding Features

1. **Backend**: Add new endpoints in `backend/main.py`
2. **Frontend**: Update `frontend/index.html` to call new endpoints
3. **Model**: Modify inference logic in `backend/model.py`

### Testing

Test the API directly:
```bash
curl -X POST http://localhost:8000/api/summarize \
  -H "Content-Type: application/json" \
  -d '{"text": "Your text here for summarization testing"}'
```

## 📊 Performance Notes

- **GPU Usage**: Automatically uses CUDA if available (much faster)
- **CPU Fallback**: Falls back to CPU if CUDA unavailable
- **Processing Time**: ~2-10 seconds depending on text length and hardware
- **Max Text Length**: 2000 words (configurable in `main.py`)
- **Model Inference**: Batching optimized, single text at a time

## 🐛 Troubleshooting

### Issue: Backend connection failed

**Solution**: Ensure backend is running on `http://localhost:8000`
```bash
cd backend
python main.py
```

### Issue: Model loading error

**Solution**: Verify the model exists at `saved_summary_model/`
```bash
ls -la saved_summary_model/
```

### Issue: CORS error in browser console

**Solution**: Update `ALLOWED_ORIGINS` in `backend/.env` to include your frontend URL

### Issue: Summarization takes too long

**Solution**: Check GPU availability:
```bash
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### Issue: Text too short error

**Solution**: Ensure input text has at least 10 words

## 🔒 Security Notes

- No user data is stored or logged
- Input validation on both frontend and backend
- CORS protection to prevent unauthorized access
- No sensitive information exposed in error messages
- Safe file handling for drag-and-drop

## 📄 License

This project uses pre-trained transformer models. See the model's original licensing terms.

## 🤝 Support

For issues or questions, check:
1. Backend logs for errors
2. Browser console for frontend errors
3. `.env` configuration
4. Model path and availability

---

Built with ❤️ for efficient text summarization
