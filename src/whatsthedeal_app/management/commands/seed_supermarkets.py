from django.core.management.base import BaseCommand

from whatsthedeal_app.models import Supermarket


DEFAULT_SUPERMARKETS = [
    "Tesco",
    "Sainsbury's",
    "Asda",
    "Morrisons",
    "Co-op",
    "Booths",
    "Other",
]


class Command(BaseCommand):
    help = "Create default Supermarket rows (Tesco, Sainsbury's, Asda, Morrisons, Co-op, Booths, Other)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--list",
            action="store_true",
            help="List the supermarkets that would be created without creating them",
        )

    def handle(self, *args, **options):
        if options.get("list"):
            self.stdout.write("Will create the following supermarkets:")
            for name in DEFAULT_SUPERMARKETS:
                self.stdout.write(f" - {name}")
            return

        created = 0
        for name in DEFAULT_SUPERMARKETS:
            _, was_created = Supermarket.objects.get_or_create(name=name)
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"Created: {name}"))
            else:
                self.stdout.write(f"Exists: {name}")

        self.stdout.write(self.style.SUCCESS(f"Done. {created} new supermarkets created."))
