from django.apps import AppConfig

class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        import os

        # ⚠️ duplicate run avoid
        if os.environ.get('RUN_MAIN') != 'true':
            return

        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()

            # 🔥 admin reset
            User.objects.filter(username="admin").delete()

            User.objects.create_superuser("admin", "admin@gmail.com", "admin123")

            print("Superuser reset done")

        except Exception as e:
            print(e)
