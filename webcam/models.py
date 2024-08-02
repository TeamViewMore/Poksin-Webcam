from django.db import models

class CategoryEntity(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'CategoryEntity'

    def __str__(self):
        return self.name

class EvidenceEntity(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified_at = models.DateTimeField(auto_now=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    done = models.BooleanField(default=False)
    fileUrls = models.TextField()
    title = models.CharField(max_length=255, blank=True, null=True)
    category_id = models.ForeignKey(CategoryEntity, on_delete=models.CASCADE, db_column='category_id')
    user_id = models.BigIntegerField()

    class Meta:
        db_table = 'EvidenceEntity'

    def __str__(self):
        return self.title if self.title else f"Evidence {self.id}"
