from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    Item,
    MealDeal,
    MealDealItem,
    MealDealSlot,
    Post,
    Preference,
    Supermarket,
    Comment
)


class PostWorkflowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester",
            password="testpass123",
        )
        self.supermarket = Supermarket.objects.create(name="Booths")

    def _create_post(self, *, description="A tasty deal", user=None, supermarket=None):
        user = user or self.user
        supermarket = supermarket or self.supermarket

        main_item = Item.objects.create(name="Chicken Burger", item_type=Item.ItemType.MAIN)
        side_item = Item.objects.create(name="Fries", item_type=Item.ItemType.SIDE)
        drink_item = Item.objects.create(name="Coke", item_type=Item.ItemType.DRINK)

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
        MealDealItem.objects.create(meal_deal=meal_deal, item=side_item, slot=slots["SIDE"])
        MealDealItem.objects.create(meal_deal=meal_deal, item=drink_item, slot=slots["DRINK"])

        return Post.objects.create(
            meal_deal=meal_deal,
            user=user,
            description=description,
        )

    def test_post_detail_view_displays_the_full_post(self):
        post = self._create_post(description="Full view sample")

        response = self.client.get(reverse("whatsthedeal:post-view", args=[post.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Full view sample")
        self.assertContains(response, self.supermarket.name)
        self.assertEqual(response.context["post"]["post"], post)

    def test_feed_can_be_filtered_by_newest_likes_and_dislikes(self):
        oldest = self._create_post(description="Oldest")
        oldest.created_at = timezone.now() - timedelta(days=2)
        oldest.likes = 1
        oldest.dislikes = 10
        oldest.save(update_fields=["created_at", "likes", "dislikes"])

        middle = self._create_post(description="Middle")
        middle.created_at = timezone.now() - timedelta(days=1)
        middle.likes = 5
        middle.dislikes = 3
        middle.save(update_fields=["created_at", "likes", "dislikes"])

        newest = self._create_post(description="Newest")
        newest.likes = 8
        newest.dislikes = 1
        newest.save(update_fields=["likes", "dislikes"])

        newest_response = self.client.get(reverse("whatsthedeal:post-list"), {"filter": "newest"})
        newest_ids = [entry["post"].id for entry in newest_response.context["feed"]]
        self.assertEqual(newest_ids[:3], [newest.id, middle.id, oldest.id])

        likes_response = self.client.get(reverse("whatsthedeal:post-list"), {"filter": "most-likes"})
        likes_ids = [entry["post"].id for entry in likes_response.context["feed"]]
        self.assertEqual(likes_ids[:3], [newest.id, middle.id, oldest.id])

        dislikes_response = self.client.get(reverse("whatsthedeal:post-list"), {"filter": "most-dislikes"})
        dislikes_ids = [entry["post"].id for entry in dislikes_response.context["feed"]]
        self.assertEqual(dislikes_ids[:3], [oldest.id, middle.id, newest.id])

    def test_liking_can_be_added_removed_and_switched_to_dislike(self):
        self.client.force_login(self.user)
        post = self._create_post()

        self.client.post(
            reverse(
                "whatsthedeal:post-preference",
                kwargs={"postid": post.pk, "userpreference": 1},
            )
        )
        post.refresh_from_db()
        self.assertEqual(post.likes, 1)
        self.assertEqual(post.dislikes, 0)
        self.assertTrue(Preference.objects.filter(user=self.user, post=post, value=1).exists())

        self.client.post(
            reverse(
                "whatsthedeal:post-preference",
                kwargs={"postid": post.pk, "userpreference": 1},
            )
        )
        post.refresh_from_db()
        self.assertEqual(post.likes, 0)
        self.assertFalse(Preference.objects.filter(user=self.user, post=post).exists())

        self.client.post(
            reverse(
                "whatsthedeal:post-preference",
                kwargs={"postid": post.pk, "userpreference": 1},
            )
        )
        self.client.post(
            reverse(
                "whatsthedeal:post-preference",
                kwargs={"postid": post.pk, "userpreference": 2},
            )
        )
        post.refresh_from_db()
        self.assertEqual(post.likes, 0)
        self.assertEqual(post.dislikes, 1)
        self.assertTrue(Preference.objects.filter(user=self.user, post=post, value=2).exists())

    def test_disliking_can_be_added_removed_and_switched_to_like(self):
        self.client.force_login(self.user)
        post = self._create_post()

        self.client.post(
            reverse(
                "whatsthedeal:post-preference",
                kwargs={"postid": post.pk, "userpreference": 2},
            )
        )
        post.refresh_from_db()
        self.assertEqual(post.dislikes, 1)
        self.assertEqual(post.likes, 0)
        self.assertTrue(Preference.objects.filter(user=self.user, post=post, value=2).exists())

        self.client.post(
            reverse(
                "whatsthedeal:post-preference",
                kwargs={"postid": post.pk, "userpreference": 2},
            )
        )
        post.refresh_from_db()
        self.assertEqual(post.dislikes, 0)
        self.assertFalse(Preference.objects.filter(user=self.user, post=post).exists())

        self.client.post(
            reverse(
                "whatsthedeal:post-preference",
                kwargs={"postid": post.pk, "userpreference": 2},
            )
        )
        self.client.post(
            reverse(
                "whatsthedeal:post-preference",
                kwargs={"postid": post.pk, "userpreference": 1},
            )
        )
        post.refresh_from_db()
        self.assertEqual(post.dislikes, 0)
        self.assertEqual(post.likes, 1)
        self.assertTrue(Preference.objects.filter(user=self.user, post=post, value=1).exists())

    def test_feed_shows_posts_for_users(self):
        self._create_post(description="Visible deal")

        response = self.client.get(reverse("whatsthedeal:post-list"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["feed"])
        self.assertIn("Visible deal", [entry["description"] for entry in response.context["feed"]])

    def test_logged_in_user_can_create_a_basic_meal_deal_post(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("whatsthedeal:post-create"),
            {
                "supermarket": self.supermarket.pk,
                "main": "Chicken Burger",
                "side": "Fries",
                "drink": "Coke",
                "description": "A basic meal deal",
            },
        )

        self.assertEqual(response.status_code, 302)
        post = Post.objects.get(description="A basic meal deal")
        self.assertEqual(post.user, self.user)
        self.assertEqual(post.meal_deal.supermarket, self.supermarket)
        self.assertEqual(post.meal_deal.entries.count(), 3)

    def test_guest_user_can_create_a_two_sided_booths_meal_deal_post(self):
        self.client.logout()

        response = self.client.post(
            reverse("whatsthedeal:post-create"),
            {
                "supermarket": self.supermarket.pk,
                "main": "Chicken Burger",
                "side": "Fries",
                "side_2": "Onion Rings",
                "drink": "Coke",
                "description": "Booths double side deal",
            },
        )

        self.assertEqual(response.status_code, 302)
        post = Post.objects.get(description="Booths double side deal")
        self.assertEqual(post.user.username, "anonymous")
        self.assertEqual(post.meal_deal.entries.count(), 4)
        self.assertEqual(post.meal_deal.items.count(), 4)

    def test_guest_user_can_comment(self):
        self.client.logout()
        self._create_post(description="Visible deal")
        post = Post.objects.get(description="Visible deal")

        response = self.client.post(
            reverse("whatsthedeal:post-view", kwargs={'pk': post.id}),
            {
                "comment": "I don't like this meal deal!"
            }
        )

        self.assertEqual(response.status_code, 302)
        comment = Comment.objects.get(content="I don't like this meal deal!")
        self.assertEqual(comment.user.username, "anonymous")

    def test_user_can_comment(self):
        self.client.force_login(self.user)
        self._create_post(description="Visible deal")
        post = Post.objects.get(description="Visible deal")

        response = self.client.post(
            reverse("whatsthedeal:post-view", kwargs={'pk': post.id}),
            {
                "comment": "I don't like this meal deal!"
            }
        )

        self.assertEqual(response.status_code, 302)
        comment = Comment.objects.get(content="I don't like this meal deal!")
        self.assertEqual(comment.user, self.user)


class UserProfileTests(TestCase):
    def test_user_detail_view_uses_username_in_url(self):
        user = get_user_model().objects.create_user(username="profile-user", password="secret123")

        response = self.client.get(reverse("whatsthedeal:user-view", kwargs={"username": user.username}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["profile_user"], user)

    def test_profile_view_does_not_shadow_logged_in_user(self):
        logged_in_user = get_user_model().objects.create_user(username="viewer", password="secret123")
        profile_user = get_user_model().objects.create_user(username="profile-user", password="secret123")
        self.client.force_login(logged_in_user)

        response = self.client.get(reverse("whatsthedeal:user-view", kwargs={"username": profile_user.username}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user"], logged_in_user)
        self.assertEqual(response.context["profile_user"], profile_user)

    def test_user_cannot_view_anonymous_user(self):
        guest_user = get_user_model().objects.create_user(username="anonymous", password="secret123")

        response = self.client.post(
            reverse("whatsthedeal:user-view", kwargs={"username": guest_user.username}),
            {"next": reverse("whatsthedeal:post-list")},
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("whatsthedeal:post-list"))

    def test_user_cannot_view_superuser(self):
        superuser = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="secret123",
        )

        response = self.client.post(
            reverse("whatsthedeal:user-view", kwargs={"username": superuser.username}),
            {"next": reverse("whatsthedeal:post-list")},
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("whatsthedeal:post-list"))


class ModelTests(TestCase):
    def test_supermarket_item_meal_deal_and_slot_models_are_created(self):
        supermarket = Supermarket.objects.create(name="Tesco")
        item = Item.objects.create(name="Chicken Wrap", item_type=Item.ItemType.MAIN)
        meal_deal = MealDeal.objects.create(supermarket=supermarket)
        slot = MealDealSlot.objects.create(
            meal_deal=meal_deal,
            slot_type=MealDealSlot.SlotType.MAIN,
        )
        MealDealItem.objects.create(meal_deal=meal_deal, item=item, slot=slot)

        self.assertEqual(str(supermarket), "Tesco")
        self.assertEqual(str(item), "Chicken Wrap")
        self.assertEqual(str(meal_deal), "Tesco meal deal")
        self.assertEqual(str(slot), f"{meal_deal} - MAIN (1-1)")
        self.assertEqual(meal_deal.entries.count(), 1)

    def test_duplicate_meal_deal_slot_types_are_rejected(self):
        supermarket = Supermarket.objects.create(name="Sainsbury's")
        meal_deal = MealDeal.objects.create(supermarket=supermarket)
        MealDealSlot.objects.create(
            meal_deal=meal_deal,
            slot_type=MealDealSlot.SlotType.MAIN,
        )

        with self.assertRaises(IntegrityError):
            MealDealSlot.objects.create(
                meal_deal=meal_deal,
                slot_type=MealDealSlot.SlotType.MAIN,
            )

    def test_preference_model_represents_likes_and_dislikes(self):
        user = get_user_model().objects.create_user(username="preference-user", password="secret123")
        supermarket = Supermarket.objects.create(name="M&S")
        meal_deal = MealDeal.objects.create(supermarket=supermarket)
        post = Post.objects.create(user=user, meal_deal=meal_deal, description="Preference test")

        like = Preference.objects.create(user=user, post=post, value=1)
        dislike = Preference.objects.create(user=user, post=post, value=2)

        self.assertEqual(str(like), f"{user} likes {post}")
        self.assertEqual(str(dislike), f"{user} dislikes {post}")
