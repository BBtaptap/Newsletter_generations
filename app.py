import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional 
from datetime import datetime  # For date handling
# LangChain components
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun  # Simple search tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub  # To pull standard ReAct prompt templates
from langchain_community.tools import ArxivQueryRun  # LangChain's built-in Arxiv tool

# --- Configuration & Setup ---
load_dotenv()
logging_enabled = True  # Set to True to see logs, False to hide them

# Optional: Configure logging to see less verbose LangChain internal logs if desired
if not logging_enabled:
    import logging
    logging.getLogger('langchain').setLevel(logging.ERROR)
    logging.getLogger('httpx').setLevel(logging.ERROR)  # httpx is used by some clients

# Check for API key
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY not found in .env file")

class NewsletterContent(BaseModel):
    """
    Represents the structured content for the Blackbucks Weekly AI Digest.
    """
    figure_name: str = Field(..., description="Filename of the header image.", alias="FIGURE_NAME")
    quote_1: str = Field(..., description="First AI-related quote.", alias="Quote-1")
    quote_2: str = Field(..., description="Second AI-related quote.", alias="Quote-2")
    description: str = Field(..., description="Short description of AI trends for the week.", alias="Description")

    title_1: str = Field(..., description="Title of the first headline research paper.", alias="Title-1")
    summary_1: str = Field(..., description="Summary of the first headline research paper.", alias="Summary-1")
    takeaway_1: str = Field(..., description="Key takeaway from the first headline research paper.", alias="Takeaway-1")

    title_2: str = Field(..., description="Title of the second headline research paper.", alias="Title-2")
    summary_2: str = Field(..., description="Summary of the second headline research paper.", alias="Summary-2")
    takeaway_2: str = Field(..., description="Key takeaway from the second headline research paper.", alias="Takeaway-2")

    title_3: str = Field(..., description="Title of the third headline research paper.", alias="Title-3")
    summary_3: str = Field(..., description="Summary of the third headline research paper.", alias="Summary-3")
    takeaway_3: str = Field(..., description="Key takeaway from the third headline research paper.", alias="Takeaway-3")

    main_paper_title: str = Field(..., description="Title of the main foundational research paper highlighted.", alias="Mainpaper_title")
    main_paper_description: str = Field(..., description="Description/summary of the main foundational paper.", alias="Mainpaper_description")

    featured_title: str = Field(..., description="Title of the featured research paper.", alias="fTitle")
    featured_published_in: str = Field(..., description="Publication details (e.g., journal, conference, arXiv ID).", alias="Published_in")
    featured_summary: str = Field(..., description="Summary of the featured research paper.", alias="fsummary")

# --- Initialize LLM ---
llm = ChatGroq(
    temperature=0,  # Low temperature for more deterministic reasoning
    groq_api_key=groq_api_key,
    model_name="llama3-70b-8192"
)

# --- Define Tools ---
search_tool = DuckDuckGoSearchRun()
arxiv_tool = ArxivQueryRun()

tools = [search_tool, arxiv_tool]

# --- Create the ReAct Agent ---
prompt = hub.pull("hwchase17/react")

# 2. Create the Agent
agent = create_react_agent(llm, tools, prompt)

# 3. Create the Agent Executor
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,  # This shows the thought process
    handle_parsing_errors=True,
    max_iterations=10  # Increased iterations to allow more time for generating content
)

# --- Run the Agent ---
if __name__ == "__main__":
    print("--- Starting ReAct Agent ---")
    
    # Get the current date to use in the newsletter
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Draft the question for generating the newsletter with the current date included
    question = f"""
    Create a newsletter for the Blackbucks Weekly AI Digest for {current_date}. The newsletter should include:
    - A header image filename
    - Two AI-related quotes given by someone online
    - A description of the latest AI trends for the week
    - Get top 5 recent research papers fron arxive
    - Titles, summaries, and key takeaways from last three fromtop 5 papers headline research papers published recently (within the last 30 days)
    - The main research paper spotlighted, along with a description/summary of top 1 research papers from top 5
    - A featured research paper, with its title, publication details (including date), and a summary from top 2 research papers from top 5.
    Ensure to include only the most recent research papers and trends that align with the current AI landscape.
    return the output in the formate of output pydantic given in NewsletterContent
    """

    print(f"\nQuestion: {question}\n")

    # Invoke the agent executor
    response = agent_executor.invoke({"input": question})

    print("\n--- Agent Run Finished ---")
    print(f"\nRaw Response: {response.get('output')}")  # Show raw response for debugging

    # Optionally, you can parse the response into the `NewsletterContent` Pydantic model
    try:
        newsletter_content = NewsletterContent.model_validate(response.get('output'))  # Using the new `model_validate` method
        print("\nNewsletter Content:")
        print(newsletter_content.json(indent=2))
    except Exception as e:
        print(f"Error parsing response into NewsletterContent: {e}")
