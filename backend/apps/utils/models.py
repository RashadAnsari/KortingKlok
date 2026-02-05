from django.db import models
from django.utils import timezone


class BaseModelManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().order_by("-created_at")


class BaseModelMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = BaseModelManager()

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
