import json
import logging

from django.http import JsonResponse
from django.shortcuts import render
from django_ratelimit.decorators import ratelimit
from django.views.decorators.http import require_http_methods

from .models import Conversation, Message
from .services import get_gemini_response

logger = logging.getLogger(__name__)


def chat_page(request):
    """Render the public chat page and the signed-in user's recent history."""
    context = {"messages": []}
    if request.user.is_authenticated:
        conversation = Conversation.objects.filter(user=request.user).order_by("-updated_at").first()
        if conversation:
            context["messages"] = list(
                conversation.messages.order_by("-created_at")[:50]
            )[::-1]
    else:
        context["is_guest"] = True
    return render(request, "chatbot/chat.html", context)


@ratelimit(key="ip", rate="20/m", method="POST", block=False)
@require_http_methods(["POST"])
def send_message(request):
    """Handle one bounded JSON chat request for a guest or authenticated user."""
    if getattr(request, "limited", False):
        return JsonResponse({"error": "Too many messages. Please wait a minute and try again."}, status=429)
    content_length = request.META.get("CONTENT_LENGTH") or ""
    if content_length.isdigit() and int(content_length) > 8192:
        return JsonResponse({"error": "Request is too large."}, status=413)
    if request.content_type != "application/json":
        return JsonResponse({"error": "Content-Type must be application/json."}, status=415)

    body = request.body
    if len(body) > 8192:
        return JsonResponse({"error": "Request is too large."}, status=413)
    try:
        data = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON format."}, status=400)

    if not isinstance(data, dict) or not isinstance(data.get("message"), str):
        return JsonResponse({"error": "Message must be text."}, status=400)
    user_message = data["message"].strip()
    if not user_message:
        return JsonResponse({"error": "Message cannot be empty."}, status=400)
    if len(user_message) > 1000:
        return JsonResponse({"error": "Message too long. Limit it to 1000 characters."}, status=400)

    recent_messages = []
    conversation = None
    user_msg = None
    if request.user.is_authenticated:
        conversation = Conversation.objects.filter(user=request.user).order_by("-updated_at").first()
        if conversation is None:
            conversation = Conversation.objects.create(user=request.user)
        user_msg = Message.objects.create(
            conversation=conversation,
            content=user_message,
            is_from_user=True,
        )
        recent_messages = list(
            conversation.messages.exclude(pk=user_msg.pk).order_by("-created_at")[:10]
        )[::-1]

    try:
        ai_response = get_gemini_response(user_message, recent_messages, request.user)
    except Exception:
        logger.exception("Chat service failed")
        return JsonResponse({"error": "The assistant is temporarily unavailable."}, status=503)

    if request.user.is_authenticated:
        ai_msg = Message.objects.create(
            conversation=conversation,
            content=ai_response,
            is_from_user=False,
        )
        conversation.save(update_fields=["updated_at"])
        return JsonResponse(
            {
                "success": True,
                "ai_response": ai_response,
                "user_message_id": user_msg.pk,
                "ai_message_id": ai_msg.pk,
                "is_authenticated": True,
            }
        )
    return JsonResponse(
        {
            "success": True,
            "ai_response": ai_response,
            "is_authenticated": False,
            "message": "Log in to save your conversation history.",
        }
    )
