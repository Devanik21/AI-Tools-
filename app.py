import streamlit as st
import google.generativeai as genai
import io
import base64
import json
import time
import os
from datetime import datetime
import fitz  # PyMuPDF for PDF text extraction
import re
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns
import pyperclip


# Configure Streamlit page
st.set_page_config(page_title="Ultimate AI Creator Hub", page_icon="🧠", layout="wide", initial_sidebar_state="expanded")

# Custom CSS (highly condensed)
st.markdown("""<style>.main{background-color:#f8f9fa}.stApp{max-width:1200px;margin:0 auto}.tool-category{font-size:1.2rem;font-weight:bold;margin-top:1rem;color:#1e3a8a}div[data-testid="stVerticalBlock"]{gap:0.5rem}.stButton>button{background:linear-gradient(90deg,#3b82f6,#8b5cf6);color:white;font-weight:600;border-radius:10px;padding:10px 20px;box-shadow:0 4px 14px rgba(0,0,0,0.1);transition:all 0.3s ease}.stButton>button:hover{transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,0.15)}div.stTabs [data-baseweb="tab-list"]{gap:8px}div.stTabs [data-baseweb="tab"]{background-color:#300661;border-radius:8px 8px 0px 0px;padding:10px 16px;font-weight:600}div.stTabs [aria-selected="true"]{background-color:#450542}.output-box{background-color:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:20px;margin-top:20px}.history-item{padding:10px;border:1px solid #e5e7eb;border-radius:8px;margin-bottom:8px;background-color:white}.category-selector{margin:10px 0}.search-box{margin:15px 0}</style>""", unsafe_allow_html=True)

# Initialize session state
if 'api_key' not in st.session_state: st.session_state.api_key = ""
if 'history' not in st.session_state: st.session_state.history = []
if 'api_model' not in st.session_state: st.session_state.api_model = "gemini-2.0-flash"
if 'prompt_templates' not in st.session_state: st.session_state.prompt_templates = {}



import os
import subprocess
import sys

# Function to check & install system dependencies (Tesseract & FFmpeg)
def install_dependencies():
    try:
        # Check if Tesseract is installed
        subprocess.run(["tesseract", "-v"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("✅ Tesseract is already installed.")
    except FileNotFoundError:
        print("⚠️ Tesseract not found. Installing now...")
        if os.name == "nt":  # Windows
            os.system("winget install -e --id UB-Mannheim.TesseractOCR")  # Requires Windows Package Manager
        elif os.name == "posix":  # Linux & MacOS
            os.system("sudo apt update && sudo apt install -y tesseract-ocr")
        print("✅ Tesseract installed successfully.")

    try:
        # Check if FFmpeg is installed
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("✅ FFmpeg is already installed.")
    except FileNotFoundError:
        print("⚠️ FFmpeg not found. Installing now...")
        if os.name == "nt":  # Windows
            os.system("winget install -e --id Gyan.FFmpeg")  # Requires Windows Package Manager
        elif os.name == "posix":  # Linux & MacOS
            os.system("sudo apt update && sudo apt install -y ffmpeg")
        print("✅ FFmpeg installed successfully.")

# Run dependency check on startup
install_dependencies()



import pytesseract
from PIL import Image

# Function to extract text from images (OCR)
def extract_text_from_image(uploaded_file):
    """Extracts text from an uploaded image file using OCR."""
    image = Image.open(uploaded_file)
    text = pytesseract.image_to_string(image)
    return text if text.strip() else "No text detected in the image."


# Function to extract text from CSV files
def extract_text_from_csv(uploaded_file):
    """Reads a CSV file and returns its content as a formatted string."""
    df = pd.read_csv(uploaded_file)
    return df.to_string(index=False)  # Convert DataFrame to readable text



# Function to extract text from TXT files
def extract_text_from_txt(uploaded_file):
    """Reads and returns text from a TXT file."""
    return uploaded_file.read().decode("utf-8")


import docx  # Ensure you have python-docx installed

# Function to extract text from DOCX files
def extract_text_from_docx(uploaded_file):
    """Reads and extracts text from a DOCX file."""
    doc = docx.Document(uploaded_file)
    return "\n".join([para.text for para in doc.paragraphs])  # Join paragraphs into a single text


import speech_recognition as sr
from pydub import AudioSegment
import io

# Function to extract text from audio files
def extract_text_from_audio(uploaded_file):
    """Converts speech from an audio file (MP3/WAV) to text using Google Speech Recognition."""
    recognizer = sr.Recognizer()
    
    # Read the file into a binary stream
    audio_bytes = uploaded_file.read()

    # Convert MP3 to WAV if needed
    try:
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))  # Auto-detect format
        audio = audio.set_channels(1).set_frame_rate(16000)  # Convert to mono, 16kHz
        wav_bytes = io.BytesIO()
        audio.export(wav_bytes, format="wav")
        wav_bytes.seek(0)  # Move to start of file
    except Exception as e:
        return f"Error processing audio file: {str(e)}"

    # Transcribe the converted WAV file
    with sr.AudioFile(wav_bytes) as source:
        audio_data = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio_data)  # Uses Google Speech Recognition API
        return text if text.strip() else "No speech detected in the audio."
    except sr.UnknownValueError:
        return "Could not understand the audio."
    except sr.RequestError:
        return "Could not request results from Google Speech Recognition."

