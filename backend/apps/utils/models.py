from django.db import models
from django.utils import timezone


class BaseModelMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        db_table = ValueError("You must specify a db_table for this model.")

    def save(self, **kwargs):
        self.updated_at = timezone.now()
        super().save(**kwargs)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.save()
