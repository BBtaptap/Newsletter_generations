# import os
# from dotenv import load_dotenv
# from datetime import datetime
# from pydantic import BaseModel, Field, ValidationError
# from agno.agent import Agent
# from agno.models.groq import Groq # Keep Groq if you might switch back
# from agno.tools.duckduckgo import DuckDuckGoTools
# from agno.tools.arxiv import ArxivTools
# from agno.tools.thinking import ThinkingTools
# from agno.agent import Agent, RunResponse
# from agno.models.google import Gemini
# from tools import Googletoolkit
# import json
# import re
# # Path to your credentials JSON (if needed for other tools later)
# credentials_path = "/workspaces/Newsletter_generations/credentials.json"
# sheet_id = "16o88VRyZLcAa3ZwC-kGRU2QJIj-Rad4FQIKmYcY5j-o"
# google_toolkit = Googletoolkit(credentials_path, sheet_id) # Not used currently

# # Load environment variables
# load_dotenv()
# groq_api_key = os.getenv("GROQ_API_KEY") # Keep for potential future use
# google_api_key = os.getenv("GOOGLE_API_KEY")

# # Use Google API Key as it's used for Gemini
# if not google_api_key:
#     raise ValueError("GOOGLE_API_KEY not found in .env file")

# # --- Define Pydantic Schema ---
# class NewsletterContent(BaseModel):
#     # Using Field aliases to match the expected JSON output keys exactly
#     figure_name: str = Field(..., description="Description of image to generate.", alias="FIGURE_NAME")
#     quote_1: str = Field(..., description="First AI-related quote, including who said it.", alias="Quote_1") # Note: Using _ instead of - based on your sample output
#     quote_2: str = Field(..., description="Second AI-related quote, including who said it.", alias="Quote_2")
#     description: str = Field(..., description="Short description of AI trends for the week.", alias="Description")

#     title_1: str = Field(..., description="Title of the first headline research paper.", alias="title_1")
#     summary_1: str = Field(..., description="Summary of the first headline research paper.", alias="summary_1")
#     takeaway_1: str = Field(..., description="Key takeaway from the first headline research paper.", alias="takeaway_1")

#     title_2: str = Field(..., description="Title of the second headline research paper.", alias="title_2")
#     summary_2: str = Field(..., description="Summary of the second headline research paper.", alias="summary_2")
#     takeaway_2: str = Field(..., description="Key takeaway from the second headline research paper.", alias="takeaway_2")

#     title_3: str = Field(..., description="Title of the third headline research paper.", alias="title_3")
#     summary_3: str = Field(..., description="Summary of the third headline research paper.", alias="summary_3")
#     takeaway_3: str = Field(..., description="Key takeaway from the third headline research paper.", alias="takeaway_3")

#     main_paper_title: str = Field(..., description="Title of the main foundational research paper highlighted.", alias="main_paper_title")
#     main_paper_description: str = Field(..., description="Description/summary of the main foundational paper.", alias="main_paper_description")

#     featured_title: str = Field(..., description="Title of the featured research paper.", alias="featured_title")
#     featured_published_in: str = Field(..., description="Publication details (e.g., journal, conference, arXiv ID, date).", alias="featured_published_in")
#     featured_summary: str = Field(..., description="Summary of the featured research paper.", alias="featured_summary")

#     class Config:
#         # Allow population by alias name (e.g., allows creating model instance using FIGURE_NAME)
#         populate_by_name = True
#         # Optional: If you want to ensure the output JSON keys exactly match the aliases (like Quote_1)
#         # serialization_alias_priority = 2 # Pydantic v2

