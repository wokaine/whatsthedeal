from django.conf import settings
from django.db import models
from django.db.models import Q


class Supermarket(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Item(models.Model):
    class ItemType(models.TextChoices):
        MAIN = "MAIN", "Main"
        SIDE = "SIDE", "Side"
        DRINK = "DRINK", "Drink"

    name = models.CharField(max_length=100)
    item_type = models.CharField(max_length=10, choices=ItemType.choices)
    supermarkets = models.ManyToManyField(
        Supermarket,
        related_name="items",
        blank=True,
    )

    def __str__(self):
        return self.name


class MealDeal(models.Model):
    supermarket = models.ForeignKey(
        Supermarket,
        on_delete=models.CASCADE,
        related_name="meal_deals",
    )
    items = models.ManyToManyField(
        Item,
        related_name="meal_deals",
        through="MealDealItem",
        blank=True,
    )

    def __str__(self):
        return f"{self.supermarket.name} meal deal"


class MealDealSlot(models.Model):
    class SlotType(models.TextChoices):
        MAIN = "MAIN", "Main"
        SIDE = "SIDE", "Side"
        DRINK = "DRINK", "Drink"

    meal_deal = models.ForeignKey(
        MealDeal,
        related_name="slots",
        on_delete=models.CASCADE,
    )
    slot_type = models.CharField(max_length=10, choices=SlotType.choices)
    required = models.BooleanField(default=True)
    min_items = models.PositiveIntegerField(default=1)
    max_items = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["meal_deal", "slot_type"],
                name="unique_meal_deal_slot_type",
            )
        ]

    def __str__(self):
        return f"{self.meal_deal} - {self.slot_type} ({self.min_items}-{self.max_items})"


class MealDealItem(models.Model):
    meal_deal = models.ForeignKey(
        MealDeal,
        related_name="entries",
        on_delete=models.CASCADE,
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    slot = models.ForeignKey(MealDealSlot, on_delete=models.CASCADE, related_name="items")
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["meal_deal", "item", "slot"],
                name="unique_meal_deal_item_slot",
            )
        ]

    def __str__(self):
        return f"{self.meal_deal} - {self.item} ({self.slot})"


class Post(models.Model):
    meal_deal = models.ForeignKey(
        MealDeal,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to="posts/", blank=True, null=True)
    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user} - {self.meal_deal}"


class Preference(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="likes",
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="preference")
    value = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'post', 'value'],
                name='unique_user_post_preference',
            ),
            models.CheckConstraint(
                condition=Q(value__gte=1) & Q(value__lte=2),
                name='value_between_1_and_2'
            ),
            models.CheckConstraint(
                condition=Q(value__gt=0),
                name='value_non_negative'
            )
        ]

    def __str__(self):
        if self.value == 1:
            # 1 for like
            return f"{self.user} likes {self.post}"
        elif self.value == 2:
            # 2 for dislike
            return f"{self.user} dislikes {self.post}"

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField()

    def __str__(self):
        return f"{self.user} - {self.post}"
