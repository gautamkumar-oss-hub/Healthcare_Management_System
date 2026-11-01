from django.shortcuts import render

def home(request):
    """
    Public home page - accessible to everyone
    Shows the platform features and chatbot.
    """
    context = {
        'page': 'home',
    }
    return render(request, 'core/home.html', context)
