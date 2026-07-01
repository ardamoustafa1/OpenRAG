from typing import Any

import jinja2


class PromptManager:
    """
    Manages prompt templates, few-shot examples, and basic prompt injection defenses.
    Supports rendering templates via Jinja2.
    """

    def __init__(self) -> None:
        # Setup Jinja environment
        self.env = jinja2.Environment(autoescape=True)

        # Define base templates
        self.templates = {
            "rag_tr": """
Aşağıdaki bağlamı (context) kullanarak kullanıcının sorusunu yanıtla.
Eğer cevabı bağlamda bulamazsan, "Bilmiyorum" de ve kendi bilgini kullanma.
Alıntı yaparken her zaman kaynak doküman ismini belirt.

BAĞLAM:
{% for chunk in chunks %}
[Kaynak: {{ chunk.document_name }}]
{{ chunk.content }}
{% endfor %}

KULLANICI SORUSU: {{ question }}
""",
            "rag_en": """
Answer the user's question using the following context.
If you cannot find the answer in the context, say "I don't know" and do not use outside knowledge.
Always cite your sources using the document name.

CONTEXT:
{% for chunk in chunks %}
[Source: {{ chunk.document_name }}]
{{ chunk.content }}
{% endfor %}

USER QUESTION: {{ question }}
""",
        }

    def render_rag_prompt(
        self, language: str, chunks: list[dict[str, Any]], question: str
    ) -> str:
        """Render the RAG system prompt with context chunks."""
        template_str = self.templates.get(f"rag_{language}", self.templates["rag_en"])
        template = self.env.from_string(template_str)
        return template.render(chunks=chunks, question=self.sanitize_input(question))

    def build_system_prompt(
        self, base_prompt: str, tenant_prompt: str = "", collection_prompt: str = ""
    ) -> str:
        """Combine platform, tenant, and collection specific instructions."""
        parts = [base_prompt.strip()]
        if tenant_prompt:
            parts.append(tenant_prompt.strip())
        if collection_prompt:
            parts.append(collection_prompt.strip())
        return "\n\n".join(parts)

    def sanitize_input(self, text: str) -> str:
        """
        Basic prompt injection defense.
        In a real scenario, you might run an LLM classifier or a library like Rebuff to detect injections.
        Here we do simple sanitization.
        """
        # Basic removal of markdown code block markers if they shouldn't be there,
        # or escaping system prompt instruction keywords.
        sanitized = text.replace("<|system|>", "").replace("<|user|>", "")
        return sanitized


prompt_manager = PromptManager()
