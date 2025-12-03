from mistralai import Mistral

class MistralWrapper:
    def __init__(self, api_key: str = None):
        self.client = Mistral(api_key=api_key)
        self.model = "mistral-small-2506"
        with open("./src/data/prompts/system_prompt.txt", "r") as f:
            self.system_prompt = f.read()
            f.close()

    def generate(self, user_prompt: str, history: list[dict[str:str]] = []) -> str:
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