from mistralai import Mistral

class MistralWrapper:
    def __init__(self, api_key: str = None):
        self.client = Mistral(api_key=api_key)
        self.model = "mistral-small-2506"
        import os
        # Construct absolute path to system prompt file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(current_dir, "..", "data", "prompts", "system_prompt.txt")
        with open(prompt_path, "r") as f:
            self.system_prompt = f.read()
            f.close()

    def generate(self, user_prompt: str, history: list[dict[str, str]] = []) -> str:
        try:
            if history == []:
                history = [{"role": "system", "content": self.system_prompt}]
            history.append({"role": "user", "content": user_prompt})
            
            response = self.client.chat.complete(
                model=self.model,
                messages=history,
            )

            text_response = response.choices[0].message.content

            history.append({"role": "assistant", "content": text_response})
            
            return text_response, history
        except Exception as e:
            print(f"Error in LLM generation: {e}")
            # Return a fallback response and the original history
            fallback_response = "Désolé, je n'ai pas pu traiter votre demande. Veuillez réessayer."
            history.append({"role": "assistant", "content": fallback_response})
            return fallback_response, history