import fitz  # For PDF processing (PyMuPDF)
import pandas as pd
import docx

def extract_text_from_file(uploaded_file):
    """Extracts text from an uploaded file (PDF, DOCX, TXT, CSV)."""
    file_type = uploaded_file.type
    if file_type == "application/pdf":
        # For PDFs
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        return "\n".join([page.get_text("text") for page in doc])
    elif file_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        # For DOCX files
        doc = docx.Document(uploaded_file)
        return "\n".join([para.text for para in doc.paragraphs])
    elif file_type in ["text/plain"]:
        # For TXT files
        return uploaded_file.read().decode("utf-8")
    elif file_type in ["text/csv"]:
        # For CSV files
        df = pd.read_csv(uploaded_file)
        return df.to_string(index=False)
    else:
        return "Unsupported file format."


import re

def extract_references(text):
    """Extracts possible reference sections from research papers."""
    references = re.findall(r"\[.*?\]|\(.*?\)", text)
    return references if references else ["No references detected."]


import fitz  # PyMuPDF for PDF text extraction

def extract_text_from_pdf(uploaded_file):
    """Extracts text from an uploaded PDF file."""
    try:
        with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
            text = "\n".join([page.get_text("text") for page in doc])
        return text
    except Exception as e:
        return f"Error extracting text: {str(e)}"

