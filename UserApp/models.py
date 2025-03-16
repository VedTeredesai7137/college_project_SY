from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    last_seen = models.DateTimeField(default=timezone.now)
    is_online = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

from django.db import models
from django.contrib.auth.models import User

class PDFFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    file = models.FileField(upload_to='pdfs/')
    subject = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    year_published = models.IntegerField()
    day_published = models.CharField(max_length=2, blank=True, null=True)
    month_published = models.CharField(max_length=10, blank=True, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.subject})"

class ChatRoom(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    participants = models.ManyToManyField(User, related_name='chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    is_group = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_groups')

    def __str__(self):
        if self.is_group:
            return f"Group: {self.name or 'Unnamed Group'}"
        else:
            participants = self.participants.all()
            return f"Private Chat between {participants[0]} and {participants[1]}"

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"

    def mark_as_read(self):
        self.is_read = True
        self.save()

