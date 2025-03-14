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
        font-size: 16px !important;
        padding: 10px !important;
    }
    </style>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 , tab6 = st.tabs([
    "📋 Categories", "🔍 Search Results", 
    "📚 AI Research Assistant", "🤖 AI Chatbot", "🌍 AI Translator" , "⚡ AI Code Wizard"
])


with tab1:
    selected_category = st.selectbox("Choose a category:", list(tool_categories.keys()))
    
    # Only show tools from selected category
    if selected_category:
        tools_in_category = tool_categories[selected_category]
        st.markdown(f"### {selected_category} Tools ({len(tools_in_category)})")
        
        # Create grid layout for tools
        cols = st.columns(3)
        for i, tool in enumerate(tools_in_category):
            with cols[i % 3]:
                if st.button(tool, key=f"cat_{tool}"):
                    st.session_state.selected_tool = tool

with tab2:
    if search_term:
        st.markdown(f"### Search Results for '{search_term}' ({len(filtered_tools)})")
        
        # Create grid layout for search results
        cols = st.columns(3)
        for i, tool in enumerate(filtered_tools[:30]):  # Limit to 30 results
            with cols[i % 3]:
                if st.button(tool, key=f"search_{tool}"):
                    st.session_state.selected_tool = tool
    else:
        st.info("Enter a search term in the sidebar to find specific tools.")


with tab3:
    st.header("📚 AI Research Assistant")

    # Paper Summarization Section - ENHANCED
    st.subheader("📑 Research Paper Summarization")
    uploaded_file = st.file_uploader("Upload Research Paper (PDF)", type="pdf")
    
    if uploaded_file:
        pdf_text = extract_text_from_pdf(uploaded_file)
        
        # Add advanced PDF extraction options
        extraction_options = st.expander("Advanced Extraction Options")
        with extraction_options:
            extract_figures = st.checkbox("Extract Figures", value=False)
            extract_tables = st.checkbox("Extract Tables", value=False)
            extract_references = st.checkbox("Extract References", value=True)
            max_text_length = st.slider("Maximum Text Length (chars)", 1000, 20000, 6000)
        
        st.text_area("Extracted Text:", pdf_text[:max_text_length], height=500)
        
        summary_options = st.expander("Summary Options")
        with summary_options:
            summary_type = st.radio("Summary Type", 
                ["Concise (1 paragraph)", "Standard (3-5 paragraphs)", "Detailed (comprehensive)"])
            focus_areas = st.multiselect("Focus Areas", 
                ["Methodology", "Results", "Conclusions", "Background", "Limitations", "Future Work"])
            academic_level = st.select_slider("Academic Level", 
                ["Undergraduate", "Graduate", "Expert"])
        
        if st.button("Summarize Paper ✨"):
            # Enhanced prompt with options
            focus_str = ", ".join(focus_areas) if focus_areas else "all sections"
            summary_prompt = f"""Summarize this research paper {summary_type}. 
            Focus on {focus_str} at an {academic_level} level:
            
            {pdf_text[:max_text_length]}"""
            
            with st.spinner("Generating summary..."):
                summary = generate_ai_content(summary_prompt, st.session_state.api_key, st.session_state.api_model)
            
            st.success("📑 AI Summary:")
            st.write(summary)

            # Add export options
            col1, col2 = st.columns(2)
            with col1:
                st.download_button("Download Summary", summary, "paper_summary.txt")
            with col2:
                st.button("Copy to Clipboard", on_click=lambda: st.write("<script>navigator.clipboard.writeText(`" + summary.replace("`", "\\`") + "`);</script>", unsafe_allow_html=True))

    # Citation Generator - ENHANCED
    st.subheader("📖 Citation Generator")
    
    citation_tabs = st.tabs(["Text Input", "PDF Upload", "DOI Lookup"])
    
    with citation_tabs[0]:
        citation_input = st.text_area("Paste Reference Text:")
        
    with citation_tabs[1]:
        citation_pdf = st.file_uploader("Upload paper for citation extraction", type="pdf")
        if citation_pdf:
            citation_input = extract_text_from_pdf(citation_pdf)
            st.success("PDF processed for citations")
            
    with citation_tabs[2]:
        doi_input = st.text_input("Enter DOI (e.g., 10.1038/nature12373):")
        if doi_input and st.button("Fetch DOI Metadata"):
            # Implement DOI lookup API call
            st.session_state.citation_input = f"DOI: {doi_input}"
            citation_input = st.session_state.citation_input
            st.success(f"Retrieved metadata for DOI: {doi_input}")
    
    citation_format = st.selectbox("Citation Format:", 
        ["IEEE", "APA", "MLA", "Chicago", "Harvard", "BibTeX", "RIS"])
    
    if st.button("Generate Citations"):
        citations = extract_references(citation_input)
        citation_prompt = f"Convert these references into {citation_format} format:\n{citations}"
        
        with st.spinner("Formatting citations..."):
            formatted_citations = generate_ai_content(citation_prompt, st.session_state.api_key, st.session_state.api_model)
        
        st.success("📜 Formatted Citations:")
        st.code(formatted_citations)
        
        # Add copy and export options
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("Download Citations", formatted_citations, f"citations_{citation_format.lower()}.txt")
        with col2:
            if citation_format == "BibTeX":
                st.download_button("Download BibTeX", formatted_citations, "references.bib")

    # Research Idea Expansion - ENHANCED
    st.subheader("🔬 Research Proposal Generator")
    
    research_topic = st.text_input("Enter Research Idea:")
    
    proposal_options = st.expander("Proposal Options")
    with proposal_options:
        proposal_type = st.selectbox("Proposal Type", 
            ["Brief Concept", "Conference Abstract", "Full Research Proposal", "Grant Application"])
        
        discipline = st.selectbox("Academic Discipline", 
            ["Computer Science", "Biology", "Chemistry", "Physics", "Psychology", 
             "Sociology", "Economics", "Engineering", "Medicine", "Environmental Science", "Other"])
        
        if discipline == "Other":
            custom_discipline = st.text_input("Specify Discipline:")
            if custom_discipline:
                discipline = custom_discipline
        
        methodologies = st.multiselect("Preferred Methodologies", 
            ["Quantitative", "Qualitative", "Mixed Methods", "Experimental", 
             "Observational", "Literature Review", "Meta-Analysis", "Simulation"])
        
        novelty_slider = st.slider("Novelty Level", 1, 10, 7, 
            help="1 = Incremental research, 10 = Groundbreaking approach")
        
        word_limit = st.number_input("Word Count Target", 300, 5000, 1000)
    
    if st.button("Generate Proposal 🚀"):
        # Build advanced prompt with all parameters
        methods_str = ", ".join(methodologies) if methodologies else "any appropriate"
        
        expansion_prompt = f"""Develop a {proposal_type} for: {research_topic}
        
        Academic field: {discipline}
        Methodologies to consider: {methods_str}
        Novelty level (1-10): {novelty_slider}
        Target length: ~{word_limit} words
        
        Include: research question, background, methodology, expected outcomes, and significance.
        """
        
        with st.spinner("Creating research proposal..."):
            research_proposal = generate_ai_content(expansion_prompt, st.session_state.api_key, st.session_state.api_model)
        
        st.success("📄 AI-Generated Research Proposal:")
        st.write(research_proposal)
        
        # Export options
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("Download Proposal", research_proposal, "research_proposal.docx")
        with col2:
            st.button("Save to Projects", help="Save this proposal to your projects collection")


