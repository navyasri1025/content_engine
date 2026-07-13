# 🚀 AI Content Engine

Transform a simple product brief into a complete marketing campaign with the power of AI.

The AI Content Engine is a Streamlit-based application that generates multiple creative assets from a single product brief, helping users quickly create marketing content for different platforms.

---

## ✨ Features

- 💡 Generate a compelling campaign tagline
- 📝 Create a blog introduction tailored to the target audience
- 📱 Generate platform-specific social media posts
  - Twitter (X)
  - Instagram
  - LinkedIn
- 🎨 Generate a campaign hero image
- 🎬 Create a promotional video with AI-generated visuals and narration
- 📥 Download the generated promotional video
- 🎯 Simple and interactive Streamlit interface

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| Streamlit | User Interface |
| OpenRouter GPT-4.1 Mini | Text Generation |
| Pollinations AI (FLUX.1-dev) | Hero Image Generation |
| Pillow + NumPy + imageio | Ken Burns Video Creation |
| Edge TTS | AI Voice Narration |
| Python | Backend Logic |

---

# 📸 Application Workflow

User Brief

↓

Campaign Tagline

↓

Blog Introduction

↓

Social Media Posts

↓

Hero Image

↓

Promotional Video

---

## 🚀 Installation

Clone the repository

```bash
git clone <repository-url>
cd content_engine
```

Install dependencies

```bash
pip install -r requirements.txt
```

Create a `.env` file

```env
OPENROUTER_API_KEY=your_api_key
```

Run the application

```bash
streamlit run app.py
```

Open

```
http://localhost:8501
```

---

# 📋 Input

The application accepts:

- Product Name
- Target Audience
- Brand Tone

Click **Generate Campaign** to create the complete marketing suite.

---

# 🎯 Generated Assets

## Campaign Tagline

- AI-generated marketing slogan
- Tone-aware
- Short and memorable

---

## Blog Introduction

- Audience-focused
- Professional writing style
- Incorporates the campaign tagline

---

## Social Media Posts

Platform-specific content generated for

- Twitter (X)
- Instagram
- LinkedIn

Users can select a platform to view its generated post individually.

---

## Campaign Hero Image

Generated using AI based on

- Product
- Brand tone
- Marketing style

---

## Promotional Video

Creates a promotional video using

- AI-generated hero image
- Ken Burns animation
- AI narration using Edge TTS

The generated MP4 can be downloaded directly.

---

# 📂 Project Structure

```
content_engine/
│
├── app.py
├── config.py
├── text_gen.py
├── image_gen.py
├── video_gen.py
├── output/
├── requirements.txt
├── README.md
└── .env
```

---

# 📦 Dependencies

- Streamlit
- OpenAI
- python-dotenv
- Requests
- Pillow
- NumPy
- imageio
- imageio-ffmpeg
- Edge-TTS

---
# 🔮 Future Enhancements

- Export complete campaign as PDF
- Download complete campaign as ZIP
- Multiple image variations
- Additional social media platforms
- More AI models for content generation

---

# 📄 License

MIT License

---