# Function to generate expanded AI tools list
@st.cache_data
def generate_ai_tools():
    # Base categories dictionary - we'll expand with multipliers later
    base_categories = {
        "Writing": [
            "Resume", "Cover Letter", "Email", "Blog Post", "Content Rewrite", "Grammar Check", 
            "Summary", "Academic Essay", "Letter", "Script", "Technical Writing", "Research Paper",
            "Whitepaper", "Thesis Statement", "Literature Review", "Citation", "Lab Report",
            "Case Study", "Editorial Guidelines", "Style Guide", "Professional Bio", "Executive Summary",
            "Project Proposal", "Meeting Minutes", "Documentation", "SOP", "Policy Draft",
            "Legal Document", "Contract Clause", "Terms & Conditions", "Privacy Policy"
        ],
        
        "Creative": [
            "Poem", "Story", "Dialogue", "Character", "Book Title", "Horror Story", "Sci-Fi Story",
            "Song Lyrics", "Children's Story", "Novel Outline", "Metaphor", "Joke", "Fantasy World",
            "Sci-Fi Technology", "Historical Fiction", "Memoir", "Poetry Prompt", "Creative Prompt",
            "Short Story Starter", "Screenplay Format", "Plot Twist", "Character Backstory",
            "Setting Description", "Alternate History", "Mythical Creature", "Magic System",
            "Fictional Language", "Story Conflict"
        ],
        
        "Business": [
            "Business Idea", "Startup Pitch", "SEO Keywords", "Business Consultation", "Marketing Strategy",
            "Grant Proposal", "Freelance Proposal", "LinkedIn Bio", "Branding Guide", "Business Email",
            "SWOT Analysis", "Business Case", "Market Research", "Competitor Analysis", "Pricing Strategy",
            "Product Launch", "Go-to-Market", "Customer Persona", "Mission Statement", "Company Values",
            "Business Plan", "Investor Pitch", "Funding Request", "Project Timeline", "Risk Assessment",
            "ROI Calculator", "KPI Framework"
        ]
    }

    
    # Additional categories to reach 2000+ tools
    extended_categories = {
        "Social Media": ["Post", "Caption", "Viral Tweet", "YouTube Idea", "Tagline", "Pinterest Description",
                        "Cold Email", "Podcast Episode", "Content Calendar", "Viral Formula", "Influencer Pitch",
                        "Brand Partnership", "YouTube Script", "Dating Profile", "Networking Opener",
                        "TikTok Trend", "Instagram Story", "LinkedIn Article", "Twitter Thread", "Facebook Ad",
                        "Hashtag Strategy", "Reel Script", "Community Post", "Review Response", "Crisis Response"],
        
        "Productivity": ["Productivity Plan", "Daily Plan", "Travel Itinerary", "Note-Taking", "Brainstorming",
                         "Grocery List", "Interview Prep", "Learning Path", "Time Management", "Prioritization",
                         "Decision Matrix", "Problem-Solving", "Critical Thinking", "Goal Setting", "Habit Tracker",
                         "Professional Development", "Weekly Schedule", "Project Management", "Task Breakdown"],
        
        "Education": ["Lesson Plan", "Course Outline", "Curriculum", "Educational Quiz", "Study Guide",
                     "Teaching Material", "Assignment", "Workshop", "Test Questions", "Learning Objectives",
                     "Educational Game", "Academic Resource", "Subject Summary", "Syllabus", "Tutorial"],
        
        "Design": ["Design Brief", "Color Palette", "Typography Guide", "Design System", "Logo Concept",
                  "UI Element", "UX Flow", "Website Layout", "Print Material", "Product Packaging",
                  "Illustration Concept", "Icon Set", "Brand Identity", "Style Tile", "Mood Board"],
        
        "Development": ["Code Review", "Technical Spec", "API Documentation", "Development Plan", "Code Architecture",
                       "Database Schema", "Software Requirements", "Testing Strategy", "Bug Report", "Feature Spec",
                       "Code Refactoring", "Algorithm", "Tech Stack", "System Architecture", "Code Snippet"],
        
        "Marketing": ["Marketing Plan", "Campaign Brief", "Ad Copy", "Landing Page", "Email Campaign",
                     "Conversion Strategy", "Growth Hack", "Product Description", "Promotion", "Sales Script",
                     "Value Proposition", "USP", "Elevator Pitch", "Customer Journey", "Messaging Framework"],
        
        "Finance": ["Budget Plan", "Financial Analysis", "Investment Strategy", "Expense Report", "Revenue Forecast",
                   "Cash Flow", "Financial Model", "Cost Reduction", "Profit Optimization", "Tax Strategy",
                   "Retirement Plan", "Debt Management", "Financial Education", "Savings Plan", "Equity Distribution"],
        
        "Health": ["Wellness Plan", "Diet Plan", "Fitness Routine", "Mental Health", "Sleep Improvement",
                  "Meditation Script", "Nutrition Guide", "Health Goal", "Self-Care Routine", "Stress Management",
                  "Recovery Plan", "Symptom Analysis", "Mindfulness Exercise", "Health Tracker", "Medical Information"],
        
        "Legal": ["Legal Analysis", "Contract Template", "Legal Response", "Compliance Check", "Privacy Statement",
                 "Disclaimer", "Terms of Service", "Copyright Notice", "IP Strategy", "Legal Research",
                 "Legal Letter", "Dispute Resolution", "Regulatory Filing", "Legal Defense", "Intellectual Property"],
        
        "Event": ["Event Plan", "Invitation", "Wedding Speech", "Toast", "Anniversary Message", "Party Theme",
                 "Conference Agenda", "Event Marketing", "Catering Menu", "Venue Description", "Entertainment Plan",
                 "Guest List", "Event Schedule", "Thank You Note", "Event Budget", "Virtual Event"],
        
        "Relationships": ["Relationship Advice", "Conflict Resolution", "Apology Letter", "Friendship Message",
                         "Love Letter", "Dating Profile", "Breakup Letter", "Family Communication", "Networking Message",
                         "Condolence Note", "Birthday Message", "Anniversary Note", "Congratulations Note", "Reconnection"],
        
        "Industry": ["Industry Analysis", "Sector Trend", "Market Forecast", "Industry Report", "Competitive Landscape",
                    "Regulatory Impact", "Technology Adoption", "Industry Disruption", "Vertical Strategy", "Supply Chain",
                    "Distribution Channel", "Industry Standards", "Industry Partnership", "Trade Association", "Industry Event"]
    }
    
    # Combine base and extended categories
    all_categories = {**base_categories, **extended_categories}
    
    # Multipliers to expand each tool category (adjectival prefixes)
    tool_multipliers = [
        "Advanced", "Custom", "Premium", "Enhanced", "Professional", "Intelligent", "Smart", "Dynamic",
        "Interactive", "Personalized", "Strategic", "Comprehensive", "Automated", "High-Performance", "Next-Gen",
        "Streamlined", "Optimized", "Scalable", "Innovative", "Creative", "Essential", "Ultimate", "Practical",
        "Specialized", "Expert", "Efficient", "Versatile", "Powerful", "Flexible", "Multi-purpose"
    ]
    
    # Format multipliers (output format variations)
    format_multipliers = [
        "Generator", "Builder", "Creator", "Designer", "Maker", "Assistant", "Helper", "Tool", "Solution",
        "Expert", "Consultant", "Advisor", "Planner", "Architect", "Analyst", "Strategist", "Developer",
        "Manager", "Optimizer", "Writer", "Guide", "Template", "Framework", "System", "Toolkit"
    ]
    
    # Generate expanded tools by combining base tools with multipliers
    expanded_categories = {}
    for category, base_tools in all_categories.items():
        expanded_tools = []
        for base_tool in base_tools:
            # Add the original tool with common suffixes
            for format_mult in format_multipliers[:3]:  # Limit to top 3 formats
                expanded_tools.append(f"{base_tool} {format_mult}")
            
            # Add tools with multipliers (limit to reduce overwhelming options)
            for mult in tool_multipliers[:5]:  # Limit to top 5 multipliers
                expanded_tools.append(f"{mult} {base_tool}")
        
        expanded_categories[category] = expanded_tools
    
    # Create specialized industry categories (new areas)
    specialized_industries = {
        "Healthcare": ["Patient Care", "Medical Record", "Clinical Trial", "Health Assessment", "Treatment Plan",
                      "Healthcare Policy", "Medical Research", "Patient Education", "Telehealth", "Health Insurance",
                      "Medical Device", "Healthcare Compliance", "Medical Diagnosis", "Patient Experience", "Wellness Program"],
        
        "E-commerce": ["Product Listing", "Customer Review", "E-commerce Copy", "Shipping Policy", "Return Policy",
                       "Product Bundle", "Flash Sale", "Customer Engagement", "Shopping Experience", "Loyalty Program",
                       "Product Recommendation", "Checkout Process", "Customer Retention", "Marketplace Strategy", "Pricing Model"],
        
        "Real Estate": ["Property Description", "Market Analysis", "Investment Property", "Rental Analysis", "Home Staging",
                       "Property Marketing", "Neighborhood Guide", "Real Estate Listing", "Agent Bio", "Mortgage Information",
                       "Home Inspection", "Lease Agreement", "Property Management", "HOA Communication", "Commercial Lease"],
        
        "Sustainability": ["Environmental Impact", "Sustainability Report", "Green Initiative", "Carbon Footprint", "ESG Strategy",
                          "Circular Economy", "Sustainable Design", "Climate Action", "Conservation Plan", "Energy Efficiency",
                          "Waste Reduction", "Water Conservation", "Sustainable Supply Chain", "Social Impact", "Eco Certification"],
        
        "Technology": ["Tech Specification", "Product Roadmap", "User Guide", "Tech Support", "Software Release",
                      "Hardware Design", "Tech Solution", "IT Strategy", "Digital Transformation", "Tech Integration",
                      "Tech Troubleshooting", "Cloud Migration", "Data Strategy", "Network Design", "Tech Evaluation"]
    }
    
    # Add specialized industries to the expanded categories
    for industry, tools in specialized_industries.items():
        industry_tools = []
        for tool in tools:
            # Add the original tool with common suffixes
            for format_mult in format_multipliers[:3]:  # Limit to top 3 formats
                industry_tools.append(f"{tool} {format_mult}")
            
            # Add tools with multipliers (limit to reduce overwhelming options)
            for mult in tool_multipliers[:3]:  # Limit to top 3 multipliers
                industry_tools.append(f"{mult} {tool}")
        
        expanded_categories[industry] = industry_tools
    
    # Create flat list of all tools
    all_tools = []
    for category, tools in expanded_categories.items():
        all_tools.extend(tools)
    
    return all_tools, expanded_categories


