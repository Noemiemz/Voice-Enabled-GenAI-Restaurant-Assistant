from mistralai import Mistral

class MistralWrapper:
    def __init__(self, api_key: str = None):
        self.client = Mistral(api_key=api_key)
        self.model = "mistral-small-latest"
        with open("source/data/prompts/system_prompt.txt", "r") as f:
            self.system_prompt = f.read()
            f.close()

    def generate(self, user_prompt: str, history: list[dict[str:str]] = None) -> str:
        if history is None:
            history = [{"role": "system", "content": self.system_prompt}]
        
        response = self.client.chat.complete(
            model=self.model,
            messages=history + [{"role": "user", "content": user_prompt}],
        )
        
        return response.text