import json

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.shortcuts import render, redirect, get_object_or_404
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import generic
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from .forms import PostCreateForm

from .models import (
    Item,
    MealDeal,
    MealDealSlot,
    MealDealItem,
    Post,
    Preference,
)

MULTI_SIDE_SUPERMARKETS = {"Booths"}

def index(request):
    return render(request, "index.html")

def create_post(request):
    if request.method == "POST":
        form = PostCreateForm(request.POST, request.FILES)
        if form.is_valid():
            supermarket = form.cleaned_data["supermarket"]
            sides = [form.cleaned_data["side"]]
            side_2 = form.cleaned_data["side_2"].strip()
            if side_2 and supermarket.name in MULTI_SIDE_SUPERMARKETS:
                sides.append(side_2)
            description = form.cleaned_data["description"]
            image = form.cleaned_data["image"]

            main_item, _ = Item.objects.get_or_create(
                name=normalize_item_name(form.cleaned_data["main"]),
                defaults={"item_type": Item.ItemType.MAIN},
            )

            side_items = []
            for side_name in sides:
                side_item, _ = Item.objects.get_or_create(
                    name=normalize_item_name(side_name),
                    defaults={"item_type": Item.ItemType.SIDE},
                )
                side_items.append(side_item)
            drink_item, _ = Item.objects.get_or_create(
                name=normalize_item_name(form.cleaned_data["drink"]),
                defaults={"item_type": Item.ItemType.DRINK},
            )

            meal_deal = get_or_create_meal_deal(
                supermarket=supermarket,
                main_item=main_item,
                side_items=side_items,
                drink_item=drink_item,
                description=description,
            )

            user = request.user if request.user.is_authenticated else get_guest_user()
            Post.objects.create(
                user=user,
                meal_deal=meal_deal,
                description=description,
                image=image,
            )
            return redirect("whatsthedeal:post-list")
        else:
            messages.add_message(request, messages.WARNING, "Something went wrong:")
            if "image" in form.errors:
                messages.add_message(request, messages.ERROR, "Please upload a valid image file.")
            else:
                messages.add_message(request, messages.ERROR, "Please make sure you have filled all the required fields.")
    else:
        # Clear old messages
        storage = messages.get_messages(request)
        storage.used = True
        form = PostCreateForm()

    return render(request, "whatsthedeal_app/post_form.html", {
        "form": form,
        "multi_side_supermarkets": json.dumps(list(MULTI_SIDE_SUPERMARKETS)),
    })
    
def feed(request):
    template_name = "whatsthedeal_app/feed.html"

    posts = Post.objects.select_related(
        "user",
        "meal_deal__supermarket",
    ).prefetch_related(
        "meal_deal__entries__item",
        "meal_deal__entries__slot",
    )

    filter = request.GET.get('filter')

    if filter == 'newest':
        posts = posts.order_by("-created_at")
    elif filter == 'most-likes':
        posts = posts.order_by("-likes")
    elif filter == 'most-dislikes':
        posts = posts.order_by("-dislikes")
    else:
        # Set default to newest
        filter == 'newest'
        posts = posts.order_by("-created_at")

    feed = build_post_feed(posts=posts)

    return render(request, template_name, {
        'feed': feed,
        'filter': filter
    })

