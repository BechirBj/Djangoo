from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator

from .forms import CategoryForm, EventForm, LoginForm, ParticipationForm, RegisterForm, ReviewForm
from .models import Badge, Category, Event, EventCategory, Participation, Review, UserBadge



def create_default_badges():
    Badge.objects.get_or_create(name="First Step",      defaults={"condition": "Join your first event."})
    Badge.objects.get_or_create(name="Critic",          defaults={"condition": "Submit your first review."})
    Badge.objects.get_or_create(name="Social Butterfly",defaults={"condition": "Join 5 or more events."})
    Badge.objects.get_or_create(name="Party Starter",   defaults={"condition": "Create your first event."})


def award_badge(user, name):
    badge = Badge.objects.filter(name=name).first()
    if badge:
        UserBadge.objects.get_or_create(user=user, badge=badge)


def check_and_award_badges(user):
    create_default_badges()

    if Participation.objects.filter(user=user).count() >= 1:
        award_badge(user, "First Step")

    if Review.objects.filter(user=user).count() >= 1:
        award_badge(user, "Critic")

    if Participation.objects.filter(user=user).count() >= 5:
        award_badge(user, "Social Butterfly")

    if Event.objects.filter(created_by=user).count() >= 1:
        award_badge(user, "Party Starter")



def home(request):
    events = Event.objects.order_by("date")[:5]
    user_badges = []

    if request.user.is_authenticated:
        user_badges = UserBadge.objects.filter(user=request.user)

    return render(request, "home.html", {
        "upcoming_events": events,
        "user_badges": user_badges,
    })



def event_list(request):
    events = Event.objects.order_by("date")

    q = request.GET.get("q", "")
    if q:
        events = events.filter(title__icontains=q) | events.filter(location__icontains=q)

    print(events)
    paginator = Paginator(events, 6)
    page_obj = paginator.get_page(request.GET.get("page"))
    print(events.values())

    return render(request, "events/list.html", {"page_obj": page_obj, "q": q})



def event_detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    reviews = Review.objects.filter(event=event)
    participant_count = Participation.objects.filter(event=event).count()

    avg_rating = None
    if reviews.exists():
        total = sum(r.rating for r in reviews)
        avg_rating = total / reviews.count()

    user_participation = None
    user_review = None

    if request.user.is_authenticated:
        user_participation = Participation.objects.filter(user=request.user, event=event).first()
        user_review = Review.objects.filter(user=request.user, event=event).first()

    return render(request, "events/detail.html", {
        "event": event,
        "reviews": reviews,
        "participant_count": participant_count,
        "avg_rating": avg_rating,
        "user_participation": user_participation,
        "user_review": user_review,
        "participation_form": ParticipationForm(instance=user_participation),
        "review_form": ReviewForm(instance=user_review),
    })



@login_required
def event_create(request):
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()

            EventCategory.objects.filter(event=event).delete()
            for category in form.cleaned_data.get("categories", []):
                EventCategory.objects.create(event=event, category=category)

            check_and_award_badges(request.user)
            messages.success(request, "Event created!")
            return redirect("event_detail", event_id=event.id)
    else:
        form = EventForm()

    return render(request, "events/form.html", {
        "form": form,
        "title": "Create Event",
        "submit_label": "Create",
    })



@login_required
def event_edit(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    if event.created_by != request.user:
        messages.error(request, "Only the creator can edit this event.")
        return redirect("event_detail", event_id=event.id)

    if request.method == "POST":
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()

            EventCategory.objects.filter(event=event).delete()
            for category in form.cleaned_data.get("categories", []):
                EventCategory.objects.create(event=event, category=category)

            messages.success(request, "Event updated!")
            return redirect("event_detail", event_id=event.id)
    else:
        current_categories = [ec.category for ec in EventCategory.objects.filter(event=event)]
        form = EventForm(instance=event, initial={"categories": current_categories})

    return render(request, "events/form.html", {
        "form": form,
        "title": "Edit Event",
        "submit_label": "Save",
    })



@login_required
def event_delete(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    if event.created_by != request.user:
        messages.error(request, "Only the creator can delete this event.")
        return redirect("event_detail", event_id=event.id)

    if request.method == "POST":
        event.delete()
        messages.success(request, "Event deleted.")
        return redirect("event_list")

    return render(request, "events/confirm_delete.html", {"object": event})


@login_required
def event_join(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    if request.method == "POST":
        participation = Participation.objects.filter(user=request.user, event=event).first()
        form = ParticipationForm(request.POST, instance=participation)

        if form.is_valid():
            p = form.save(commit=False)
            p.user = request.user
            p.event = event
            p.save()
            check_and_award_badges(request.user)
            messages.success(request, "Participation saved!")

    return redirect("event_detail", event_id=event.id)



@login_required
def event_review(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    if request.method == "POST":
        review = Review.objects.filter(user=request.user, event=event).first()
        form = ReviewForm(request.POST, instance=review)

        if form.is_valid():
            r = form.save(commit=False)
            r.user = request.user
            r.event = event
            r.rating = int(form.cleaned_data["rating"])
            r.save()
            check_and_award_badges(request.user)
            messages.success(request, "Review saved!")

    return redirect("event_detail", event_id=event.id)



def category_list_create(request):
    categories = Category.objects.all()

    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category created.")
            return redirect("category_list")
    else:
        form = CategoryForm()

    return render(request, "categories/list.html", {"categories": categories, "form": form})


def category_edit(request, category_id):
    category = get_object_or_404(Category, pk=category_id)

    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated.")
            return redirect("category_list")
    else:
        form = CategoryForm(instance=category)

    return render(request, "categories/form.html", {
        "form": form,
        "title": "Edit Category",
        "submit_label": "Save",
    })


def category_delete(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    if request.method == "POST":
        category.delete()
        messages.success(request, "Category deleted.")
    return redirect("category_list")



def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created! You can now log in.")
            return redirect("login")
    else:
        form = RegisterForm()

    return render(request, "auth/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, "Welcome back!")
            return redirect("home")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm(request)

    return render(request, "auth/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.success(request, "Logged out.")
    return redirect("login")