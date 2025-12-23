# views.py
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.staticfiles import finders
import os
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

import os
from django.conf import settings

# Ensure nltk_data path
NLTK_DATA_DIR = os.path.join(settings.BASE_DIR, 'nltk_data')
if NLTK_DATA_DIR not in nltk.data.path:
    nltk.data.path.append(NLTK_DATA_DIR)

# Download required resources safely
required_nltk = [
    ('taggers', 'averaged_perceptron_tagger_eng'),  # this is the one your error wants
    ('tokenizers', 'punkt'),
    ('corpora', 'wordnet'),
    ('corpora', 'omw-1.4'),
    ('corpora', 'stopwords')
]

for folder, resource in required_nltk:
    try:
        nltk.data.find(f"{folder}/{resource}")
    except LookupError:
        nltk.download(resource, download_dir=NLTK_DATA_DIR)


# ---------------------------
# Basic pages
# ---------------------------
def home_view(request):
    return render(request, 'home.html')

def about_view(request):
    return render(request, 'about.html')

def contact_view(request):
    return render(request, 'contact.html')

# ---------------------------
# Animation view (login required)
# ---------------------------
@login_required(login_url='login')
def animation_view(request):
    if request.method == 'POST':
        text = request.POST.get('sen', '')
        text = text.lower()
        words = word_tokenize(text)
        tagged = nltk.pos_tag(words)

        # Determine probable tense
        tense = {
            "future": len([w for w, p in tagged if p == "MD"]),
            "present": len([w for w, p in tagged if p in ["VBP", "VBZ", "VBG"]]),
            "past": len([w for w, p in tagged if p in ["VBD", "VBN"]]),
            "present_continuous": len([w for w, p in tagged if p == "VBG"]),
        }
        probable_tense = max(tense, key=tense.get)

        # Stopwords
        stop_words = set(nltk.corpus.stopwords.words('english'))

        # Lemmatize filtered words
        lr = WordNetLemmatizer()
        filtered_text = []
        for w, p in zip(words, tagged):
            if w not in stop_words:
                if p[1] in ['VBG','VBD','VBZ','VBN','NN']:
                    filtered_text.append(lr.lemmatize(w, pos='v'))
                elif p[1] in ['JJ','JJR','JJS','RBR','RBS']:
                    filtered_text.append(lr.lemmatize(w, pos='a'))
                else:
                    filtered_text.append(lr.lemmatize(w))
        words = filtered_text

        # Adjust tense words
        if probable_tense == "past" and tense["past"] >= 1:
            words = ["Before"] + words
        elif probable_tense == "future" and tense["future"] >= 1:
            if "Will" not in words:
                words = ["Will"] + words
        elif probable_tense == "present" and tense["present_continuous"] >= 1:
            words = ["Now"] + words

        # Map words to animations or split letters if animation not found
        final_words = []
        for w in words:
            path = w + ".mp4"
            f = finders.find(path)
            if not f:
                final_words.extend(list(w))
            else:
                final_words.append(w)
        words = final_words

        return render(request, 'animation.html', {'words': words, 'text': text})
    return render(request, 'animation.html')

# ---------------------------
# Signup
# ---------------------------
def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Signup successful!")
            return redirect('animation')
        else:
            messages.error(request, "Signup failed. Please check the errors below.")
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

# ---------------------------
# Login
# ---------------------------
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next') or request.POST.get('next')
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect(next_url or 'animation')
        else:
            messages.error(request, "Login failed. Please check username and password.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

# ---------------------------
# Logout
# ---------------------------
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('home')
