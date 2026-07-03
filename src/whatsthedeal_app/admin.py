from django.contrib import admin
from .models import (
    Post, 
    Item, 
    Supermarket,
    MealDealItem,
    MealDealSlot,
    MealDeal,
)

# Register your models here.
admin.site.register(Post)
admin.site.register(Item)
admin.site.register(Supermarket)
admin.site.register(MealDealItem)
admin.site.register(MealDealSlot)
admin.site.register(MealDeal)