# Add this to your imports
import re
from collections import Counter

# Add this function after your other functions
def analyze_content(text):
    # Basic text analysis
    word_count = len(re.findall(r'\w+', text))
    sentence_count = len(re.findall(r'[.!?]+', text)) + 1
    paragraph_count = len(text.split('\n\n'))
    
    # Readability metrics
    words = re.findall(r'\w+', text.lower())
    word_lengths = [len(word) for word in words]
    avg_word_length = sum(word_lengths) / len(word_lengths) if word_lengths else 0
    
    # Sentiment indicators (simplified)
    positive_words = ['good', 'great', 'excellent', 'best', 'positive', 'happy', 'wonderful', 'amazing']
    negative_words = ['bad', 'worst', 'terrible', 'negative', 'poor', 'awful', 'horrible']
    
    positive_count = sum(1 for word in words if word in positive_words)
    negative_count = sum(1 for word in words if word in negative_words)
    
    sentiment = "Positive" if positive_count > negative_count else "Negative" if negative_count > positive_count else "Neutral"
    
    # Most common words
    common_words = Counter(words).most_common(5)
    
    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "paragraph_count": paragraph_count,
        "avg_word_length": round(avg_word_length, 2),
        "sentiment": sentiment,
        "common_words": common_words
    }
    
