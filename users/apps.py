from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'Users'

    def ready(self):
        # Remove this line if it exists, or make sure it's correct
        # import users.signals  # Only uncomment if you have signals
        pass