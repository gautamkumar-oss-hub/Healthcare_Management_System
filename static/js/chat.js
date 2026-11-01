document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('chatForm');
    const input = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const messages = document.getElementById('chatMessages');
    const typing = document.getElementById('typingIndicator');
    const status = document.getElementById('chatStatus');

    if (!form || !input || !sendButton || !messages || !typing || !status) return;

    const endpoint = messages.dataset.endpoint;
    const sendLabel = form.dataset.sendLabel || 'Send';
    const waitLabel = form.dataset.waitLabel || 'Sending...';
    let isSending = false;

    function scrollToLatest() {
        messages.scrollTop = messages.scrollHeight;
    }

    function addMessage(content, isUser) {
        const article = document.createElement('article');
        article.className = `message ${isUser ? 'user-message' : 'ai-message'}`;

        const wrapper = document.createElement('div');
        wrapper.className = 'message-wrapper';
        const sender = document.createElement('div');
        sender.className = 'message-sender';
        sender.textContent = isUser ? 'You' : 'Assistant';
        const bubble = document.createElement('div');
        bubble.className = 'message-content';
        const text = document.createElement('div');
        text.className = 'message-text';
        text.textContent = content;
        bubble.appendChild(text);
        const time = document.createElement('time');
        time.className = 'message-time';
        time.dateTime = new Date().toISOString();
        time.textContent = new Intl.DateTimeFormat(undefined, {
            hour: 'numeric', minute: '2-digit'
        }).format(new Date());

        wrapper.append(sender, bubble, time);
        article.appendChild(wrapper);
        messages.appendChild(article);
        scrollToLatest();
    }

    function setSending(value) {
        isSending = value;
        sendButton.disabled = value;
        input.disabled = value;
        sendButton.querySelector('span').textContent = value ? waitLabel : sendLabel;
        typing.hidden = !value;
        if (value) status.textContent = 'Assistant is responding...';
        scrollToLatest();
    }

    function getCsrfToken() {
        const inputToken = form.querySelector('[name="csrfmiddlewaretoken"]');
        if (inputToken?.value) return inputToken.value;
        const cookie = document.cookie.split('; ').find((part) => part.startsWith('csrftoken='));
        return cookie ? decodeURIComponent(cookie.slice('csrftoken='.length)) : '';
    }

    async function sendMessage(message) {
        setSending(true);
        const controller = new AbortController();
        const timeout = window.setTimeout(() => controller.abort(), 60000);
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                credentials: 'same-origin',
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify({ message }),
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(data.error || (response.status === 403
                    ? 'Your session may have expired. Refresh the page and try again.'
                    : 'The assistant could not process that message. Try again.'));
            }
            if (!data.success || typeof data.ai_response !== 'string') {
                throw new Error(data.error || 'The assistant returned an unexpected response.');
            }
            addMessage(data.ai_response, false);
            status.textContent = data.is_authenticated
                ? 'Conversation saved to your account.'
                : 'Guest messages are not saved.';
        } catch (error) {
            const messageText = error.name === 'AbortError'
                ? 'The assistant took too long to respond. Please try again.'
                : error.message;
            addMessage(messageText, false);
            status.textContent = 'Message was not completed.';
        } finally {
            window.clearTimeout(timeout);
            setSending(false);
            input.focus({ preventScroll: true });
        }
    }

    form.addEventListener('submit', (event) => {
        event.preventDefault();
        if (isSending) return;
        const message = input.value.trim();
        if (!message || message.length > 1000) return;
        addMessage(message, true);
        input.value = '';
        sendMessage(message);
    });

    input.addEventListener('input', () => {
        status.textContent = `${input.value.length}/${input.maxLength} characters`;
    });

    document.querySelectorAll('.quick-question').forEach((button) => {
        button.addEventListener('click', () => {
            if (isSending) return;
            input.value = button.dataset.question || '';
            input.focus();
            input.dispatchEvent(new Event('input'));
        });
    });

    scrollToLatest();
});
