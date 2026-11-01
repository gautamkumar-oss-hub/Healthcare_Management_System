from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from .models import Conversation, Message
from .services import get_gemini_response
from django.contrib import messages

def chat_page(request):
    """
    Public chat page - accessible to everyone
    Logged-in users get saved history, guests don't
    """
    context = {}
    
    # If user is logged in, load their conversation history
    if request.user.is_authenticated:
        try:
            conversation = Conversation.objects.get(user=request.user)
            context['messages'] = conversation.messages.all()[:50]  # Last 50 messages
        except Conversation.DoesNotExist:
            context['messages'] = []
    else:
        # For guests, no history
        context['messages'] = []
        context['is_guest'] = True
    
    return render(request, 'chatbot/chat.html', context)

# ✅ REMOVED @csrf_exempt - Now using proper CSRF token
@require_http_methods(["POST"])
def send_message(request):
    """
    Handle chat messages via AJAX
    Works for both logged-in users and guests
    ✅ FIXED: Now properly handles CSRF tokens
    """
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)
        
        # Limit message length
        if len(user_message) > 1000:
            return JsonResponse({'error': 'Message too long. Please limit to 1000 characters.'}, status=400)
        
        # Get conversation history for context
        recent_messages = []
        
        # Only save for logged-in users
        if request.user.is_authenticated:
            # Get or create conversation
            conversation, created = Conversation.objects.get_or_create(
                user=request.user,
                defaults={'user': request.user}
            )
            
            # Save user message
            user_msg = Message.objects.create(
                conversation=conversation,
                content=user_message,
                is_from_user=True
            )
            
            # Get conversation history (last 10 messages for performance)
            recent_messages = list(
                conversation.messages.exclude(pk=user_msg.pk).order_by('-created_at')[:10]
            )[::-1]
        
        # Get AI response (works for both logged-in and guest users)
        ai_response = get_gemini_response(user_message, recent_messages, request.user)
        
        # Save AI response only for logged-in users
        if request.user.is_authenticated:
            ai_msg = Message.objects.create(
                conversation=conversation,
                content=ai_response,
                is_from_user=False
            )
            
            # Update conversation timestamp
            conversation.save()
            
            return JsonResponse({
                'success': True,
                'ai_response': ai_response,
                'user_message_id': user_msg.id,
                'ai_message_id': ai_msg.id,
                'is_authenticated': True
            })
        else:
            # Guest user - no saving
            return JsonResponse({
                'success': True,
                'ai_response': ai_response,
                'is_authenticated': False,
                'message': 'Login to save your conversation history'
            })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        print(f"Chat error: {e}")  # For debugging
        return JsonResponse({
            'error': 'Something went wrong. Please try again.',
            'debug': str(e) if request.user.is_superuser else None
        }, status=500)
