from django.core.management.base import BaseCommand, CommandError

from core_app.scraping.health import check_resources


class Command(BaseCommand):
    help = "Check enabled website and API resources and notify staff on status changes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--timeout",
            type=int,
            default=10,
            help="HTTP timeout in seconds (1-60; default: 10).",
        )

    def handle(self, *args, **options):
        timeout = options["timeout"]
        if not 1 <= timeout <= 60:
            raise CommandError("--timeout must be between 1 and 60 seconds.")

        summary = check_resources(timeout=timeout)
        result = (
            f"Checked {summary.checked} resources: {summary.healthy} healthy, "
            f"{summary.failing} failing."
        )
        style = self.style.WARNING if summary.failing else self.style.SUCCESS
        self.stdout.write(style(result))
