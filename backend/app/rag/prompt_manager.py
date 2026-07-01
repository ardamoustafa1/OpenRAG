class PromptManager:
    def build_system_prompt(self, base_prompt: str, tenant_prompt: str) -> str:
        if tenant_prompt:
            return f"{base_prompt}\n\nTenant Instructions:\n{tenant_prompt}"
        return base_prompt


prompt_manager = PromptManager()