# # Initialize the agent using Agno
# agent = Agent(
#     # Use a model known for good instruction following and JSON output if possible
#     # Gemini Flash is okay, but stronger models might be more reliable for JSON
#     model=Gemini(id="gemini-2.0-flash-exp", api_key=google_api_key, temperature=0.5), # Changed model ID slightly, adjust if needed
#     description="""You are an AI journalist writing weekly newsletters. You MUST use the tools provided to find real, current information. Your final output MUST be ONLY a valid JSON object matching the user-provided schema, populated with ACTUAL data found using the tools. DO NOT use placeholder text 
#     **and save the data in google sheet using google_toolkit**
#     """,    
#     tools=[
#         DuckDuckGoTools(),
#         ArxivTools(),
#         ThinkingTools(),
#         google_toolkit
#     ],
#     show_tool_calls=True,
#     markdown=False, # Set markdown=False as we want raw JSON
# )

# if __name__ == "__main__":
#     print("\n--- Running Agno Agent for AI Digest ---\n")

#     # Prepare the question - IMPORTANT: Instruct for JSON output
#     current_date = datetime.now().strftime("%Y-%m-%d")
#     # Get the Pydantic schema as a JSON string for the prompt
#     schema_json = NewsletterContent.model_json_schema()

#     # --- Refined Prompt ---
#     prompt = f"""
#     Generate content for the Blackbucks Weekly AI Digest for {current_date}.
#     Follow these steps precisely:
#     1.  Use tools to find the latest AI trends for the week (focus on LLMs, Generative AI, Agentic AI, Ethics). Summarize them for the 'Description'.
#     2.  Use tools to find two recent, relevant AI-related quotes from prominent figures online. Include who said them for 'Quote_1' and 'Quote_2'.
#     3.  Generate a description for a suitable image ('FIGURE_NAME') related to current AI trends (e.g., Interconnected LLM nodes, AI ethics concept).
#     4.  Use the ArXiv tool to search for the top 5 most relevant AND RECENT (within the last few months if possible, max 1 year) research papers related to "Large Language Models" OR "Agentic AI" OR "AI Alignment" OR "Generative AI". Prioritize relevance and recency.
#     5.  From the ACTUAL ArXiv search results:
#         a. Select paper #1 as the 'Main Paper'. Extract its EXACT title for 'main_paper_title' and its ACTUAL summary/abstract for 'main_paper_description'.
#         b. Select paper #2 as the 'Featured Paper'. Extract its EXACT title for 'featured_title', its publication details (use 'arXiv ID: [id], Date: [published_date]' format for 'featured_published_in'), and its ACTUAL summary/abstract for 'featured_summary'.
#         c. Select papers #3, #4, and #5 as 'Headline Papers'. For each, extract the EXACT title, a CONCISE summary derived from its abstract, and ONE key takeaway. Use the fields title_1/summary_1/takeaway_1, title_2/..., title_3/... Ensure these are distinct papers from #1 and #2.
#     6.  Compile ALL gathered information into a single JSON object.
#     7.  The JSON object MUST strictly adhere to the following Pydantic schema:
#         ```json
#         {json.dumps(schema_json, indent=2)}
#         ```
#     8.  CRITICAL: Your *entire final response* must be *only* the valid JSON object populated with the REAL data found using the tools. Do NOT include introductory text, explanations, apologies, or markdown formatting like ```json ... ```. ABSOLUTELY NO PLACEHOLDER TEXT like "Title 1" or "Summary 1". If you cannot find suitable information for a field after using the tools, you may indicate that within the JSON value (e.g., "Could not find recent quote"), but do NOT use generic placeholders.
#     9. **Save the data in google steet using google_toolkit**
#     Focus on using the tool results accurately.
#     """

#     # Run the agent
#     print("\n--- Sending Prompt to Agent ---")
#     agent.print_response(prompt)
#     response = agent.run(prompt)

#     print("\n--- Raw Agent Output ---")
#     # Check if content is None or empty before proceeding
#     if response.content:
#         print(response.content) # Print the raw string output from the LLM
#     else:
#         print("Agent returned empty content.")
#         exit() # Exit if no content was generate

