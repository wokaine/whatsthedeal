from django.contrib import admin
from .models import (
    Post, 
    Item, 
    Supermarket,
    MealDealItem,
    MealDealSlot,
    MealDeal,
    Comment,
)

# Register your models here.
admin.site.register(Post)
admin.site.register(Item)
admin.site.register(Supermarket)
admin.site.register(MealDealItem)
admin.site.register(MealDealSlot)
admin.site.register(MealDeal)
admin.site.register(Comment)
