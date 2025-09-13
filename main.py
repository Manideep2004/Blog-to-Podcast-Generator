import os
from dotenv import load_dotenv

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY", "")
eleven_labs_api_key = os.getenv("ELEVENLABS_API_KEY", "")
firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY", "")

from agno.agent import Agent
from agno.models.google.gemini import Gemini
from agno.tools.firecrawl import FirecrawlTools
from agno.agent import RunOutput
from agno.utils.audio import write_audio_to_file
from agno.utils.log import logger
import streamlit as st
import uuid
import PyPDF2
import io
import requests
import base64

st.set_page_config(page_title="Content to Podcast Generator")
st.title("🎙️ Content to Podcast Generator")
st.write("Convert blog posts, PDF documents, or any text into engaging audio podcasts!")

keys_provided= all([gemini_api_key, eleven_labs_api_key, firecrawl_api_key])

# Display API key status
st.write(f"Gemini API Key: {'✓' if gemini_api_key else '✗'}")
st.write(f"ElevenLabs API Key: {'✓' if eleven_labs_api_key else '✗'}")
st.write(f"Firecrawl API Key: {'✓' if firecrawl_api_key else '✗'}")

# Input type selection
input_type = st.radio("Choose input type:", ["Blog URL", "PDF File", "Text Input"])

if input_type == "Blog URL":
    url = st.text_input("Enter the Blog URL:", "")
    pdf_file = None
    text_input = None
elif input_type == "PDF File":
    url = None
    pdf_file = st.file_uploader("Upload a PDF file:", type=['pdf'])
    text_input = None
else:  # Text Input
    url = None
    pdf_file = None
    text_input = st.text_area("Paste your text here:", height=200, placeholder="Enter any text, paragraph, or content you want to convert to a podcast...")

def extract_text_from_pdf(pdf_file):
    """Extract text content from uploaded PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

def generate_audio_with_elevenlabs(text, voice_id="21m00Tcm4TlvDq8ikWAM"):
    """Generate audio using ElevenLabs API directly"""
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": eleven_labs_api_key
        }
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return response.content
        else:
            st.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error generating audio: {e}")
        return None

generate_button = st.button("🎵 Generate Podcast") 


if generate_button==True:
    # Validate inputs based on type
    if input_type == "Blog URL" and (not url or url.strip() == ""):
        st.warning("Please enter a valid URL")
    elif input_type == "PDF File" and pdf_file is None:
        st.warning("Please upload a PDF file")
    elif input_type == "Text Input" and (not text_input or text_input.strip() == ""):
        st.warning("Please enter some text to convert")
    elif not keys_provided:
        st.error("Please check your .env file and ensure all API keys are properly set")
    else:
        os.environ["ELEVENLABS_API_KEY"]=eleven_labs_api_key
        os.environ["ELEVEN_LABS_API_KEY"]=eleven_labs_api_key  # ElevenLabsTools expects this format
        os.environ["FIRECRAWL_API_KEY"]=firecrawl_api_key
        os.environ["GEMINI_API_KEY"]=gemini_api_key

        # Prepare content based on input type
        if input_type == "Blog URL":
            content_source = f"blog URL: {url}"
            spinner_text = "Processing... Scraping blog, summarizing and generating podcast!"
        elif input_type == "PDF File":
            # Extract text from PDF
            pdf_text = extract_text_from_pdf(pdf_file)
            if pdf_text is None:
                st.error("Failed to extract text from PDF")
                st.stop()
            
            # Truncate if too long (PDFs can be very long)
            if len(pdf_text) > 10000:  # Limit to first 10k characters
                pdf_text = pdf_text[:10000] + "..."
                st.info("PDF is very long, using first 10,000 characters")
            
            content_source = f"PDF content: {pdf_text}"
            spinner_text = "Processing... Analyzing PDF, summarizing and generating podcast!"
        else:  # Text Input
            # Use the text directly
            content_source = f"text content: {text_input}"
            spinner_text = "Processing... Analyzing text, summarizing and generating podcast!"

        with st.spinner(spinner_text):
            try:
                # Create agent for content processing (without ElevenLabsTools)
                tools = []
                
                # Only add FirecrawlTools for blog URLs
                if input_type == "Blog URL":
                    tools.append(FirecrawlTools())

                content_processor = Agent(
                    name="Content Processor",
                    id="content_processor_agent",
                    model=Gemini(id="gemini-2.5-flash", api_key=gemini_api_key),
                    tools=tools,
                    description="You are an AI agent that processes content for podcast generation",
                    instructions=[
                        f"when the user provides {input_type.lower()}",
                        "1. If it's a blog URL, use firecrawltools to scrape the content. If scraping fails, inform the user about the issue",
                        "2. If it's PDF content, analyze the provided text directly",
                        "3. If it's text content, analyze the provided text directly",
                        "4. Create a concise summary NO MORE than 2000 characters",
                        "5. Capture the important details and main points",
                        "6. Since you are turning it into a podcast, make the language casual and friendly",
                        "7. Return ONLY the summary text - do not mention audio generation",
                        "8. If you cannot process the content, provide a helpful error message to the user",
                    ],
                    markdown=True,
                    debug_mode=True
                )   
                
                # Process content to get summary
                content_result: RunOutput = content_processor.run(
                    f"process the {input_type.lower()} content and create a podcast-friendly summary: {content_source}"
                )
                
                # Check if content processing was successful
                if not content_result.content or "trouble accessing" in content_result.content.lower() or "error" in content_result.content.lower():
                    st.error("Failed to process content. Please check the input and try again.")
                    st.write("**Error details:**")
                    st.write(content_result.content)
                    st.stop()
                
                # Generate audio using our custom function
                st.write("**📝 Generated Summary:**")
                st.write(content_result.content)
                
                with st.spinner("🎵 Generating audio..."):
                    audio_data = generate_audio_with_elevenlabs(content_result.content)
                    
                if audio_data:
                    # Save audio file
                    save_dir = "audio_generations"
                    os.makedirs(save_dir, exist_ok=True)
                    filename = f"{save_dir}/podcast_{uuid.uuid4()}.wav"
                    
                    with open(filename, "wb") as f:
                        f.write(audio_data)
                    
                    st.success("🎉 Podcast Generated Successfully!")
                    
                    # Display audio player
                    st.audio(audio_data, format="audio/mpeg")
                    
                    # Download button
                    st.download_button(
                        label="📥 Download The Generated Podcast",
                        data=audio_data,
                        file_name="generated_podcast.mp3",
                        mime="audio/mpeg",
                    )
                else:
                    st.error("Failed to generate audio. Please check your ElevenLabs API key and credits.")
            except Exception as e:
                st.error(f"an error occured:{e}")
                logger.error(f"Streamlit app error:{e}")







