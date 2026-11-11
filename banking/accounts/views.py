from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

def accounts(request):
    template = loader.get_template('accounts.html')
    return HttpResponse(template.render())