# Get all tools and categories
ai_tools, tool_categories = generate_ai_tools()

# Function to load prompt templates (dynamic generation)
@st.cache_data
def load_prompt_templates():
    templates = {}
    for tool in ai_tools:
        templates[tool] = f"Generate content using the '{tool}' feature for: {{prompt}}. Ensure the output is high quality, relevant, and tailored to the user's needs."
    return templates

# Function to generate content with AI
def generate_ai_content(prompt, api_key, model_name):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        with st.spinner("🔮 AI is working its magic..."):
            generation_config = {"temperature": 0.7, "top_p": 0.95, "top_k": 40, "max_output_tokens": 8192}
            response = model.generate_content(prompt, generation_config=generation_config)
            return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# Function to save content to history
def save_to_history(tool_name, prompt, output):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.history.insert(0, {"timestamp": timestamp, "tool": tool_name, "prompt": prompt, "output": output})
    if len(st.session_state.history) > 20:
        st.session_state.history = st.session_state.history[:20]

# Sidebar for API configuration
with st.sidebar:
    st.image("aichip.jpg")
    st.markdown("### 🔑 API Configuration")
    api_key = st.text_input("Enter Google Gemini API Key:", type="password", value=st.session_state.api_key, help="Your API key is stored in the session and not saved.")
    if api_key: st.session_state.api_key = api_key
    
    # Model selection with Gemini models
    st.session_state.api_model = st.selectbox(
        "Select AI Model:",
        ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro","gemini-2.0-flash-lite","gemini-2.0-pro-exp-02-05",
"gemini-2.0-flash-thinking-exp-01-21","gemini-1.5-flash-8b"],
        index=0
    )
    
    st.markdown("---")
    search_term = st.text_input("🔍 Search for tools:")
    filtered_tools = [tool for tool in ai_tools if search_term.lower() in tool.lower()] if search_term else ai_tools
    
    # Statistics
    # Statistics
    st.sidebar.markdown("### 📊 Stats")
    st.sidebar.markdown(f"**Total Tools:** {len(ai_tools)}")
    st.sidebar.markdown(f"**Categories:** {len(tool_categories)}")
    
    # History button in sidebar
    st.sidebar.markdown("---")
    show_history = st.sidebar.button("📜 View History")
    clear_history = st.sidebar.button("🗑️ Clear History")
    if clear_history:
        st.session_state.history = []
        st.sidebar.success("History cleared!")

