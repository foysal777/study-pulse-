from django.db import models


class Policy(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Policies"

    def __str__(self):
        return self.title


class HelpSupport(models.Model):
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Help & Support"
        verbose_name_plural = "Help & Support"

    def __str__(self):
        return f"Support: {self.email}"
