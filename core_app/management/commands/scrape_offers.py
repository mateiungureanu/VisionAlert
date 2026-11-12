import logging

from django.core.management.base import BaseCommand, CommandError

from core_app.scraping.pipeline import run_pipeline
from core_app.scraping.scrapers.cinemacity import LMStudioUnavailableError


class Command(BaseCommand):
    help = "Ruleaza manual scraping-ul de oferte"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email-backend",
            choices=("console", "configured"),
            default="console",
            help=(
                "Email delivery backend: print messages in this console by default, "
                "or use EMAIL_BACKEND from settings with 'configured'."
            ),
        )

    def handle(self, *args, **options):
        logger = logging.getLogger("core_app.scraping")
        handler = logging.StreamHandler(self.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%H:%M:%S")
        )
        previous_level = logger.level
        previous_propagate = logger.propagate
        logger.setLevel(logging.INFO)
        logger.propagate = False
        logger.addHandler(handler)

        try:
            try:
                email_backend = (
                    "django.core.mail.backends.console.EmailBackend"
                    if options["email_backend"] == "console"
                    else None
                )
                summary = run_pipeline(email_backend=email_backend)
            except LMStudioUnavailableError as error:
                raise CommandError(str(error)) from error
        finally:
            logger.removeHandler(handler)
            handler.close()
            logger.setLevel(previous_level)
            logger.propagate = previous_propagate

        self.stdout.write(self.style.SUCCESS(str(summary)))