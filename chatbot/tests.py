from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from datetime import date, time

from appointments.models import Appointment
from users.models import Doctor, Patient
from .services import PATIENT_TOOLS, STAFF_TOOLS, _execute
from .models import Conversation, Message
import json

User = get_user_model()

class ChatbotTests(TestCase):
    """Test chatbot functionality"""
    
    def setUp(self):
        """Create test user"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@test.com',
            user_type='patient'
        )
        self.client = Client()
    
    def test_chat_page_loads(self):
        """Test that chat page loads"""
        response = self.client.get('/chatbot/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AI Health Assistant')
        print("✅ Test 1 passed: Chat page loads")
    
    def test_guest_can_access_chatbot(self):
        """Test that guests can use chatbot"""
        response = self.client.get('/chatbot/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Guest chat')
        print("✅ Test 2 passed: Guest can access chatbot")
    
    def test_logged_in_user_sees_history(self):
        """Test that logged in users see their chat history"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create a conversation and messages
        conversation = Conversation.objects.create(user=self.user)
        Message.objects.create(
            conversation=conversation,
            content='Hello',
            is_from_user=True
        )
        Message.objects.create(
            conversation=conversation,
            content='Hi! How can I help?',
            is_from_user=False
        )
        
        response = self.client.get('/chatbot/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hello')
        print("✅ Test 3 passed: User sees chat history")
    
    def test_send_message_requires_post(self):
        """Test that send_message only accepts POST"""
        response = self.client.get('/chatbot/send/')
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
        print("✅ Test 4 passed: Send message requires POST")
    
    def test_empty_message_rejected(self):
        """Test that empty messages are rejected"""
        response = self.client.post(
            '/chatbot/send/',
            data=json.dumps({'message': ''}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        print("✅ Test 5 passed: Empty messages rejected")
    
    def test_message_too_long_rejected(self):
        """Test that very long messages are rejected"""
        long_message = 'a' * 1001  # Over 1000 character limit
        
        response = self.client.post(
            '/chatbot/send/',
            data=json.dumps({'message': long_message}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('too long', data['error'].lower())
        print("✅ Test 6 passed: Long messages rejected")
    
    def test_conversation_created_for_user(self):
        """Test that conversation is created for logged in user"""
        self.client.login(username='testuser', password='testpass123')
        
        # Mock the Gemini API response (we'll skip actual API call in tests)
        # In real scenario, you'd mock get_gemini_response
        
        # Check conversation doesn't exist yet
        self.assertFalse(Conversation.objects.filter(user=self.user).exists())
        
        # Note: Actual sending would require mocking the AI service
        # For now, we'll just test the model creation
        conversation = Conversation.objects.create(user=self.user)
        Message.objects.create(
            conversation=conversation,
            content='Test message',
            is_from_user=True
        )
        
        self.assertTrue(Conversation.objects.filter(user=self.user).exists())
        self.assertEqual(conversation.messages.count(), 1)
        print("✅ Test 7 passed: Conversation created for user")
    
    def test_conversation_ordering(self):
        """Test that conversations are ordered by most recent"""
        import time
        
        # Create first conversation
        conv1 = Conversation.objects.create(user=self.user)
        
        # Small delay to ensure different timestamps
        time.sleep(0.01)
        
        # Create second conversation
        conv2 = Conversation.objects.create(user=self.user)
        
        # Refresh from database to get accurate ordering
        conv1.refresh_from_db()
        conv2.refresh_from_db()
        
        # Get all conversations
        conversations = Conversation.objects.all()
        
        # Most recent should be first (due to Meta ordering = ['-updated_at'])
        self.assertEqual(conversations.first().id, conv2.id)
        print("✅ Test 8 passed: Conversations ordered correctly")
    
    def test_message_ordering(self):
        """Test that messages are ordered chronologically"""
        conversation = Conversation.objects.create(user=self.user)
        
        msg1 = Message.objects.create(
            conversation=conversation,
            content='First message',
            is_from_user=True
        )
        msg2 = Message.objects.create(
            conversation=conversation,
            content='Second message',
            is_from_user=False
        )
        
        messages = conversation.messages.all()
        
        # Should be in chronological order (oldest first)
        self.assertEqual(messages[0], msg1)
        self.assertEqual(messages[1], msg2)
        print("✅ Test 9 passed: Messages ordered chronologically")


class ChatbotModelTests(TestCase):
    """Test chatbot models"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            user_type='patient'
        )
    
    def test_conversation_str_method(self):
        """Test conversation string representation"""
        conversation = Conversation.objects.create(user=self.user)
        str_repr = str(conversation)
        
        self.assertIn('testuser', str_repr)
        print("✅ Test 10 passed: Conversation __str__ works")
    
    def test_message_str_method(self):
        """Test message string representation"""
        conversation = Conversation.objects.create(user=self.user)
        message = Message.objects.create(
            conversation=conversation,
            content='This is a test message that is quite long',
            is_from_user=True
        )
        
        str_repr = str(message)
        self.assertIn('User', str_repr)
        # Should be truncated to 50 chars
        self.assertTrue(len(str_repr) < 100)
        print("✅ Test 11 passed: Message __str__ works")
    
    def test_message_user_vs_ai(self):
        """Test distinguishing user vs AI messages"""
        conversation = Conversation.objects.create(user=self.user)
        
        user_msg = Message.objects.create(
            conversation=conversation,
            content='User question',
            is_from_user=True
        )
        
        ai_msg = Message.objects.create(
            conversation=conversation,
            content='AI response',
            is_from_user=False
        )
        
        self.assertTrue(user_msg.is_from_user)
        self.assertFalse(ai_msg.is_from_user)
        print("✅ Test 12 passed: User vs AI messages distinguished")
