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
        # More specific prompt to avoid misinterpreting commands and code blocks
        prompt = f"""
        Analyze the text to determine if it's a task. A task is a to-do item, a question needing an answer, or a request for action.
        - A command starting with "/" is NOT a task.
        - A simple statement or conversation is NOT a task.
        - A block of code is NOT a task.
        - A report, summary, or log entry is NOT a task.
        
        Respond with only "true" or "false".

        Example 1:
        Text: "Remember to buy milk tomorrow"
        Response: "true"

        Example 2:
        Text: "/add_task buy milk"
        Response: "false"

        Example 3:
        Text: "What is the capital of France?"
        Response: "true"
        
        Example 4:
        Text: "hello how are you"
        Response: "false"

        Example 5:
        Text: "```python\\nprint('hello world')\\n```"
        Response: "false"

        Example 6:
        Text: "06/25 Report"
        Response: "false"

        Text to analyze: "{text}"
        """
        response = await model.generate_content_async(prompt)
        
        # Clean up the response and check for "true"
        result = response.text.strip().lower()
        print(f"LLM check for '{text[:30]}...': {result}")
        return "true" in result

    except Exception as e:
        print(f"🚨 ERROR in LLM task check: {e}")
        return False 