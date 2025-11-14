from django.db import models

class BookDemo(models.Model):
    full_name = models.CharField(max_length=100, blank=False, null=False)
    email = models.EmailField()
    company = models.CharField(max_length=150, blank=True, null=True)
    preferred_date = models.DateField()
    description = models.TextField()

    def __str__(self):
        return self.full_name
