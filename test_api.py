import os
from dotenv import load_dotenv
from google import genai

load_dotenv()


def test_models():
    from google import genai

    # The client gets the API key from the environment variable `GEMINI_API_KEY`.
    client = genai.Client()

    response = client.models.generate_content(
        model="gemini-3-flash-preview", contents="Explain how AI works in a few words"
    )
    print(response.text)


def list_and_test_models():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY not found in .env")
        return

    client = genai.Client(api_key=api_key)

    print("--- Fetching Available Models ---")
    try:
        # List all models
        models = client.models.list()
        available_model_names = []
        for m in models:
            # We filter for models that support content generation
            if "generateContent" in m.supported_generation_methods:
                print(f"Model: {m.name} (Display: {m.display_name})")
                # Strip the 'models/' prefix if present for the actual call
                name = m.name.split("/")[-1] if "/" in m.name else m.name
                available_model_names.append(name)

        if not available_model_names:
            print("⚠️ No models found with 'generateContent' support.")
            return

        print("\n--- Testing Top Models ---")
        # Test up to 3 models from the list to find one that works
        for model_id in available_model_names[:5]:
            print(f"Testing: {model_id}...")
            try:
                response = client.models.generate_content(model=model_id, contents="Hi")
                print(f"✅ Success with {model_id}!")
                print(f"Response: {response.text}")
                print(f"\n👉 FOUND WORKING MODEL: {model_id}")
                return
            except Exception as e:
                print(f"❌ Failed with {model_id}: {str(e)[:100]}...")

    except Exception as e:
        print(f"❌ Error listing models: {e}")


if __name__ == "__main__":
    # list_and_test_models()
    test_models()
