import google.generativeai as genai
from src import config

def init_llm():
    if not config.GEMINI_API_KEY:
        print("⚠️ WARNING: GEMINI_API_KEY is not set. LLM features will be disabled.")
        return False
    
    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
        print("LLM client initialized successfully.")
        return True
    except Exception as e:
        print(f"🚨 ERROR: Failed to initialize LLM client: {e}")
        return False

# Initialize the model, check for API key
is_llm_enabled = init_llm()
model = genai.GenerativeModel('models/gemini-2.0-flash') if is_llm_enabled else None

async def is_task(text: str) -> bool:
    """Uses LLM to determine if the message content is a task."""
    if not model:
        return False

    try:
        # Simple prompt to check for task-like intent
        prompt = f"""
        Analyze the following text and determine if it represents a task, a to-do item, a question that needs an answer, or a request for action.
        Respond with only "true" if it is a task, and "false" if it is not.

        Text: "{text}"
        """
        response = await model.generate_content_async(prompt)
        
        # Clean up the response and check for "true"
        result = response.text.strip().lower()
        print(f"LLM check for '{text[:30]}...': {result}")
        return "true" in result

    except Exception as e:
        print(f"🚨 ERROR in LLM task check: {e}")
        return False 