from django.core.management.base import BaseCommand, CommandError

from firebase_admin import messaging

from users.models import UserDevice, UserTopicSecret


class Command(BaseCommand):
    help = "Send a test push notification to a user by their Firebase UID."

    def add_arguments(self, parser):
        parser.add_argument("user_id", type=str, help="Firebase UID of the user")
        parser.add_argument(
            "--title",
            default="Test notification",
            help="Notification title (default: 'Test notification')",
        )
        parser.add_argument(
            "--body",
            default="This is a test notification from KortingKlok.",
            help="Notification body",
        )
        parser.add_argument(
            "--language",
            default=None,
            help="Language code (nl/en). If omitted, sends to all device languages.",
        )

    def handle(self, *args, **options):
        user_id = options["user_id"]
        title = options["title"]
        body = options["body"]
        language = options["language"]

        devices = UserDevice.objects.filter(user_id=user_id)
        if not devices.exists():
            raise CommandError(f"No devices found for user '{user_id}'.")

        if language:
            languages = {language}
        else:
            languages = set(devices.values_list("language", flat=True).distinct()) or {"nl"}

        self.stdout.write(f"Sending test notification to user {user_id} ({', '.join(languages)})...")

        sent = 0
        for lang in languages:
            topic = UserTopicSecret.get_topic_name(user_id, lang)
            message = messaging.Message(
                topic=topic,
                notification=messaging.Notification(title=title, body=body),
                data={"type": "test"},
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(sound="default"),
                    ),
                ),
            )
            try:
                messaging.send(message)
                sent += 1
                self.stdout.write(self.style.SUCCESS(f"  Sent to topic {topic} ({lang})"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"  Failed for {lang}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Done. {sent}/{len(languages)} notification(s) sent."))
