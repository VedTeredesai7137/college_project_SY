from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.cache import never_cache
from .forms import SignUpForm, LoginForm, PDFFileForm, MessageForm, GroupChatForm
from .models import PDFFile, ChatRoom, Message, UserProfile
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.forms import AuthenticationForm


# Sign up view
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'notes/signup.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')  # If the user is already logged in, redirect to dashboard

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')  # Redirect to the dashboard after successful login
    else:
        form = AuthenticationForm()

    return render(request, 'notes/login.html', {'form': form})
# Dashboard view
@never_cache
@login_required(login_url='login')
def dashboard(request):
    return render(request, 'notes/dashboard.html')

# Profile view for uploading PDFs
@never_cache
@login_required(login_url='login')
def profile(request):
    if request.method == 'POST':
        form = PDFFileForm(request.POST, request.FILES)
        if form.is_valid():
            pdf_file = form.save(commit=False)
            pdf_file.user = request.user  # Assign logged-in user
            pdf_file.day_published = form.cleaned_data.get('day_published', '')
            pdf_file.month_published = form.cleaned_data.get('month_published', '')
            pdf_file.save()
            messages.success(request, "File uploaded successfully!")
            return redirect('profile')
    else:
        form = PDFFileForm()

    # Get only logged-in user's PDFs
    user_pdfs = PDFFile.objects.filter(user=request.user).order_by('-upload_date')

    return render(request, 'notes/profile.html', {'form': form, 'user_pdfs': user_pdfs})

from django.shortcuts import render
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from .models import PDFFile  # Assuming your model name is PDFFile

@never_cache
@login_required(login_url='login')
def ViewNotes(request):
    query = request.GET.get('q', '')  # Get search query
    selected_subject = request.GET.get('subject', '')  # Get selected subject
    selected_day = request.GET.get('day_published', '')  # Get selected day
    selected_month = request.GET.get('month_published', '')  # Get selected month
    selected_year = request.GET.get('year_published', '')  # Get selected year

    # Fetch all notes ordered by upload date
    pdf_files = PDFFile.objects.all().order_by('-upload_date')

    # Apply search filter if query exists
    if query:
        pdf_files = pdf_files.filter(
            Q(subject__icontains=query) | Q(name__icontains=query)
        )

    # Apply subject filter only if a subject is selected
    if selected_subject:
        pdf_files = pdf_files.filter(subject=selected_subject)

    # Apply date filters only if selected
    if selected_day:
        pdf_files = pdf_files.filter(day_published=selected_day)
    if selected_month:
        pdf_files = pdf_files.filter(month_published=selected_month)
    if selected_year:
        pdf_files = pdf_files.filter(year_published=selected_year)

    # Pass predefined lists for dropdowns
    days_list = [str(i) for i in range(1, 32)]
    months_list = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    years_list = [str(i) for i in range(2000, 2031)]

    return render(request, 'notes/ViewNotes.html', {
        'pdf_files': pdf_files,
        'query': query,
        'selected_subject': selected_subject,
        'selected_day': selected_day,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'days_list': days_list,
        'months_list': months_list,
        'years_list': years_list
    })

# Logout view
@never_cache
@login_required(login_url='login')
def logout_view(request):
    logout(request)
    return redirect('login')

# About Us page
@never_cache
@login_required(login_url='login')
def AboutUs(request):
    return render(request, 'notes/AboutUs.html')

