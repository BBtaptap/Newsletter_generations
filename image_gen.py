import asyncio
# import replicate # No longer needed
import openai        # Import OpenAI library
import aiohttp
import aiofiles
import os
import time
from dotenv import load_dotenv

load_dotenv()

# --- Get OpenAI API Key ---
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY not found in .env file or environment variables")

# --- Initialize OpenAI Async Client ---
# It's often better to initialize the client once if the script runs longer
# or is part of a larger app, but for this example, we can do it here or inside the function.
# Using async client as our functions are async
client = openai.AsyncOpenAI(api_key=openai_api_key)

# --- Dummy Classes (keep for standalone example) ---
class HTTPException(Exception):
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"{status_code}: {detail}")

class JSONResponse:
    def __init__(self, content):
        self.content = content
    def __repr__(self):
        # Limit printing very long base64 strings if we were using that format
        if "image_b64" in self.content:
             return f"JSONResponse(content={{'image_b64': '... (data omitted) ...'}})"
        return f"JSONResponse(content={self.content})"

# Define a simple class to hold the prompt string
class ImagePrompt:
    def __init__(self, prompt_text):
        self.prompt = prompt_text

# --- Modified Image Generation Function ---

async def generate_image_openai(image_prompt): # Renamed for clarity
    """Generates an image using OpenAI's DALL-E 3 API."""
    try:
        prompt = image_prompt.prompt
        print(f"Received prompt for OpenAI: {prompt}")

        # Use OpenAI's DALL-E 3 API
        # Note: DALL-E 3 requires specific sizes. 1024x1024 is standard square.
        # Other options: 1792x1024 (landscape), 1024x1792 (portrait)
        # We request the URL directly.
        response = await client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,                     # Generate one image
            size="1024x1024",        # Standard square size for DALL-E 3
            quality="standard",      # Or "hd" for higher quality (costs more)
            style="vivid",           # Or "natural"
            response_format="url"    # Get a temporary URL for the image
        )

        print(f"Raw OpenAI response object: {response}") # See the structure

        # Extract the URL from the response
        # The response object structure is response.data[image_index].attribute
        if response.data and len(response.data) > 0:
            image_url = response.data[0].url
            # Optionally, you might want revised_prompt if OpenAI changed it
            # revised_prompt = response.data[0].revised_prompt
            # print(f"Revised prompt: {revised_prompt}")
        else:
            raise ValueError("No image data found in OpenAI response.")

        if not image_url:
             raise ValueError("Image URL is empty in OpenAI response.")

        print(f"Generated image URL (OpenAI): {image_url}")

        return JSONResponse(content={"image_url": image_url})

    except openai.APIError as e:
        # Handle API error here, e.g. retry or log
        print(f"OpenAI API returned an API Error: {e}")
        return JSONResponse(content={"error": f"OpenAI API Error: {e}"})
    except openai.APIConnectionError as e:
        # Handle connection error here
        print(f"Failed to connect to OpenAI API: {e}")
        return JSONResponse(content={"error": f"OpenAI Connection Error: {e}"})
    except openai.RateLimitError as e:
        # Handle rate limit error (we recommend using exponential backoff)
        print(f"OpenAI API request exceeded rate limit: {e}")
        return JSONResponse(content={"error": f"OpenAI Rate Limit Error: {e}"})
    except Exception as e:
        print(f"Error generating image with OpenAI: {str(e)}")
        # raise HTTPException(status_code=400, detail=str(e))
        return JSONResponse(content={"error": f"Generation failed: {str(e)}"})


# --- Download Function (remains the same) ---
async def download_image(image_url: str):
    try:
        # Create Output folder if it doesn't exist
        output_folder = "Output"
        os.makedirs(output_folder, exist_ok=True)

        # Generate a unique filename
        filename = f"generated_image_openai_{int(time.time())}.jpg" # Added openai marker
        filepath = os.path.join(output_folder, filename)

        print(f"Attempting to download image from: {image_url}")
        # Download the image
        async with aiohttp.ClientSession() as session:
            # Some image URLs might require specific headers, but usually not needed for OpenAI URLs
            async with session.get(image_url) as resp:
                print(f"Download response status: {resp.status}")
                resp.raise_for_status() # Raise error for bad responses (4xx or 5xx)
                async with aiofiles.open(filepath, mode='wb') as f:
                    await f.write(await resp.read())
                print(f"Image successfully downloaded to: {filepath}")

        # Return the filepath and filename
        return JSONResponse(content={
            "filepath": filepath,
            "filename": filename
        })
    except aiohttp.ClientError as e:
         print(f"Error downloading image (network/HTTP error): {str(e)}")
         # raise HTTPException(status_code=400, detail=f"Download failed: {str(e)}")
         return JSONResponse(content={"error": f"Download failed (network): {str(e)}"})
    except Exception as e:
        print(f"Error downloading image (other error): {str(e)}")
        # raise HTTPException(status_code=400, detail=str(e))
        return JSONResponse(content={"error": f"Download failed: {str(e)}"})

# --- Main Async Function and Runner ---
async def main():
    prompt_text = "AI related workflows or AI Agents images"
    image_prompt_object = ImagePrompt(prompt_text) # Create the object

    print("Generating image using OpenAI DALL-E 3...")
    # Use await to call the async function
    generation_response = await generate_image_openai(image_prompt_object) # Call the OpenAI version
    print(f"Generation Response: {generation_response}")

    # Check if generation was successful and get URL
    if generation_response and "image_url" in generation_response.content:
        image_url = generation_response.content["image_url"]
        print("\nDownloading image...")
        download_response = await download_image(image_url)
        print(f"Download Response: {download_response}")
    elif generation_response and "error" in generation_response.content:
         print(f"Image generation failed: {generation_response.content['error']}")
    else:
        print("Image generation did not return a valid URL or response.")


if __name__ == "__main__":
    # Run the main async function using asyncio's event loop
    asyncio.run(main())