# Main content area
st.title("🧠 Ultimate AI Creator Hub")
st.markdown("Create amazing content with AI-powered tools - all in one place!")

# Welcome message
if not st.session_state.api_key:
    st.info("👋 Welcome! Please enter your API key in the sidebar to get started.")

# Display history if requested
if show_history and 'history' in st.session_state and len(st.session_state.history) > 0:
    st.header("📜 Content History")
    for i, item in enumerate(st.session_state.history):
        with st.expander(f"{item['timestamp']} - {item['tool']}"):
            st.markdown("**Prompt:**")
            st.markdown(f"```\n{item['prompt']}\n```")
            st.markdown("**Output:**")
            st.markdown(item['output'])
    st.markdown("---")

# Load prompt templates if needed
if not st.session_state.prompt_templates or len(st.session_state.prompt_templates) == 0:
    st.session_state.prompt_templates = load_prompt_templates()

# Tool Selection Section
st.header("🛠️ Select Your Creation Tool")

st.markdown("""
    <style>
    div[data-testid="stTabs"] button {
        font-size: 12px !important;
        padding: 20px !important;
    }
    </style>
""", unsafe_allow_html=True)

import streamlit as st

# Example tool categories dictionary
tool_categories = {
    "📋 Categories": ["Data Science", "AI Tools", "Research"],
    "🔍 Search Results": ["Recent Searches", "Trending Tools"],
    "📚 AI Research Assistant": ["Paper Summarizer", "Citation Generator"],
    "🤖 AI Chatbot": ["Chatbot 1", "Chatbot 2"],
    "🌍 AI Translator": ["Text Translator", "Speech Translator"],
    "⚡ AI Code Wizard": ["Code Generator", "Bug Fixer"],
}

# Select section
selected_section = st.selectbox("Choose a section:", list(tool_categories.keys()))

# Display tools in the selected section
if selected_section:
    tools_in_section = tool_categories[selected_section]
    st.markdown(f"### {selected_section} Tools ({len(tools_in_section)})")

    # Create grid layout for tools
    cols = st.columns(3)
    for i, tool in enumerate(tools_in_section):
        with cols[i % 3]:
            if st.button(tool, key=f"tool_{tool}"):
                st.session_state.selected_tool = tool




