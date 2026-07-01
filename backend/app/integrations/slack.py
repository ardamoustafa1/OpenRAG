import os
from typing import Any

import structlog
from fastapi import APIRouter, Request
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler

logger = structlog.get_logger()
router = APIRouter(tags=["Slack Integration"])

# Initialize Slack App
# In a real multi-tenant system, you'd use OAuth installation flow
# and look up the Slack Token based on the Enterprise ID.
slack_app = App(
    token=os.environ.get("SLACK_BOT_TOKEN", "xoxb-mock-token"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET", "mock-secret"),
)
handler = SlackRequestHandler(slack_app)


@slack_app.command("/ask")  # type: ignore[untyped-decorator]
def handle_ask_command(ack: Any, respond: Any, command: dict[str, Any]) -> None:
    """
    Handles the `/ask` slash command from Slack.
    Queries the RAG platform and responds in the thread.
    """
    ack()
    query = command["text"]
    user_id = command["user_id"]
    logger.info("Slack /ask command received", user_id=user_id, query=query)

    # Mock RAG Call
    # response, sources = rag_engine.chat(query)
    response_text = (
        f"Here is the answer to '{query}' from your secure enterprise documents."
    )

    blocks: list[dict[str, Any]] = [
        {"type": "section", "text": {"type": "mrkdwn", "text": response_text}},
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "📚 *Sources:* [Financial Report Q3], [HR Policy v2]",
                }
            ],
        },
    ]

    respond(blocks=blocks)


@slack_app.event("app_mention")  # type: ignore[untyped-decorator]
def handle_app_mention_events(body: dict[str, Any], say: Any) -> None:
    """
    Handles direct mentions of the bot (e.g. @platformbot).
    """
    event = body.get("event", {})
    query = event.get("text", "").split(">", 1)[-1].strip()

    # Mock RAG Call
    say(f"Responding to your mention regarding: {query}")


@router.post("/slack/events")
async def slack_events(req: Request) -> Any:
    """
    The main webhook endpoint registered in the Slack API Dashboard.
    Passes the raw request to the slack-bolt handler.
    """
    return await handler.handle(req)
