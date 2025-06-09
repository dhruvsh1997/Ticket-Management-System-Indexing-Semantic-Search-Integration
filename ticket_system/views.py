from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.contrib.postgres.search import SearchVector
from django.core.cache import cache
from .models import Customer, Ticket, TicketCategory, KnowledgeBase
from .utils import classify_ticket, analyze_sentiment, find_similar_solutions
import json
import logging

# Configure logger
# logger = logging.getLogger('ticket_system.views')
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(levelname)s - %(message)s'
# )

# Configure logging
logger = logging.getLogger('ticket_system')

def dashboard(request):
    if not request.user.is_authenticated:
        logger.warning(f"Unauthenticated access attempt to dashboard by {request.META.get('REMOTE_ADDR')}")
        return redirect('login')
    
    logger.info(f"User {request.user.username} accessed dashboard")
    
    # Cache key for open tickets
    cache_key = f"open_tickets_{request.user.id}"
    tickets = cache.get(cache_key)
    
    if tickets is None:
        logger.debug(f"Cache miss for {cache_key}, querying database")
        tickets = Ticket.objects.filter(status='O').select_related('customer', 'category').order_by('-created_at')
        cache.set(cache_key, tickets, timeout=300)  # Cache for 5 minutes
        logger.info(f"Cached {len(tickets)} open tickets for user {request.user.id}")
    else:
        logger.debug(f"Cache hit for {cache_key}")
    
    # Full-text search
    search_query = request.GET.get('search', '')
    if search_query:
        logger.info(f"User {request.user.username} searched for: {search_query}")
        try:
            tickets = tickets.filter(
                Q(subject__search=search_query) | Q(description__search=search_query)
            )
            logger.debug(f"Search returned {len(tickets)} results")
        except Exception as e:
            logger.error(f"Search query failed: {str(e)}")
            messages.error(request, 'Error performing search')
    
    # ML-based suggestions
    if search_query:
        try:
            similar_solutions = find_similar_solutions(search_query)
            logger.info(f"Found {len(similar_solutions)} similar solutions for query: {search_query}")
        except Exception as e:
            logger.error(f"Error in finding similar solutions: {str(e)}")
            similar_solutions = []
    else:
        similar_solutions = []
    
    context = {
        'tickets': tickets,
        'similar_solutions': similar_solutions,
        'search_query': search_query
    }
    return render(request, 'ticket_system/dashboard.html', context)

def create_ticket(request):
    if not request.user.is_authenticated:
        logger.warning(f"Unauthenticated access attempt to create ticket by {request.META.get('REMOTE_ADDR')}")
        return redirect('login')
    
    if request.method == 'POST':
        subject = request.POST.get('subject')
        description = request.POST.get('description')
        priority = request.POST.get('priority')
        
        logger.info(f"User {request.user.username} attempting to create ticket: {subject}")
        
        try:
            breakpoint()
            user = User.objects.create_user(username=request.user.email, email=request.user.username, password=request.user.password)
            Customer.objects.create(email=request.user.email, user=user)
            customer = Customer.objects.get(email=request.user.email)
            category_id = classify_ticket(description)
            ticket = Ticket.objects.create(
                customer=customer,
                subject=subject,
                description=description,
                priority=priority,
                category=TicketCategory.objects.get(id=category_id),
                sentiment_score=analyze_sentiment(description)
            )
            cache.delete(f"open_tickets_{request.user.id}")  # Invalidate cache
            logger.info(f"Ticket {ticket.id} created successfully by user {request.user.username}")
            messages.success(request, 'Ticket created successfully!')
            return redirect('dashboard')
        except Exception as e:
            logger.error(f"Error creating ticket for user {request.user.username}: {str(e)}")
            messages.error(request, f'Error creating ticket: {str(e)}')
    
    return render(request, 'ticket_system/dashboard.html')

def login_view(request):
    if request.user.is_authenticated:
        logger.info(f"Authenticated user {request.user.username} redirected from login to dashboard")
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        logger.info(f"Login attempt for username: {username}")
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            logger.info(f"User {username} logged in successfully")
            return redirect('dashboard')
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            messages.error(request, 'Invalid credentials')
    
    return render(request, 'ticket_system/login.html')

def register_view(request):
    if request.user.is_authenticated:
        logger.info(f"Authenticated user {request.user.username} redirected from register to dashboard")
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        logger.info(f"Registration attempt for username: {username}, email: {email}")
        
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            Customer.objects.create(email=email, user=user)
            login(request, user)
            logger.info(f"User {username} registered and logged in successfully")
            return redirect('dashboard')
        except Exception as e:
            logger.error(f"Error registering user {username}: {str(e)}")
            messages.error(request, f'Error registering: {str(e)}')
    
    return render(request, 'ticket_system/register.html')

def logout_view(request):
    logger.info(f"User {request.user.username} logged out")
    logout(request)
    return redirect('login')