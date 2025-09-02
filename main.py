import os
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.eleven_labs import ElevenLabsTools
from agno.tools.firecrawl import FirecrawlTools
from agno.agent import RunResponse
from agno.utils.audio import write_audio_to_file
from agno.utils.log import logger
import streamlit as st
import uuid

st.set_page_config(page_title="Blog to Podcast")
st.title("friendly blog to podcast agent")


openAI_api_key=""
eleven_labs_api_key=""
firecrawl_api_key=""

keys_provided= all([openAI_api_key, eleven_labs_api_key, firecrawl_api_key])
url=st.text_input("Enter the Blog URL","")
generate_button=st.button("generate podcast") 


if generate_button==True:
    if url.strip()=="":
        st.warning("Please enter a valid URL")
    else:
        os.environ["OPENAI_API_KEY"]=openAI_api_key
        os.environ["ELEVENLABS_API_KEY"]=eleven_labs_api_key
        os.environ["FIRECRAWL_API_KEY"]=firecrawl_api_key

        with st.spinner("Processing...,Scraping Blog,Summarizing and generating podcast!"):
            try:
                blog_to_podcast= Agent(
                    name="Blog to Podcast",
                    agent_id="blog_to_podcast Agent",
                    model=OpenAIChat(id="gpt-4.1"),
                    tools=[
                        ElevenLabsTools(
                           voice_id="ElevenLabs",
                           model_id="eleven_multilingual_v2",
                           target_directory="audio_generations"
                        ),
                        FirecrawlTools(),

                           
                    ],
                    description="You are an AI agent that can generate voice over for a given blog URL ",
                    instructions=[
                        "when the user gives you the url of a blog website",
                        "1.Use firecrawltools to scrape the given blog post",
                        "2. create a concise summary of the given blog post NO MORE than 2000 characters",
                        "3. you should capture the important details of the blog post",
                        "4. since you are turning it into a podcast make the language more casual and friendly type",
                        "5 use the ElevenLabsTools to convert the generated summary into an engaging audio",
                    ],
                    markdown=True,
                    debug_mode=True
                )   
                podcast: RunResponse=blog_to_podcast.run(
                    f"convert the blog content into an engaging podcast:{url}"

                )
                save_dir="audio_generations"
                os.makedirs(save_dir,exist_ok=True)

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
                else:
                    st.error("No audio was generated.Please try again")
            except Exception as e:
                st.error(f"an error occured:{e}")
                logger.error(f"Streamlit app error:{e}")







