from django.contrib import admin
from .models import InternalLetter, LetterAttachment

admin.site.register(InternalLetter)
admin.site.register(LetterAttachment)
