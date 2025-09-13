import os
from dotenv import load_dotenv

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY", "")
eleven_labs_api_key = os.getenv("ELEVENLABS_API_KEY", "")
firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY", "")

from agno.agent import Agent
from agno.models.google.gemini import Gemini
from agno.tools.eleven_labs import ElevenLabsTools
from agno.tools.firecrawl import FirecrawlTools
from agno.agent import RunOutput
from agno.utils.audio import write_audio_to_file
from agno.utils.log import logger
import streamlit as st
import uuid

st.set_page_config(page_title="Blog to Podcast")
st.title("friendly blog to podcast agent")


keys_provided= all([gemini_api_key, eleven_labs_api_key, firecrawl_api_key])

# Display API key status
st.write(f"Gemini API Key: {'✓' if gemini_api_key else '✗'}")
st.write(f"ElevenLabs API Key: {'✓' if eleven_labs_api_key else '✗'}")
st.write(f"Firecrawl API Key: {'✓' if firecrawl_api_key else '✗'}")

url=st.text_input("Enter the Blog URL","")
generate_button=st.button("generate podcast") 


if generate_button==True:
    if url.strip()=="":
        st.warning("Please enter a valid URL")
    elif not keys_provided:
        st.error("Please check your .env file and ensure all API keys are properly set")
    else:
        os.environ["ELEVENLABS_API_KEY"]=eleven_labs_api_key
        os.environ["FIRECRAWL_API_KEY"]=firecrawl_api_key
        os.environ["GEMINI_API_KEY"]=gemini_api_key

        with st.spinner("Processing...,Scraping Blog,Summarizing and generating podcast!"):
            try:
                blog_to_podcast= Agent(
                    name="Blog to Podcast",
                    id="blog_to_podcast Agent",
                    model=Gemini(id="gemini-2.5-flash", api_key=gemini_api_key),
                    tools=[
                        ElevenLabsTools(
                           voice_id="pNInz6obpgDQGcFmaJgB",  # Adam voice ID
                           model_id="eleven_multilingual_v2",
                           target_directory="audio_generations"
                        ),
                        FirecrawlTools(),

                           
                    ],
                    description="You are an AI agent that can generate voice over for a given blog URL ",
                    instructions=[
                        "when the user gives you the url of a blog website",
                        "1. Use firecrawltools to scrape the given blog post. If scraping fails, inform the user about the issue and ask them to provide the blog content directly or try a different URL",
                        "2. If scraping is successful, create a concise summary of the given blog post NO MORE than 2000 characters",
                        "3. You should capture the important details of the blog post",
                        "4. Since you are turning it into a podcast make the language more casual and friendly type",
                        "5. Use the ElevenLabsTools to convert the generated summary into an engaging audio",
                        "6. If you cannot access the blog content, do not attempt to generate audio - instead, provide a helpful error message to the user",
                    ],
                    markdown=True,
                    debug_mode=True
                )   
                podcast: RunOutput=blog_to_podcast.run(
                    f"convert the blog content into an engaging podcast:{url}"

                )
                save_dir="audio_generations"
                os.makedirs(save_dir,exist_ok=True)

                # Debug information
                st.write(f"Podcast object type: {type(podcast)}")
                st.write(f"Podcast has audio attribute: {hasattr(podcast, 'audio')}")
                if hasattr(podcast, 'audio'):
                    st.write(f"Podcast audio: {podcast.audio}")
                    st.write(f"Podcast audio length: {len(podcast.audio) if podcast.audio else 'None'}")
                
                # Show the content to help debug
                if hasattr(podcast, 'content'):
                    st.write("**Agent Response:**")
                    st.write(podcast.content)
                else:
                    st.write("No content attribute found")

                if podcast.audio and len(podcast.audio)>0:
                    filename=f"{save_dir}/podcast_{uuid.uuid4()}.wav"
                    write_audio_to_file(
                        audio=podcast.audio[0].base64_audio,
                        filename=filename,
                    )
                    st.success("Podcast Generated Successfully")
                    audio_bytes=open(filename,"rb").read()

                    st.audio(audio_bytes,format="audio/wav")
                    st.download_button(
                        label="Download The Generated Podcast",
                        data=audio_bytes,
                        file_name="generated_podcast.wav",
                        mime="audio/wav",
                    )
                elif hasattr(podcast, 'content') and podcast.content and "trouble accessing" not in podcast.content.lower():
                    st.warning("Content was processed but no audio was generated. This might be due to ElevenLabs API issues or the content being too long.")
                    st.write("**Processed Content:**")
                    st.write(podcast.content)
                else:
                    st.error("No audio was generated. This could be due to:")
                    st.write("- Firecrawl couldn't access the blog URL (check if the URL is correct and accessible)")
                    st.write("- ElevenLabs API issues (check your API key and credits)")
                    st.write("- The blog content might be too long or in an unsupported format")
            except Exception as e:
                st.error(f"an error occured:{e}")
                logger.error(f"Streamlit app error:{e}")