#     match = re.search(r"\{.*\}", response.content, re.DOTALL)
#     if match:
#         json_string = match.group(0)
#         print("\n--- Extracted JSON String ---")
#         print(json_string)
#     else:
#         # Fallback: Simple stripping if regex fails (less robust)
#         print("\n--- Regex extraction failed, attempting simple strip ---")
#         json_string = raw_content.strip().strip('```json').strip('```').strip()
#         print("\n--- Stripped JSON String ---")
#         print(json_string)
#     # --- END CLEANING STEP ---


#     # Parse the cleaned JSON string content into the structured Pydantic model
#     try:
#         # Use model_validate_json to parse the cleaned string content
#         content_model = NewsletterContent.model_validate_json(json_string)
#         print("\n--- Structured Newsletter Content (Validated) ---")
#         # Print the validated data as a JSON string
#         print(content_model.model_dump_json(indent=2, by_alias=True)) # Use by_alias=True to get keys like "FIGURE_NAME"--


#     except ValidationError as e:
#         print("\n⚠️ Pydantic Validation Error: Could not parse the cleaned agent's response into the NewsletterContent schema.")
#         print("--- Error Details ---")
#         print(e)
#         print("--- Review Cleaned JSON String Above ---")
#     except json.JSONDecodeError as e:
#         print("\n⚠️ JSON Decode Error: The cleaned agent's response was not valid JSON.")
#         print("--- Error Details ---")
#         print(e)
#         print("--- Review Cleaned JSON String Above ---")
#     except Exception as e:
#         print(f"\n⚠️ An unexpected error occurred during validation: {e}")
#         print("--- Review Cleaned JSON String Above ---")
import os
import asyncio
from dotenv import load_dotenv
from datetime import datetime
from pydantic import BaseModel, Field, ValidationError
from agno.agent import Agent
# from agno.models.groq import Groq
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.arxiv import ArxivTools
from agno.tools.thinking import ThinkingTools
from agno.agent import Agent, RunResponse
from agno.models.google import Gemini
from googleapiclient.errors import HttpError # <--- ADD THIS LINE

# --- Import your Google Toolkit ---
# Make sure 'tools.py' exists in the same directory or adjust the import path
try:
    # Assuming tools.py is in the same directory
    from tools import GoogleSheetsHelper
    from image_gen import generate_image_openai, JSONResponse, ImagePrompt
except ImportError:
    print("⚠️ Warning: Could not import from tools.py. Google Sheet/Image Gen operations will be disabled.")
    GoogleSheetsHelper = None
    generate_image_openai = None
    JSONResponse = None # Define a dummy if needed for error handling below
import json
import re

# --- Configuration ---
# IMPORTANT: Make sure these paths/IDs are correct
CREDENTIALS_PATH = "/workspaces/Newsletter_generations/credentials.json" # Path to your Google API credentials
SHEET_ID = "16o88VRyZLcAa3ZwC-kGRU2QJIj-Rad4FQIKmYcY5j-o"            # Your Google Sheet ID
TARGET_SHEET_NAME = 'Sheet1' # The name of the sheet (tab) within your spreadsheet to write to

# --- Load Environment Variables ---
load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

