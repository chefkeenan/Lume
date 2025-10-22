from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.contrib.auth.forms import AuthenticationForm

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # opsional: auto-login setelah daftar
            login(request, user)
            return redirect("user_profile")
    else:
        form = RegisterForm()
    return render(request, "register.html", {"form": form})

def login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # TODO: panggil merge cart session -> DB cart di sini
            return redirect("home")
    else:
        form = AuthenticationForm(request)
    return render(request, "login.html", {"form": form})

def logout(request):
    logout(request)
    return redirect("home")