class PostDetailView(generic.DetailView):
    model = Post
    template_name = "whatsthedeal_app/view.html"

    def get_queryset(self):
        return Post.objects.select_related(
            "user",
            "meal_deal__supermarket",
        ).prefetch_related(
            "meal_deal__entries__item",
            "meal_deal__entries__slot",
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = [context.get("object") or self.object]
        context["post"] = build_post_feed(posts=post)[0] # only has 1 item
        return context

@login_required
def postpreference(request, postid, userpreference):
    if request.method == "POST":
        eachpost = get_object_or_404(Post, id=postid)
        # Prefer an explicit `next` parameter from the form, then fall back to the HTTP referer.
        next_url = request.POST.get("next") or request.META.get("HTTP_REFERER")
        # Validate to avoid open redirect vulnerabilities.
        if next_url and not url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
            next_url = None
        obj = ''
        valueobj = ''
        try:
            obj= Preference.objects.get(user=request.user, post=eachpost)
            valueobj= obj.value #value of userpreference
            valueobj= int(valueobj)
            userpreference= int(userpreference)
            if valueobj != userpreference:
                # Switch preference

                obj.delete()
                upref= Preference()
                upref.user= request.user
                upref.post= eachpost
                upref.value= userpreference

                if userpreference == 1 and valueobj != 1:
                    eachpost.likes += 1
                    eachpost.dislikes -=1
                elif userpreference == 2 and valueobj != 2:
                    eachpost.dislikes += 1
                    eachpost.likes -= 1

                upref.save()
                eachpost.save()
            elif valueobj == userpreference:
                # Remove preference
                obj.delete()
                if userpreference == 1:
                    eachpost.likes -= 1
                elif userpreference == 2:
                    eachpost.dislikes -= 1
                eachpost.save()
        except Preference.DoesNotExist:
            # New preference
            upref= Preference()
            upref.user= request.user
            upref.post= eachpost
            upref.value= userpreference
            userpreference= int(userpreference)
            if userpreference == 1:
                eachpost.likes += 1
            elif userpreference == 2:
                eachpost.dislikes +=1
            upref.save()
            eachpost.save()
        return redirect(next_url or 'whatsthedeal:post-list')
    else:
        eachpost= get_object_or_404(Post, id=postid)
        context = {'eachpost': eachpost, 'postid': postid}

        return render (request, 'posts/view.html', context)

# Helpers

def get_guest_user():
    User = get_user_model()
    guest_username = "anonymous"
    guest_email = "guest@example.com"
    user, _ = User.objects.get_or_create(
        username=guest_username,
        defaults={"email": guest_email},
    )
    return user

def normalize_item_name(value):
    return " ".join(value.strip().title().split())

def build_post_feed(posts):
    slot_order = {"MAIN": 0, "SIDE": 1, "DRINK": 2}
    feed = []
    for post in posts:
        entries = sorted(
            post.meal_deal.entries.all(),
            key=lambda entry: slot_order.get(entry.slot.slot_type, 99),
        )
        feed.append({
            "post": post,
            "user": post.user,
            "date": post.created_at,
            "description": post.description,
            "image": post.image,
            "supermarket": post.meal_deal.supermarket,
            "components": [entry.item for entry in entries],
            "likes": post.likes,
            "dislikes": post.dislikes,
            "id": post.id
        })
    return feed

def get_or_create_meal_deal(supermarket, main_item, side_items, drink_item, description=""):
    item_ids = {main_item.id, drink_item.id} | {item.id for item in side_items}
    existing = MealDeal.objects.filter(supermarket=supermarket).prefetch_related("items")
    for deal in existing:
        if set(deal.items.values_list("id", flat=True)) == item_ids:
            return deal

    main_item.supermarkets.add(supermarket)
    for side_item in side_items:
        side_item.supermarkets.add(supermarket)
    drink_item.supermarkets.add(supermarket)

    meal_deal = MealDeal.objects.create(supermarket=supermarket)
    slots = {
        "MAIN": MealDealSlot.objects.create(
            meal_deal=meal_deal,
            slot_type=MealDealSlot.SlotType.MAIN,
            min_items=1,
            max_items=1,
        ),
        "SIDE": MealDealSlot.objects.create(
            meal_deal=meal_deal,
            slot_type=MealDealSlot.SlotType.SIDE,
            min_items=1,
            max_items=2,
        ),
        "DRINK": MealDealSlot.objects.create(
            meal_deal=meal_deal,
            slot_type=MealDealSlot.SlotType.DRINK,
            min_items=1,
            max_items=1,
        ),
    }
    MealDealItem.objects.create(meal_deal=meal_deal, item=main_item, slot=slots["MAIN"])
    for side_item in side_items:
        MealDealItem.objects.create(meal_deal=meal_deal, item=side_item, slot=slots["SIDE"])
    MealDealItem.objects.create(meal_deal=meal_deal, item=drink_item, slot=slots["DRINK"])
    return meal_deal