with tab4:
    st.header("🤖 AI Chatbot with Universal File Upload")
    
    # Import required libraries
    import pandas as pd
    import matplotlib.pyplot as plt
    import plotly.express as px
    from collections import Counter
    import re
    from io import StringIO
    
    # Try to import wordcloud or handle missing dependency
    try:
        from wordcloud import WordCloud, STOPWORDS
    except ImportError:
        st.warning("WordCloud is not installed. Install with: pip install wordcloud")
        # Create dummy functions/classes to prevent errors
        class WordCloud:
            def __init__(self, **kwargs):
                pass
            def generate(self, text):
                pass
        STOPWORDS = set()
    
    # Try to import nltk or handle missing dependency
    try:
        import nltk
        from nltk.util import ngrams
    except ImportError:
        st.warning("NLTK is not installed. Install with: pip install nltk")
        # Create dummy functions to prevent errors
        def ngrams(text, n):
            return []

    # File uploader
    uploaded_file = st.file_uploader("Upload a file (PDF, DOCX, CSV, TXT, Audio)", 
                                    type=["pdf", "docx", "csv", "txt", "mp3", "wav"])

    extracted_text = ""  # Store extracted text
    df = None  # Store dataframe for visualizations

    # Process uploaded file
    if uploaded_file:
        file_type = uploaded_file.type

        if file_type == "application/pdf":
            extracted_text = extract_text_from_pdf(uploaded_file)
        elif file_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            extracted_text = extract_text_from_docx(uploaded_file)
        elif file_type in ["text/plain"]:
            extracted_text = extract_text_from_txt(uploaded_file)
            try:
                # Try to parse as CSV in case it's a CSV saved as TXT
                if extracted_text.strip():  # Check if text is not empty
                    df = pd.read_csv(StringIO(extracted_text), sep=None, engine='python')
                else:
                    words = re.findall(r'\w+', extracted_text.lower())
                    word_freq = Counter(words)
            except Exception as e:
                st.warning(f"Could not parse as CSV: {str(e)}")
                # If not parseable as CSV, prepare for text visualizations
                words = re.findall(r'\w+', extracted_text.lower())
                word_freq = Counter(words)
        elif file_type in ["text/csv"]:
            extracted_text = extract_text_from_csv(uploaded_file)
            try:
                # Reset file pointer to beginning before reading
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file)
                if df.empty:
                    st.warning("The CSV file appears to be empty")
            except Exception as e:
                st.warning(f"Error parsing CSV: {str(e)}")
                # Handle as text if CSV parsing fails
                words = re.findall(r'\w+', extracted_text.lower())
                word_freq = Counter(words)
        elif file_type in ["image/png", "image/jpeg"]:
            extracted_text = extract_text_from_image(uploaded_file)
        elif file_type in ["audio/mpeg", "audio/wav"]:
            extracted_text = extract_text_from_audio(uploaded_file)

        st.success("✅ File processed successfully!")
        st.text_area("Extracted Content:", extracted_text[:2000], height=200)  # Preview first 2000 characters

        # Visualization section for TXT and CSV
        if file_type in ["text/plain", "text/csv"] and (df is not None or 'word_freq' in locals()):
            st.subheader("📊 Data Visualizations")
            
            # Create tabs for different visualization categories
            viz_tabs = st.tabs(["Basic Stats", "Distributions", "Correlations", "Time Series", "Text Analysis"])
            
            # CSV-specific visualizations
            if df is not None:
                with viz_tabs[0]:  # Basic Stats
                    st.write("### Data Overview")
                    st.dataframe(df.describe())
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("### Missing Values")
                        st.bar_chart(df.isnull().sum())
                    with col2:
                        st.write("### Data Types")
                        st.write(pd.DataFrame(df.dtypes, columns=['Data Type']))
                
                with viz_tabs[1]:  # Distributions
                    st.write("### Distributions")
                    
                    # Determine numeric columns
                    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                    if numeric_cols:
                        selected_col = st.selectbox("Select column for histogram:", numeric_cols)
                        fig = px.histogram(df, x=selected_col, marginal="box")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Distribution comparison
                        if len(numeric_cols) >= 2:
                            cols_to_compare = st.multiselect("Select columns to compare distributions:", 
                                                           numeric_cols, default=numeric_cols[:2])
                            if cols_to_compare:
                                fig = px.box(df, y=cols_to_compare)
                                st.plotly_chart(fig, use_container_width=True)
                    
                    # Categorical distributions
                    cat_cols = df.select_dtypes(include=['object']).columns.tolist()
                    if cat_cols:
                        selected_cat = st.selectbox("Select categorical column:", cat_cols)
                        top_n = st.slider("Top N categories:", 5, 20, 10)
                        value_counts = df[selected_cat].value_counts().head(top_n)
                        fig = px.bar(x=value_counts.index, y=value_counts.values)
                        st.plotly_chart(fig, use_container_width=True)
                
                with viz_tabs[2]:  # Correlations
                    st.write("### Correlations")
                    if len(numeric_cols) >= 2:
                        try:
                            corr_method = st.radio("Correlation method:", ["Pearson", "Spearman"])
                            corr = df[numeric_cols].corr(method=corr_method.lower())
                            
                            fig = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r')
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Scatter plot for two variables
                            st.write("### Scatter Plot")
                            col1, col2 = st.columns(2)
                            with col1:
                                x_col = st.selectbox("X-axis:", numeric_cols, index=0)
                            with col2:
                                y_col = st.selectbox("Y-axis:", numeric_cols, index=min(1, len(numeric_cols)-1))
                            
                            color_col = st.selectbox("Color by (optional):", ["None"] + df.columns.tolist())
                            if color_col == "None":
                                fig = px.scatter(df, x=x_col, y=y_col)
                            else:
                                fig = px.scatter(df, x=x_col, y=y_col, color=color_col)
                            st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.error(f"Error creating correlation visualizations: {str(e)}")
                    else:
                        st.info("Need at least 2 numeric columns for correlation analysis.")
                
                with viz_tabs[3]:  # Time Series
                    st.write("### Time Series Analysis")
                    
                    # Check for date columns
                    date_cols = []
                    for col in df.columns:
                        try:
                            pd.to_datetime(df[col])
                            date_cols.append(col)
                        except:
                            pass
                    
                    if date_cols:
                        date_col = st.selectbox("Select date column:", date_cols)
                        
                        # Convert to datetime
                        df_ts = df.copy()
                        df_ts[date_col] = pd.to_datetime(df_ts[date_col])
                        
                        # Select value column
                        value_col = st.selectbox("Select value column:", numeric_cols)
                        
                        # Resample options
                        resample_options = ['Original', 'Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly']
                        resample = st.selectbox("Resample frequency:", resample_options)
                        
                        # Prepare data based on resampling
                        if resample == 'Original':
                            plot_data = df_ts.sort_values(by=date_col)
                        else:
                            # Map selection to pandas frequency
                            freq_map = {'Daily': 'D', 'Weekly': 'W', 'Monthly': 'M', 
                                       'Quarterly': 'Q', 'Yearly': 'Y'}
                            df_ts = df_ts.set_index(date_col)
                            plot_data = df_ts[value_col].resample(freq_map[resample]).mean().reset_index()
                        
                        # Line chart
                        fig = px.line(
                            plot_data, 
                            x=date_col if resample == 'Original' else 'index', 
                            y=value_col
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No date columns detected. To perform time series analysis, ensure one of your columns contains dates.")
                
                with viz_tabs[4]:  # Text Analysis
                    st.write("### Text Analysis")
                    
                    # Check for text columns
                    text_cols = df.select_dtypes(include=['object']).columns.tolist()
                    
                    if text_cols:
                        text_col = st.selectbox("Select text column:", text_cols)
                        
                        # Word cloud
                        st.write("#### Word Cloud")
                        
                        # Join all text
                        all_text = " ".join(df[text_col].dropna().astype(str))
                        
                        if all_text.strip():
                            # Check if there are words after filtering
                            words = re.findall(r'\w+', all_text.lower())
                            stop_words = set(STOPWORDS)
                            filtered_words = [w for w in words if w not in stop_words and len(w) > 2]
                            
                            if filtered_words:  # Add this check
                                # Generate word cloud
                                wc = WordCloud(width=800, height=400, 
                                              background_color='white', 
                                              colormap='viridis', 
                                              max_words=200)
                                wc.generate(all_text)
                                
                                # Display
                                fig, ax = plt.subplots(figsize=(10, 5))
                                ax.imshow(wc, interpolation='bilinear')
                                ax.axis('off')
                                st.pyplot(fig)
                            else:
                                st.info("Not enough meaningful words to generate a word cloud after filtering.")
                            
                            # Word frequency
                            st.write("#### Top Words")
                            stop_words = set(STOPWORDS)
                            words = re.findall(r'\w+', all_text.lower())
                            word_freq = Counter([w for w in words if w not in stop_words and len(w) > 2])
                            
                            if word_freq:
                                top_words = pd.DataFrame(word_freq.most_common(20), columns=['Word', 'Count'])
                                fig = px.bar(top_words, x='Word', y='Count')
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.info("No significant words found for frequency analysis.")
                    else:
                        st.info("No text columns detected for text analysis.")
            
            # Text-specific visualizations for TXT files
            elif 'word_freq' in locals():
                with viz_tabs[0]:  # Basic Stats
                    st.write("### Text Statistics")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Words", len(words))
                    with col2:
                        st.metric("Unique Words", len(word_freq))
                    with col3:
                        st.metric("Total Characters", len(extracted_text))
                
                with viz_tabs[4]:  # Text Analysis
                    st.write("### Text Analysis")
                    
                    # Word cloud
                    st.write("#### Word Cloud")
                    if extracted_text.strip():
                        words = re.findall(r'\w+', extracted_text.lower()) # Check filtering
                        stop_words = set(STOPWORDS)
                        filtered_words = [w for w in words if w not in stop_words and len(w) > 1]
                        st.write("Filtered words:", filtered_words) 
                        
                        if filtered_words:  # Check if there are any words left after filtering
                            wordcloud_text = " ".join(filtered_words) 
                            # Generate word cloud
                            wc = WordCloud(width=800, height=400, 
                                         background_color='white', 
                                         colormap='viridis', 
                                         max_words=200)
                            wc.generate(" ".join(filtered_words))
                            
                            # Display
                            fig, ax = plt.subplots(figsize=(10, 5))
                            ax.imshow(wc, interpolation='bilinear')
                            ax.axis('off')
                            st.pyplot(fig)
                        else:
                            st.info("Not enough meaningful words to generate a word cloud. Try uploading a file with more content.")
                    else:
                         st.warning("No text content detected. Please upload a file with more words.")
                    
                    # Top words
                    st.write("#### Top Words")
                    stop_words = set(STOPWORDS)
                    filtered_words = [w for w in words if w not in stop_words and len(w) > 2]
                    
                    if filtered_words:
                        filtered_freq = Counter(filtered_words)
                        top_words = pd.DataFrame(filtered_freq.most_common(20), columns=['Word', 'Count'])
                        
                        fig = px.bar(top_words, x='Word', y='Count')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No significant words found for frequency analysis.")
                    
                    # Word length distribution
                    st.write("#### Word Length Distribution")
                    if filtered_words:
                        word_lengths = [len(w) for w in filtered_words]
                        word_length_freq = Counter(word_lengths)
                        length_df = pd.DataFrame(sorted(word_length_freq.items()), columns=['Length', 'Count'])
                        
                        fig = px.bar(length_df, x='Length', y='Count')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No significant words found for length analysis.")
                    
                    # Sentiment analysis
                    st.write("#### Sentiment Analysis")
                    if extracted_text.strip():
                        try:
                            from nltk.sentiment import SentimentIntensityAnalyzer
                            sia = SentimentIntensityAnalyzer()
                            sentiment = sia.polarity_scores(extracted_text)
                            
                            sentiment_df = pd.DataFrame({
                                'Metric': ['Negative', 'Neutral', 'Positive', 'Compound'],
                                'Value': [sentiment['neg'], sentiment['neu'], sentiment['pos'], sentiment['compound']]
                            })
                            
                            fig = px.bar(sentiment_df, x='Metric', y='Value', 
                                       color='Metric', 
                                       color_discrete_map={
                                           'Negative': 'red',
                                           'Neutral': 'gray',
                                           'Positive': 'green',
                                           'Compound': 'blue'
                                       })
                            st.plotly_chart(fig, use_container_width=True)
                        except:
                            st.info("Sentiment analysis requires NLTK with sentiment analysis models.")
                    else:
                        st.info("No text content for sentiment analysis.")
                    
                    # N-gram analysis
                    st.write("#### N-gram Analysis")
                    if filtered_words:
                        n_value = st.slider("Select n-gram size:", 2, 5, 2)
                        
                        # Generate n-grams
                        try:
                            from nltk.util import ngrams
                            n_grams = list(ngrams(filtered_words, n_value))
                            n_gram_freq = Counter([' '.join(g) for g in n_grams])
                            
                            if n_gram_freq:
                                n_gram_df = pd.DataFrame(n_gram_freq.most_common(15), 
                                                       columns=[f'{n_value}-gram', 'Count'])
                                
                                fig = px.bar(n_gram_df, x=f'{n_value}-gram', y='Count')
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.info(f"Not enough data to generate {n_value}-grams.")
                        except Exception as e:
                            st.error(f"Error in n-gram analysis: {str(e)}")
                    else:
                        st.info("Not enough text content for n-gram analysis.")

    # AI Chatbot Section
    st.subheader("💬 Chat with AI")
    user_input = st.text_area("Ask AI a question (Optional):")

    if st.button("Ask AI 🤖"):
        if extracted_text:
            prompt = f"Based on this file's content:\n{extracted_text[:3000]}\n\nAnswer the user's question: {user_input}"
        else:
            prompt = user_input  # If no file, just use user query

        response = generate_ai_content(prompt, st.session_state.api_key, st.session_state.api_model)
        st.success("🧠 AI Response:")
        st.write(response)
        
from iso639 import languages
from langdetect import detect
import pandas as pd
import docx
import json
from io import BytesIO

with tab5:
    st.header("🌍 AI-Powered Document Translator")
    
    # File uploader for document translation
    uploaded_file = st.file_uploader(
        "Upload a document (PDF, DOCX, TXT, CSV)", 
        type=["pdf", "docx", "txt", "csv"], 
        key="translator_file_uploader"
    )
    
    extracted_text = ""  # Store extracted text
    
    # Process the uploaded file and extract text
    if uploaded_file:
        extracted_text = extract_text_from_file(uploaded_file)  # Ensure this function is defined
        st.success("✅ File processed successfully!")
        st.text_area("Extracted Content:", extracted_text[:5000], height=200, key="translator_extracted_text")

    # Auto-detect source language
    detected_language = "Unknown"
    if extracted_text:
        try:
            detected_language = detect(extracted_text)
            detected_language_name = next((name for name, code in languages.items() if code == detected_language), "Unknown")
            st.info(f"🔍 Detected Source Language: **{detected_language_name} ({detected_language})**")
        except:
            st.warning("⚠️ Could not detect language. Please specify manually.")

    # Advanced translation options
    with st.expander("Advanced Translation Options"):
        translation_mode = st.selectbox(
            "Translation Mode:", 
            ["Full Translation", "Summary Translation", "Paraphrase Translation", "Technical Translation"], 
            key="translator_mode"
        )
        tone = st.selectbox(
            "Translation Tone:", 
            ["Formal", "Informal", "Neutral", "Friendly", "Academic"], 
            key="translator_tone"
        )
        output_format = st.selectbox(
            "Output Format:", 
            ["Plain Text", "Markdown", "HTML", "DOCX", "CSV", "JSON"], 
            key="translator_format"
        )
        max_chars = st.slider(
            "Max Characters to Translate:", 
            min_value=1000, max_value=20000, value=5000, step=500, 
            key="translator_max_chars"
        )
        parallel_translation = st.checkbox("Enable Parallel Translations (Compare Multiple Translations)", key="parallel_translation")
        pronunciation = st.checkbox("Include Pronunciation (For Language Learning)", key="pronunciation")

    # Fetch 200+ languages dynamically
    all_languages = {lang.name: lang.part1 for lang in languages if lang.part1}  # Get name & ISO code

    # Streamlit selectbox for choosing target language
    target_lang = st.selectbox(
        "Select Target Language:", 
        list(all_languages.keys()), 
        key="translator_language_select"
    )
    
    # Translation button and display translation
    if st.button("Translate 🌍", key="translator_translate_btn"):
        if extracted_text:
            lang_code = all_languages[target_lang]  # Convert display name to language code
            text_to_translate = extracted_text[:max_chars]  # Limit text length
            
            # Build an advanced prompt with options
            prompt = (
                f"Translation Mode: {translation_mode}\n"
                f"Tone: {tone}\n"
                f"Output Format: {output_format}\n"
                f"Pronunciation: {'Yes' if pronunciation else 'No'}\n"
                f"Translate the following text to {target_lang} ({lang_code}):\n\n{text_to_translate}"
            )
            
            translated_text = generate_ai_content(prompt, st.session_state.api_key, st.session_state.api_model)
            st.success("✅ Translation Complete:")
            st.write(translated_text)
            
            # Parallel Translations (if enabled)
            if parallel_translation:
                st.subheader("🔄 Parallel Translations")
                alternate_prompt = f"Provide an alternate translation for the text in {target_lang} ({lang_code}):\n\n{text_to_translate}"
                alternate_translation = generate_ai_content(alternate_prompt, st.session_state.api_key, st.session_state.api_model)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### 🎯 Primary Translation")
                    st.write(translated_text)
                with col2:
                    st.markdown("### 🛠 Alternate Translation")
                    st.write(alternate_translation)

            # Create downloadable DOCX file
            def create_docx(text):
                doc = docx.Document()
                doc.add_paragraph(text)
                doc_stream = BytesIO()
                doc.save(doc_stream)
                doc_stream.seek(0)  # Move to the beginning of the file
                return doc_stream
            
            # Create downloadable CSV file
            def create_csv(text):
                csv_data = pd.DataFrame([[target_lang, text]], columns=["Language", "Translation"])
                csv_stream = BytesIO()
                csv_data.to_csv(csv_stream, index=False)
                csv_stream.seek(0)
                return csv_stream

            # Export and copy options
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.download_button(
                    "Download as TXT", 
                    translated_text, 
                    file_name=f"translation_{target_lang}.txt"
                )
            with col2:
                docx_file = create_docx(translated_text)
                st.download_button(
                    "Download as DOCX", 
                    docx_file,  # ✅ Fixed: Pass binary stream instead of docx object
                    file_name=f"translation_{target_lang}.docx"
                )
            with col3:
                csv_file = create_csv(translated_text)
                st.download_button(
                    "Download as CSV", 
                    csv_file, 
                    file_name=f"translation_{target_lang}.csv"
                )
            with col4:
                st.download_button(
                    "Download as JSON", 
                    json.dumps({"language": target_lang, "text": translated_text}), 
                    file_name=f"translation_{target_lang}.json"
                )

        else:
            st.warning("⚠️ Please upload a document first!")


with tab6:
    st.header("⚡ AI Code Wizard")

    # Automatically select the AI model for coding tasks
    st.session_state.api_model = "gemini-2.0-flash-thinking-exp-01-21"

    # Choose AI task
    task = st.selectbox("What do you need help with?", 
                    ["Generate Code", "Debug Code", "Optimize Code", "Convert Code", "Explain Code",
                     "Add Comments", "Find Security Issues", "Write Unit Tests", "Generate API Documentation",
                     "Suggest Design Patterns", "Convert Pseudocode to Code", "Fix Compilation Errors",
                     "Analyze Code Performance"], 
                    key="code_task_radio")

    # Code Input (Text or File)
    code_input = st.text_area("Enter your code or request:", height=200, key="code_input")

    uploaded_code = st.file_uploader("Upload a code file", type=["py", "js", "cpp", "java", "vhdl"], key="code_file_uploader")
    
    if uploaded_code:
        code_input = uploaded_code.read().decode("utf-8")
        st.text_area("Uploaded Code:", code_input, height=200, key="uploaded_code_display")

    # AI Action Button
    if st.button("✨ Magic Code AI", key="code_magic_button"):
        if code_input.strip():
            if task == "Generate Code":
                prompt = f"Write clean, efficient code for: {code_input}"
            elif task == "Debug Code":
                prompt = f"Find and fix errors in this code:\n\n{code_input}"
            elif task == "Optimize Code":
                prompt = f"Refactor and optimize this code to improve efficiency:\n\n{code_input}"
            elif task == "Convert Code":
                prompt = f"Convert this code to another programming language:\n\n{code_input}"
            elif task == "Explain Code":
                prompt = f"Explain what this code does in simple terms:\n\n{code_input}"
            elif task == "Add Comments":
                prompt = f"Add detailed comments to this code for better understanding:\n\n{code_input}"
            elif task == "Find Security Issues":
                prompt = f"Analyze this code and highlight security vulnerabilities:\n\n{code_input}"
            elif task == "Write Unit Tests":
                prompt = f"Generate unit tests for this code:\n\n{code_input}"
            elif task == "Generate API Documentation":
                prompt = f"Create API documentation for this code:\n\n{code_input}"
            elif task == "Suggest Design Patterns":
                prompt = f"Suggest an appropriate design pattern for this code and explain why:\n\n{code_input}"
            elif task == "Convert Pseudocode to Code":
                prompt = f"Convert this pseudocode into actual code:\n\n{code_input}"
            elif task == "Fix Compilation Errors":
                prompt = f"Fix the compilation errors in this code:\n\n{code_input}"
            elif task == "Analyze Code Performance":
                prompt = f"Analyze the performance of this code and suggest improvements:\n\n{code_input}"

            # AI Code Processing
            ai_response = generate_ai_content(prompt, st.session_state.api_key, st.session_state.api_model)

            st.success("✨ AI Code Response:")
            st.code(ai_response, language="python")  # Adjust language based on task
        else:
            st.warning("⚠️ Please enter some code or upload a file.")

# Content generation section
st.header("✨ Create Content")
# Add this under the 'Generate Content' section

# Display selected tool or default
selected_tool = st.session_state.get('selected_tool', 'Smart Content Creator')
st.markdown(f"### Currently using: **{selected_tool}**")

# Content prompt area
st.text_area("Extracted Content:", extracted_text[:5000], height=200, key="translator_text_area")


# Advanced options expander
# Advanced options expander
with st.expander("⚙️ Advanced Options"):
    # Document structure tabs
    tabs = st.tabs(["Template", "Content Style", "Structure", "Format", "Generation"])
    
    with tabs[0]:
        template_edit = st.text_area(
            "Customize prompt template (use {prompt} as placeholder for your input):",
            value=st.session_state.prompt_templates.get(selected_tool, "Create {prompt}"),
            height=100
        )
        st.session_state.prompt_templates[selected_tool] = template_edit
        
        # Template presets
        st.divider()
        col1, col2 = st.columns([3, 1])
        with col1:
            template_presets = {
                "Standard": "Create {prompt}",
                "Detailed Analysis": "Conduct a comprehensive analysis of {prompt}, including key insights, trends, and recommendations.",
                "Creative Writing": "Write a creative and engaging piece about {prompt} with vivid descriptions and compelling narrative.",
                "Business Report": "Generate a professional business report about {prompt} with executive summary, analysis, and actionable recommendations.",
                "Technical Guide": "Create a detailed technical guide for {prompt} with step-by-step instructions, code examples, and troubleshooting tips."
            }
            selected_preset = st.selectbox("Template Presets:", list(template_presets.keys()))
        with col2:
            if st.button("Apply Preset"):
                st.session_state.prompt_templates[selected_tool] = template_presets[selected_preset]
                st.rerun()

    
    with tabs[1]:
        # Writing style options
        col1, col2 = st.columns(2)
        with col1:
            response_length = st.selectbox(
                "Response Length:", ["Short", "Medium", "Long", "Very Short", "Concise", "Brief", "Detailed", "Extensive", "Summary", "In-depth", "Comprehensive", "Elaboration", "Thorough"]
,index=1  # Default to Medium
            )
            tone = st.selectbox(
                "Tone:",
                ["Professional", "Casual", "Academic", "Persuasive", "Inspirational", 
                 "Technical", "Conversational", "Humorous", "Formal", "Storytelling", 
                 "Authoritative", "Empathetic", "Neutral", "Enthusiastic", "Thoughtful"]
            )
            voice = st.selectbox(
                "Voice:",
                ["Active", "Passive", "First Person", "Second Person", "Third Person", 
                 "Objective", "Subjective", "Instructional", "Narrative", "Analytical"]
            )
            
        with col2:
            audience = st.selectbox(
                "Target Audience:",
                ["General", "Technical", "Executive", "Academic", "Marketing", 
                 "Education", "Healthcare", "Financial", "Legal", "Scientific",
                 "Children", "Teenagers", "Senior Management", "Beginners", "Advanced"]
            )
            industry = st.selectbox(
                "Industry Focus:",
                ["General", "Technology", "Healthcare", "Finance", "Education", 
                 "Entertainment", "Legal", "Marketing", "Science", "Engineering", 
                 "Manufacturing", "Retail", "Government", "Nonprofit", "Energy"]
            )
        
        # Language style 
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            language_style = st.selectbox(
                "Language Style:",
                ["Standard", "Simple", "Technical", "Poetic", "Journalistic", 
                 "Business", "Academic", "Conversational", "Persuasive", "Narrative"]
            )
            emotion = st.select_slider(
                "Emotional Intensity:",
                options=["Neutral", "Subtle", "Moderate", "Strong", "Intense"],
                value="Moderate"
            )
        with col2:
            formality = st.select_slider(
                "Formality Level:",
                options=["Very Casual", "Casual", "Neutral", "Formal", "Very Formal"],
                value="Neutral"
            )
            persona = st.selectbox(
                "Writing Persona:",
                ["Default", "Expert", "Teacher", "Coach", "Journalist", 
                 "Storyteller", "Analyst", "Researcher", "Consultant", "Mentor"]
            )
    
    with tabs[2]:
        col1, col2 = st.columns(2)
        with col1:
            max_words = st.number_input("Maximum Word Count:", min_value=50, max_value=10000, value=500, step=50)
            min_words = st.number_input("Minimum Word Count:", min_value=10, max_value=5000, value=100, step=50)
            complexity = st.select_slider(
                "Language Complexity:",
                options=["Elementary", "Middle School", "High School", "College", "Graduate", "Expert", "Technical"],
                value="College"
            )
        
        with col2:
            keyword_inclusion = st.text_area("Keywords to Include (comma separated):", height=68)
            forbidden_words = st.text_area("Words to Avoid (comma separated):", height=68)
            readability_target = st.slider("Readability Score Target:", 
                                          min_value=0, max_value=100, value=60, step=5, 
                                          help="Lower = more complex, Higher = simpler")
        
        # Structure options
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            structure_type = st.selectbox(
                "Content Structure:",
                ["Standard", "Problem-Solution", "Comparison", "Chronological", 
                 "Cause-Effect", "Spatial", "Process", "Thesis-Led", "Data-Led", 
                 "Argumentative", "Descriptive", "Exploratory", "Instructional"]
            )
            emphasis = st.selectbox(
                "Content Emphasis:",
                ["Balanced", "Data-Focused", "Process-Focused", "Outcome-Focused", 
                 "Analysis-Focused", "Solution-Focused", "Context-Focused"]
            )
        with col2:
            sections = st.multiselect(
                "Required Sections:",
                ["Introduction", "Background", "Methodology", "Results", "Discussion", 
                 "Conclusion", "Executive Summary", "Recommendations", "References", 
                 "Appendix", "FAQ", "Glossary", "Abstract", "Literature Review", 
                 "Case Studies", "Implementation", "Limitations", "Future Work"]
            )
            argument_style = st.selectbox(
                "Argument Style:",
                ["Balanced", "Steelmanning", "Devil's Advocate", "Persuasive", 
                 "Exploratory", "Socratic", "Analytical", "Comparative"]
            )
    
    with tabs[3]:
        col1, col2 = st.columns(2)
        with col1:
            output_format = st.selectbox(
                "Output Format:",
                ["Standard Text", "Markdown", "HTML", "JSON", "CSV", "Outline", 
                 "Bullet Points", "Q&A Format", "Table", "Script Format", 
                 "Newsletter", "Blog Post", "Academic Paper", "Business Report", 
                 "Technical Documentation", "Speech/Presentation"]
            )
            citation_style = st.selectbox(
                "Citation Style:",
                ["None", "APA", "MLA", "Chicago", "IEEE", "Harvard", "Vancouver", 
                 "AMA", "ASA", "Bluebook", "CSE", "ACS", "NLM"]
            )
        
        with col2:
            layout_style = st.selectbox(
                "Layout Style:",
                ["Standard", "Minimal", "Hierarchical", "Segmented", "Web-Optimized", 
                 "Print-Optimized", "Mobile-Optimized", "Presentation", "Technical"]
            )
            visual_elements = st.multiselect(
                "Visual Elements:",
                ["None", "Tables", "Lists", "Blockquotes", "Code Blocks", "Headings", 
                 "Sub-headings", "Bold Emphasis", "Italics", "Horizontal Rules", 
                 "Indentation"]
            )
            
        # Media and formatting
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            formatting_style = st.selectbox(
                "Formatting Style:",
                ["Standard", "Minimal", "Academic", "Web", "Print", "Journalistic", 
                 "Technical Document", "Creative", "Business", "Scientific"]
            )
        with col2:
            syntax_highlighting = st.selectbox(
                "Code Syntax Highlighting:",
                ["None", "Standard", "GitHub", "VSCode", "Atom", "Sublime"]
            )
    
    with tabs[4]:
        # Generation parameters
        col1, col2 = st.columns(2)
        with col1:
            output_length = st.select_slider(
                "Output Detail Level:",
                options=["Minimal", "Brief", "Standard", "Detailed", "Comprehensive", "Exhaustive"],
                value="Standard"
            )
            creativity = st.slider("Creativity:", min_value=0.0, max_value=1.0, value=0.7, step=0.1,
                                help="Lower = more deterministic, Higher = more creative")
        
        with col2:
            determinism = st.slider("Determinism:", min_value=0.0, max_value=1.0, value=0.3, step=0.1,
                                help="Lower = more varied outputs, Higher = more consistent outputs")
            reasoning_depth = st.select_slider(
                "Reasoning Depth:",
                options=["Basic", "Standard", "Advanced", "Expert", "Comprehensive"],
                value="Standard",
                help="Controls depth of logical analysis and reasoning in generated content"
            )
        
        # Advanced AI parameters
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            factuality = st.slider("Factuality Weight:", min_value=0.0, max_value=1.0, value=0.8, step=0.1,
                                help="Higher values prioritize factual accuracy over creativity")
            expertise_level = st.select_slider(
                "AI Expertise Level:",
                options=["Generalist", "Field Expert", "Subject Specialist", "Domain Authority", "World-Class Expert"],
                value="Field Expert",
                help="Level of expertise the AI should demonstrate in the response"
            )
        
        with col2:
            context_relevance = st.slider("Context Relevance:", min_value=0.0, max_value=1.0, value=0.9, step=0.1,
                                      help="Higher values keep content more focused on the specific prompt")
            innovation_level = st.select_slider(
                "Innovation Level:",
                options=["Conservative", "Balanced", "Progressive", "Cutting-Edge", "Revolutionary"],
                value="Balanced",
                help="Controls how novel or traditional the ideas and approach should be"
            )
        
        # Specialized content options
        st.divider()
        st.subheader("Specialized Content Options")
        st.info("Select additional content features to include in generation")
        col1, col2, col3 = st.columns(3)
        with col1:
            tech_analysis = st.checkbox("Enable Technical Analysis", help="Add technical depth with specialized terminology")
            data_viz = st.checkbox("Include Data Visualization", help="Add descriptions of charts/graphs where appropriate")
            case_studies = st.checkbox("Add Case Studies", help="Include relevant examples and case studies")
        
        with col2:
            research_focus = st.checkbox("Research Focus", help="Emphasize research findings and methodologies")
            step_breakdown = st.checkbox("Step-by-Step Breakdown", help="Include detailed procedural explanations")
            comparative = st.checkbox("Comparative Analysis", help="Include comparisons to alternatives or competitors")
        
        with col3:
            future_trends = st.checkbox("Future Trends", help="Include predictions and future developments")
            historical = st.checkbox("Historical Context", help="Add historical background and evolution")
            expert_citations = st.checkbox("Expert Citations", help="Include references to subject matter experts")

# Add style instructions to prompt based on selections
style_instructions = {
    "Response Length": response_length,
    "tone": tone,
    "voice": voice,
    "audience": audience,
    "industry": industry,
    "max_words": max_words,
    "min_words": min_words,
    "output_format": output_format,
    "structure_type": structure_type,
    "sections": sections,
    "output_length": output_length,
    "creativity": creativity,
    "reasoning_depth": reasoning_depth
}

# Store parameters to session state for use in prompt building
st.session_state.style_instructions = style_instructions
# Export/Import functionality
st.sidebar.markdown("---")
st.sidebar.markdown("### 💾 Export/Import History")

# Export history
if st.session_state.history and st.sidebar.button("📤 Export History"):
    history_json = json.dumps(st.session_state.history)
    b64_history = base64.b64encode(history_json.encode()).decode()
    href = f'<a href="data:application/json;base64,{b64_history}" download="ai_content_history.json">Download History File</a>'
    st.sidebar.markdown(href, unsafe_allow_html=True)

# Import history
uploaded_file = st.sidebar.file_uploader("Import History:", type=['json'])
if uploaded_file is not None:
    try:
        imported_history = json.loads(uploaded_file.read())
        if st.sidebar.button("📥 Load Imported History"):
            st.session_state.history = imported_history
            st.sidebar.success("History imported successfully!")
    except Exception as e:
        st.sidebar.error(f"Error importing history: {e}")

# Generate button and output area
if st.button("🚀 Generate Content", type="primary"):
    if not st.session_state.api_key:
        st.error("Please enter your API key in the sidebar first.")
    elif not user_prompt:
        st.warning("Please enter a prompt to generate content.")
    else:
        # Build prompt with template and style instructions
        template = st.session_state.prompt_templates.get(selected_tool, "Create {prompt}")
        formatted_prompt = template.replace("{prompt}", user_prompt)
        
        # Add style instructions to prompt
        style_prompt = f"{formatted_prompt}\n\nStyle Guidelines:\n"
        for key, value in st.session_state.style_instructions.items():
            if value and value not in ["None", "Standard"] and (not isinstance(value, list) or len(value) > 0):
                style_prompt += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        # Generate content
        output = generate_ai_content(style_prompt, st.session_state.api_key, st.session_state.api_model)
        
        # Display output
        st.markdown("### 🎯 Generated Content")
        with st.expander("Content Output", expanded=True):
            st.markdown(output)
        
        # Save to history
        save_to_history(selected_tool, user_prompt, output)
              
# Add theme selector
st.sidebar.markdown("---")
st.sidebar.markdown("### 🎨 App Theme")
themes = ["Light", "Dark", "Blue", "Green", "Purple"]
selected_theme = st.sidebar.selectbox("Select Theme:", themes, index=0)

# Apply selected theme with custom CSS
theme_colors = {
    "Light": {"bg": "#f8f9fa", "accent": "#3b82f6"},
    "Dark": {"bg": "#1e293b", "accent": "#8b5cf6"},
    "Blue": {"bg": "#f0f9ff", "accent": "#0284c7"},
    "Green": {"bg": "#f0fdf4", "accent": "#16a34a"},
    "Purple": {"bg": "#faf5ff", "accent": "#9333ea"}
}

theme_css = f"""
<style>
    .main {{ background-color: {theme_colors[selected_theme]["bg"]} }}
    .stButton>button {{ background: linear-gradient(90deg, {theme_colors[selected_theme]["accent"]}, {theme_colors[selected_theme]["accent"]}88) }}
</style>
"""
st.sidebar.markdown(theme_css, unsafe_allow_html=True)
