from django.db import models
from django.conf import settings
from django.utils import timezone

class LetterStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SENT = "SENT", "Sent"
    ARCHIVED = "ARCHIVED", "Archived"

class InternalLetter(models.Model):
    subject = models.CharField(max_length=200)
    body = models.TextField()
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sent_letters")
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="received_letters")
    cc = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="cc_letters")
    status = models.CharField(max_length=20, choices=LetterStatus.choices, default=LetterStatus.DRAFT)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    read_at = models.DateTimeField(null=True, blank=True)
    read_by = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="read_letters")
    parent_letter = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name="replies")
    
    class Meta:
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.subject} - {self.sender} -> {self.recipient}"
    
    def send(self, send_email_notification=False):
        if self.status == LetterStatus.DRAFT:
            self.status = LetterStatus.SENT
            self.sent_at = timezone.now()
            self.save()
            self.read_by.add(self.sender)
            return True
        return False
    
    def mark_as_read(self, user):
        if user not in self.read_by.all():
            self.read_by.add(user)
            if self.read_at is None and user == self.recipient:
                self.read_at = timezone.now()
                self.save()
    
    def is_read_by(self, user):
        return user in self.read_by.all()
    
    def reply(self, user, body):
        if user != self.recipient and user not in self.cc.all() and user != self.sender:
            raise PermissionError("You cannot reply to this letter")
        
        reply = InternalLetter.objects.create(
            subject=f"Re: {self.subject}",
            body=body,
            sender=user,
            recipient=self.sender,
            parent_letter=self,
            status=LetterStatus.DRAFT
        )
        reply.send()
        return reply

class LetterAttachment(models.Model):
    letter = models.ForeignKey(InternalLetter, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="letter_attachments/%Y/%m/%d/")
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.filename