# Chat functionality - Main chat index
@login_required
def index(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    profile.is_online = True
    profile.last_seen = timezone.now()
    profile.save()

    users = User.objects.exclude(username=request.user.username)
    user_data = []
    for user in users:
        chat_room = ChatRoom.objects.filter(participants=request.user).filter(participants=user).first()
        last_message = chat_room.messages.last() if chat_room else None
        unread_count = chat_room.messages.filter(sender=user, is_read=False).count() if chat_room else 0
        user_data.append({
            'user': user,
            'last_message': last_message,
            'unread_count': unread_count,
            'is_online': hasattr(user, 'userprofile') and user.userprofile.is_online
        })
    return render(request, 'chat/index.html', {'user_data': user_data})


from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import PDFFile  # Ensure your model name matches
@login_required(login_url='login')
def delete_pdf(request, pdf_id):
    pdf_file = get_object_or_404(PDFFile, id=pdf_id)

    if pdf_file.user != request.user:  # Ensure only the owner can delete
        messages.error(request, "You are not authorized to delete this file.")
        return redirect('profile')

    pdf_file.delete()
    messages.success(request, "File deleted successfully!")
    return redirect('profile')

# Chat room for private chat
@login_required
def chat_room(request, username):
    # Get the other user by their username
    other_user = get_object_or_404(User, username=username)

    # Find or create the chat room for the two users
    chat_room = ChatRoom.objects.filter(participants=request.user).filter(participants=other_user).first()
    if not chat_room:
        chat_room = ChatRoom.objects.create()
        chat_room.participants.add(request.user, other_user)

    # Mark unread messages from the other user as read
    chat_room.messages.filter(sender=other_user, is_read=False).update(is_read=True)

    # Handling POST request for sending a new message
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.room = chat_room  # Associate the message with the chat room
            message.sender = request.user  # Set the sender to the current user
            message.receiver = other_user  # Set the receiver to the other user
            message.save()  # Save the message to the database
            return redirect('chat_room', username=username)  # Redirect back to the chat room
    else:
        form = MessageForm()  # If GET request, display the form for entering a message

    # Fetch all messages in the chat room to display them
    messages_list = chat_room.messages.all()

    # Render the template with context
    return render(request, 'chat/chat_room.html', {
        'other_user': other_user,
        'messages': messages_list,
        'form': form,
        'room': chat_room
    })


# Group chat creation
@login_required
def create_group(request):
    if request.method == 'POST':
        form = GroupChatForm(request.POST, user=request.user)
        if form.is_valid():
            group = form.save(commit=False)
            group.is_group = True
            group.created_by = request.user
            group.save()
            participants = form.cleaned_data['participants']
            group.participants.add(request.user, *participants)
            return redirect('group_chat', group_id=group.id)
    else:
        form = GroupChatForm(user=request.user)
    return render(request, 'chat/create_group.html', {'form': form})


@login_required
def group_chat(request, group_id):
    # Fetch the group chat room by ID
    chat_room = get_object_or_404(ChatRoom, id=group_id)

    # Get messages related to this chat room
    messages = chat_room.messages.all()  # Use 'messages' because 'related_name' is set as 'messages'

    # Handle form submission for sending a message
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user  # Set the sender to the logged-in user
            message.room = chat_room       # Link the message to the correct chat room
            message.receiver = None        # For group chat, no specific receiver, set to None
            message.save()
            return redirect('group_chat', group_id=group_id)  # Redirect back to the same chat room
    else:
        form = MessageForm()

    return render(request, 'chat/group_chat.html', {
        'chat_room': chat_room,
        'messages': messages,
        'form': form
    })

def leave_group(request, group_id):
    # Fetch the group chat room by ID
    chat_room = get_object_or_404(ChatRoom, id=group_id)

    # Ensure the user is a member of the chat room (if necessary)
    if request.user in chat_room.members.all():
        # Remove the user from the group
        chat_room.members.remove(request.user)

    # Redirect to the group chat or another appropriate page
    return redirect('group_chat', group_id=group_id)

# API for getting unread message count for user
@login_required
def get_unread_count(request):
    """
    Get the number of unread messages for the logged-in user.
    """
    unread_count = Message.objects.filter(receiver=request.user, is_read=False).count()
    return JsonResponse({'unread_count': unread_count})

@login_required
def add_group_members(request, group_id):
    group = get_object_or_404(ChatRoom, id=group_id, is_group=True)
    if request.user != group.created_by:
        return redirect('group_chat', group_id=group_id)

    if request.method == 'POST':
        form = GroupChatForm(request.POST, user=request.user, instance=group)
        if form.is_valid():
            group = form.save()
            return redirect('group_chat', group_id=group_id)
    else:
        form = GroupChatForm(user=request.user, instance=group)

    return render(request, 'chat/add_group_members.html', {'form': form, 'group': group})


'''
how signup works
In Django, the signup process involves a combination of forms, models, and views. Here's how it works, broken down step by step:

### 1. **Forms (SignUpForm in `forms.py`)**
   - The `SignUpForm` is a subclass of Django's built-in `UserCreationForm`, which is a form Django provides to handle user registration.
   - In `SignUpForm`, you've added an extra field `email`, which is required for the user to sign up.
   - The `Meta` class tells Django that this form will work with the `User` model (which is a built-in model in Django to handle user-related data like usernames and passwords).
   - The `fields` list specifies which fields will be shown in the form: `username`, `email`, `password1` (for entering the password), and `password2` (for confirming the password).

### 2. **Models (UserProfile in `models.py`)**
   - You’ve extended Django’s `User` model with `UserProfile` using a `OneToOneField`, which links each `UserProfile` to one unique user.
   - This allows you to add more information (like a bio) about the user without changing the default `User` model.

### 3. **View (signup in `views.py`)**
   - The `signup` view handles what happens when the user visits the signup page and submits the form.

#### Step-by-step of the `signup` view:
   - **Check if the request method is POST**:
     - `if request.method == 'POST':` checks if the user has submitted the form. When the form is submitted, the method will be `POST`.
   - **Create a form object with the submitted data**:
     - `form = SignUpForm(request.POST)` creates an instance of the `SignUpForm` with the data the user entered.
   - **Validate the form**:
     - `if form.is_valid():` checks if the data entered by the user is correct, such as the username being unique and both passwords matching.
   - **Save the user**:
     - `form.save()` saves the new user to the database. Django takes care of hashing the password, ensuring that it's stored securely.
   - **Get the username**:
     - `username = form.cleaned_data.get('username')` retrieves the cleaned username from the form data.
   - **Show success message**:
     - `messages.success(request, f'Account created for {username}!')` shows a message confirming that the account has been successfully created.
   - **Redirect to the login page**:
     - `return redirect('login')` redirects the user to the login page after successfully signing up.
   - **If it’s a GET request**:
     - If the user hasn’t submitted the form (i.e., they just visited the page), `form = SignUpForm()` creates a blank form to display.
   - **Render the signup page**:
     - `return render(request, 'signup.html', {'form': form})` renders the `signup.html` template, passing the empty or filled form to the template.

### How it All Fits Together:
   - The **form** collects user input like username, email, and password.
   - The **view** processes the form data, checks if it's valid, and saves it to the database (creating a new user).
   - The **model** stores the user data (in the `User` model) and any additional information (in the `UserProfile` model).
   - The **template** (`signup.html`) displays the form to the user and shows any error messages if something is wrong (like mismatched passwords).'''
'''{% extends 'base.html' %}
{% load static %}

{% block title %}
Sharing Files
{% endblock %}

{% block content %}
<div class="container" style="position: relative; background: white; max-width: 1440px; height: 1024px;">
    <!-- Updated Image -->
    <img src="{% static 'note.jpeg' %}" alt="Image" style="max-width: 100%; height: auto; margin-top: 50px; display: block; margin-left: auto; margin-right: auto;">

    <!-- Main Header Text -->
    <div class="text-center" style="color: #03099F; font-size: 50px; font-family: Montserrat; font-weight: 700; margin-top: 50px;">
        Sharing Files
    </div>

    <!-- Subheading Text -->
    <div class="text-center" style="color: black; font-size: 20px; font-family: Raleway; font-weight: 500; margin-top: 20px;">
        Transforming the Way You Share Files.<br>
        Secure, Fast, and User-Friendly Solutions for Everyone.
    </div>

    <!-- Navigation Links -->
    <div class="d-flex justify-content-center mt-5">
        <a href="#" class="mx-3" style="color: black; font-size: 20px; font-family: Montserrat; font-weight: 400; text-decoration: none;">Chat</a>
        <a href="{% url 'ViewNotes' %}" class="mx-3" style="color: black; font-size: 20px; font-family: Montserrat; font-weight: 400; text-decoration: none;">View Notes</a>
        <a href="{% url 'profile' %}" class="mx-3" style="color: black; font-size: 20px; font-family: Montserrat; font-weight: 400; text-decoration: none;">Profile</a>
        <a href="#" class="mx-3" style="color: black; font-size: 20px; font-family: Montserrat; font-weight: 400; text-decoration: none;">About Us</a>
    </div>

    <!-- Updated Call-to-Action Button -->
    <div class="d-flex justify-content-center mt-4">
        <a href="{% url 'ViewNotes' %}" class="btn btn-warning" style="font-size: 30px; font-family: Montserrat; font-weight: 700; border-radius: 40px; padding: 10px 40px;">
            View Notes
        </a>
    </div>

    <!-- Logo or Branding Text -->
    <div class="text-center" style="color: #03099F; font-size: 35px; font-family: Montserrat; font-weight: 600; margin-top: 50px;">
        Notes Sharing
    </div>

    <!-- Upload Notes Section -->
    <div class="container mt-5">
        <h3>Upload Notes</h3>
        <form action="{% url 'profile' %}" method="POST" enctype="multipart/form-data">
            {% csrf_token %}
            <div class="form-group">
                <label for="note_title">Title:</label>
                <input type="text" class="form-control" id="note_title" name="note_title" required>
            </div>
            <div class="form-group">
                <label for="note_file">Select file:</label>
                <input type="file" class="form-control" id="note_file" name="note_file" accept=".pdf, .doc, .docx, .ppt, .pptx" required>
            </div>
            <button type="submit" class="btn btn-primary">Upload</button>
        </form>
    </div>
</div>
{% endblock %}
'''

"""{% extends 'base.html' %}
{% load static %}

{% block title %}
Sharing Files
{% endblock %}

{% block content %}
<div class="container-fluid" style="position: relative; background: white; max-width: 1440px; height: 1024px;">
    <!-- Updated Image -->
    <img src="{% static 'note.jpeg' %}" alt="Image" class="img-fluid d-block mx-auto mt-4" style="max-width: 693px; height: auto;">

    <!-- Main Header Text -->
    <div class="text-center mt-5" style="color: #03099F; font-size: 50px; font-family: Montserrat; font-weight: 700;">
        Sharing Files
    </div>

    <!-- Subheading Text -->
    <div class="text-center mt-3" style="color: black; font-size: 20px; font-family: Raleway; font-weight: 500;">
        Transforming the Way You Share Files.<br/>
        Secure, Fast, and User-Friendly Solutions for Everyone.
    </div>

    <!-- Navigation Links -->
    <div class="d-flex justify-content-center mt-5">
        <a href="#" class="mx-3" style="color: black; font-size: 20px; font-family: Montserrat; font-weight: 400; text-decoration: none;">Chat</a>
        <a href="{% url 'ViewNotes' %}" class="mx-3" style="color: black; font-size: 20px; font-family: Montserrat; font-weight: 400; text-decoration: none;">View Notes</a>
        <a href="{% url 'profile' %}" class="mx-3" style="color: black; font-size: 20px; font-family: Montserrat; font-weight: 400; text-decoration: none;">Profile</a>
        <a href="#" class="mx-3" style="color: black; font-size: 20px; font-family: Montserrat; font-weight: 400; text-decoration: none;">About Us</a>
    </div>

    <!-- Updated Call-to-Action Button -->
    <div class="d-flex justify-content-center mt-4">
        <a href="{% url 'ViewNotes' %}" class="btn btn-warning" style="font-size: 30px; font-family: Montserrat; font-weight: 700; border-radius: 40px; padding: 10px 40px;">
            View Notes
        </a>
    </div>

    <!-- Logo or Branding Text -->
    <div class="text-center mt-5" style="color: #03099F; font-size: 35px; font-family: Montserrat; font-weight: 600;">
        Notes Sharing
    </div>

</div>
{% endblock %}
"""