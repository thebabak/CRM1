from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

@login_required
def test_page(request):
    return HttpResponse("Test page works! <a href='/finance/'>Back to Finance</a>")