# --- Define Pydantic Schema ---
class NewsletterContent(BaseModel):
    # Using Field aliases to match the expected JSON output keys exactly
    figure_name: str = Field(..., description="Description of image to generate.", alias="FIGURE_NAME")
    quote_1: str = Field(..., description="First AI-related quote, including who said it.", alias="Quote_1")
    quote_2: str = Field(..., description="Second AI-related quote, including who said it.", alias="Quote_2")
    description: str = Field(..., description="Short description of AI trends for the week.", alias="Description")

    title_1: str = Field(..., description="Title of the first headline research paper.", alias="title_1")
    summary_1: str = Field(..., description="Summary of the first headline research paper.", alias="summary_1")
    takeaway_1: str = Field(..., description="Key takeaway from the first headline research paper.", alias="takeaway_1")

    title_2: str = Field(..., description="Title of the second headline research paper.", alias="title_2")
    summary_2: str = Field(..., description="Summary of the second headline research paper.", alias="summary_2")
    takeaway_2: str = Field(..., description="Key takeaway from the second headline research paper.", alias="takeaway_2")

    title_3: str = Field(..., description="Title of the third headline research paper.", alias="title_3")
    summary_3: str = Field(..., description="Summary of the third headline research paper.", alias="summary_3")
    takeaway_3: str = Field(..., description="Key takeaway from the third headline research paper.", alias="takeaway_3")

    main_paper_title: str = Field(..., description="Title of the main foundational research paper highlighted.", alias="main_paper_title")
    main_paper_description: str = Field(..., description="Description/summary of the main foundational paper.", alias="main_paper_description")

    featured_title: str = Field(..., description="Title of the featured research paper.", alias="featured_title")
    featured_published_in: str = Field(..., description="Publication details (e.g., journal, conference, arXiv ID, date).", alias="featured_published_in")
    featured_summary: str = Field(..., description="Summary of the featured research paper.", alias="featured_summary")

    class Config:
        populate_by_name = True

# --- Initialize Agent ---
# NOTE: No Google Toolkit added to the *agent's* tools here,
# unless your toolkit is designed to be callable *by the LLM*.
# We are calling it directly from the Python script.
agent = Agent(
    model=Gemini(id="gemini-2.0-flash-exp", api_key=google_api_key, temperature=0.3),
    description="""You are an AI journalist writing weekly newsletters. You MUST use the tools provided to find real, current information. Your final output MUST be ONLY a valid JSON object matching the user-provided schema, populated with ACTUAL data found using the tools. DO NOT use placeholder text 

    """,     
    tools=[
        DuckDuckGoTools(),
        ArxivTools(),
        ThinkingTools()
    ],
    show_tool_calls=True,
    markdown=False,
)

# --- New Async Workflow Function ---
async def process_and_save_content(
    content_model: NewsletterContent,
    sheets_helper: GoogleSheetsHelper,
    target_sheet: str,
    column_order: list,
    image_column_header: str # Pass the actual header name string
):
    """Generates image FIRST, then appends all data including URL/error to sheet."""
    # Check if necessary components are available
    generate_func_available = callable(globals().get('generate_image_openai')) or callable(vars().get('generate_image_openai')) # Check local/global scope

    if not sheets_helper or not generate_func_available:
        print(f"Error: Sheets Helper available: {bool(sheets_helper)}, Image Generator available: {generate_func_available}. Cannot proceed.")
        return

    # --- Step 1: Generate Image ---
    image_description = content_model.figure_name # Use description from model
    print(f"\n--- Generating image for description: '{image_description}' ---")
    image_prompt_object = ImagePrompt(image_description)
    # Call generate_image_openai directly with the string prompt
    # Ensure generate_image_openai accepts a string prompt
    generation_response = await generate_image_openai(image_prompt_object)
    image_url_or_error = "Error: Generation fallback" # Default value

    if generation_response and hasattr(generation_response, 'content') and isinstance(generation_response.content, dict):
        if "image_url" in generation_response.content:
            image_url_or_error = generation_response.content["image_url"]
            print(f"--- Successfully generated image URL: {image_url_or_error} ---")
        elif "error" in generation_response.content:
            error_msg = generation_response.content['error']
            print(f"--- Image generation failed: {error_msg} ---")
            image_url_or_error = f"Error: {error_msg}" # Store error message
        else:
             print("--- Image generation response unknown format. ---")
             image_url_or_error = "Error: Unknown generation response"
    else:
        print(f"--- Invalid response object from image generator: {generation_response} ---")
        image_url_or_error = "Error: Invalid generator response"

    # --- Step 2: Prepare ALL Data for Appending ---
    print(f"\n--- Preparing data for Google Sheet '{target_sheet}' ---")
    data_to_write = content_model.model_dump(by_alias=True)

    # Add the generated image URL or error message to the data dictionary
    # Ensure the key matches the header name in your column_order list
    data_to_write[image_column_header] = image_url_or_error # Use the passed header name
    print(f"Data prepared for column '{image_column_header}': {str(image_url_or_error)[:100]}...") # Log start of value

    # --- Step 3: Append the Complete Row ---
    print(f"--- Attempting to append complete row data to sheet ---")
    # Ensure append_data_row returns row index (int) on success, None on failure
    appended_row_index = sheets_helper.append_data_row(
        sheet_name=target_sheet,
        data_dict=data_to_write,
        column_order=column_order # Ensure column_order includes image_column_header
    )

    if appended_row_index is not None and isinstance(appended_row_index, int): # Check for integer return
        print(f"--- Successfully appended complete data row (including image URL/status) to row {appended_row_index}. ---")
    else:
        print(f"--- Failed to append complete data row to sheet (append returned: {appended_row_index}). ---")


