import tiktoken


class TokenCounter:
    """
    Handles token estimation using tiktoken (cl100k_base approximation for local models)
    and context window management.
    """

    def __init__(self):
        # We use cl100k_base (OpenAI's latest tokenizer) as a fast, reliable
        # approximation for most modern LLMs (Llama 3 / Qwen) instead of
        # loading massive huggingface tokenizers per request.
        self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a string."""
        return len(self.encoding.encode(text))

    def count_message_tokens(self, messages: list[dict[str, str]]) -> int:
        """Count tokens in a list of chat messages."""
        num_tokens = 0
        for message in messages:
            # Add padding for roles
            num_tokens += 4
            for _key, value in message.items():
                num_tokens += self.count_tokens(value)
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens

    def truncate_context(
        self, messages: list[dict[str, str]], max_tokens: int
    ) -> list[dict[str, str]]:
        """
        Truncate older messages from the context window to fit within max_tokens.
        Always preserves the system message (first message) and the latest user query (last message).
        """
        if not messages:
            return messages

        current_tokens = self.count_message_tokens(messages)
        if current_tokens <= max_tokens:
            return messages

        # Keep system prompt (index 0) and the latest query (index -1)
        system_msg = messages[0] if messages[0]["role"] == "system" else None
        latest_msg = messages[-1]

        # The budget available for intermediate history
        budget = max_tokens - self.count_message_tokens([latest_msg])
        if system_msg:
            budget -= self.count_message_tokens([system_msg])

        if budget <= 0:
            # Extreme case: even system prompt and current query exceed limit
            # Just return them, it will likely error out at the LLM API
            return [msg for msg in [system_msg, latest_msg] if msg]

        # Add recent history until budget is exhausted
        truncated_history = []
        middle_messages = messages[1:-1] if system_msg else messages[:-1]

        # Iterate backwards to keep the most recent history
        for msg in reversed(middle_messages):
            msg_tokens = self.count_message_tokens([msg])
            if budget - msg_tokens >= 0:
                truncated_history.insert(0, msg)
                budget -= msg_tokens
            else:
                break

        final_messages = []
        if system_msg:
            final_messages.append(system_msg)
        final_messages.extend(truncated_history)
        final_messages.append(latest_msg)

        return final_messages


token_counter = TokenCounter()