if __name__ == "__main__":
    print("\n--- Running Agno Agent for AI Digest ---\n")

    # --- Initialize Google Sheets Helper ---
    sheets_helper = None
    if GoogleSheetsHelper:
        try:
            sheets_helper = GoogleSheetsHelper(CREDENTIALS_PATH, SHEET_ID)
            print("--- Google Sheets Helper Initialized ---")
            # Optional: Verify connection by listing sheets
            # available_sheets = sheets_helper.list_sheets()
            # print(f"Available sheets: {available_sheets}")
            # if TARGET_SHEET_NAME not in available_sheets:
            #    print(f"Warning: Target sheet '{TARGET_SHEET_NAME}' not found in spreadsheet.")
        except (FileNotFoundError, RuntimeError, ValueError, Exception) as e:
            print(f"⚠️ Error initializing Google Sheets Helper: {e}. Cannot write to Google Sheet.")
    else:
        print("--- Google Sheets Helper not available. Skipping Google Sheet operations. ---")



    current_date = datetime.now().strftime("%Y-%m-%d")
    schema_json = NewsletterContent.model_json_schema()

    # --- Refined Prompt (Keep your detailed prompt here) ---
    prompt = f"""
    Generate content for the Blackbucks Weekly AI Digest for {current_date}.
    Follow these steps precisely:
    1.  Use tools to find the latest AI trends for the week (focus on LLMs, Generative AI, Agentic AI, Ethics). Summarize them for the 'Description'.
    2.  Use tools to find two recent, relevant AI-related quotes from prominent figures online. Include who said them for 'Quote_1' and 'Quote_2'.
    3.  Generate a description for a suitable image ('FIGURE_NAME') related to current AI trends (e.g., Interconnected LLM nodes, AI ethics concept).
    4.  Use the ArXiv tool to search for the top 5 most relevant AND RECENT (within the last few months if possible, max 1 year) research papers related to "Large Language Models" OR "Agentic AI" OR "AI Alignment" OR "Generative AI". Prioritize relevance and recency.
    5.  From the ACTUAL ArXiv search results:
        a. Select paper #1 as the 'Main Paper'. Extract its EXACT title for 'main_paper_title' and its ACTUAL summary/abstract for 'main_paper_description'.
        b. Select paper #2 as the 'Featured Paper'. Extract its EXACT title for 'featured_title', its publication details (use 'arXiv ID: [id], Date: [published_date]' format for 'featured_published_in'), and its ACTUAL summary/abstract for 'featured_summary'.
        c. Select papers #3, #4, and #5 as 'Headline Papers'. For each, extract the EXACT title, a CONCISE summary derived from its abstract, and ONE key takeaway. Use the fields title_1/summary_1/takeaway_1, title_2/..., title_3/... Ensure these are distinct papers from #1 and #2.
    6.  Compile ALL gathered information into a single JSON object.
    7.  The JSON object MUST strictly adhere to the following Pydantic schema:
        ```json
        {json.dumps(schema_json, indent=2)}
        ```
    8.  CRITICAL: Your *entire final response* must be *only* the valid JSON object populated with the REAL data found using the tools. Do NOT include introductory text, explanations, apologies, or markdown formatting like ```json ... ```. ABSOLUTELY NO PLACEHOLDER TEXT like "Title 1" or "Summary 1". If you cannot find suitable information for a field after using the tools, you may indicate that within the JSON value (e.g., "Could not find recent quote"), but do NOT use generic placeholders.

    Focus on using the tool results accurately.
    """

    # Run the agent
    print("\n--- Sending Prompt to Agent ---")
    # agent.print_response(prompt) # Use this for streaming if desired
    response = agent.run(prompt)

    # --- (Optional but recommended) Inspect Full Response for Debugging ---
    # print("\n--- Full Agent Response Object (for debugging) ---")
    # print(response)
    # if hasattr(response, 'messages') and response.messages:
    #      print("\n--- Agent Message History (for debugging) ---")
    #      # ... (code to print messages as in previous example) ...

    print("\n--- Raw Agent Output ---")
    if response.content:
        raw_content = response.content
        print(raw_content)
    else:
        print("Agent returned empty content.")
        exit()

    # --- Clean the Raw Output ---
    json_string = None
    match = re.search(r"\{.*\}", raw_content, re.DOTALL)
    if match:
        json_string = match.group(0)
        print("\n--- Extracted JSON String ---")
    else:
        json_string = raw_content.strip().strip('```json').strip('```').strip()
        if not json_string.startswith('{') or not json_string.endswith('}'):
             print("\n--- Fallback stripping failed to produce likely JSON ---")
             json_string = None
        else:
             print("\n--- Stripped JSON String (Fallback) ---")

    if not json_string:
        print("\n⚠️ Error: Could not extract a JSON object from the agent's response.")
        exit()

    # --- Parse and Validate ---
    try:
        content_model = NewsletterContent.model_validate_json(json_string)
        print("\n--- Structured Newsletter Content (Validated) ---")

        # Define Column Order (MUST match your Google Sheet headers EXACTLY!)
        # Use a variable for the image column header name
        image_header = "Image_URL" # Or whatever your actual header is
        column_order = [
            "FIGURE_NAME", "Quote_1", "Quote_2", "Description",
            "title_1", "summary_1", "takeaway_1",
            "title_2", "summary_2", "takeaway_2",
            "title_3", "summary_3", "takeaway_3",
            "main_paper_title", "main_paper_description",
            "featured_title", "featured_published_in", "featured_summary",
            image_header  # Use the variable here
        ]
        print(f"Using column order for Sheet: {column_order}")

        # Trigger Async Workflow
        if sheets_helper and (callable(globals().get('generate_image_openai')) or callable(vars().get('generate_image_openai'))):
             print("\n--- Starting Post-Processing (Generate Image, Append Sheet) ---")
             # Run the async function using asyncio.run()
             asyncio.run(process_and_save_content(
                 content_model=content_model,
                 sheets_helper=sheets_helper,
                 target_sheet=TARGET_SHEET_NAME,
                 column_order=column_order,
                 image_column_header=image_header # Pass the header name correctly
             ))
             print("--- Post-Processing Complete ---")
        else:
             print("\n--- Skipping Post-Processing due to missing Sheets Helper or Image Generator ---")

    except ValidationError as e:
        print("\n⚠️ Pydantic Validation Error: Could not parse JSON into NewsletterContent schema.")
        print(f"--- Error Details ---\n{e}")
        print("--- Review Extracted JSON String ---")
        print(json_string)
    except json.JSONDecodeError as e:
        print("\n⚠️ JSON Decode Error: The extracted string was not valid JSON.")
        print(f"--- Error Details ---\n{e}")
        print("--- Review Extracted JSON String ---")
        print(json_string)
    except Exception as e:
        print(f"\n⚠️ An unexpected error occurred during validation or processing: {e}")
        print("--- Review Extracted JSON String (if applicable) ---")
        if json_string: print(json_string)