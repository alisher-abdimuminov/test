from django.core.exceptions import ValidationError
from django.db import models


class Speciality(models.Model):
    name = models.CharField("Nomi", max_length=150, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Mutaxassislik"
        verbose_name_plural = "Mutaxassisliklar"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ForeignLanguage(models.Model):
    name = models.CharField("Nomi", max_length=100, unique=True)
    code = models.CharField("Kod", max_length=10, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Xorijiy til"
        verbose_name_plural = "Xorijiy tillar"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Question(models.Model):
    class Category(models.TextChoices):
        SPECIALITY = "speciality", "Mutaxassislik"
        PEDAGOGY = "pedagogy", "Pedagogika"
        IT = "it", "IT"
        FOREIGN_LANGUAGE = "foreign_language", "Xorijiy til"

    text = models.TextField("Savol")
    image = models.ImageField(
        "Savol rasmi", upload_to="questions/", blank=True, null=True
    )
    category = models.CharField("Kategoriya", max_length=30, choices=Category.choices)
    speciality = models.ForeignKey(
        Speciality,
        verbose_name="Mutaxassislik",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="questions",
    )
    foreign_language = models.ForeignKey(
        ForeignLanguage,
        verbose_name="Xorijiy til",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="questions",
    )
    is_active = models.BooleanField("Faol", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Savol"
        verbose_name_plural = "Savollar"
        indexes = [
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["category", "speciality", "is_active"]),
            models.Index(fields=["category", "foreign_language", "is_active"]),
        ]

    def clean(self):
        errors = {}
        if self.category == self.Category.SPECIALITY and not self.speciality_id:
            errors["speciality"] = (
                "Mutaxassislik kategoriyasi uchun mutaxassislik tanlang."
            )
        if self.category != self.Category.SPECIALITY and self.speciality_id:
            errors["speciality"] = (
                "Bu kategoriya uchun mutaxassislik bo‘sh bo‘lishi kerak."
            )
        if (
            self.category == self.Category.FOREIGN_LANGUAGE
            and not self.foreign_language_id
        ):
            errors["foreign_language"] = "Xorijiy til kategoriyasi uchun til tanlang."
        if self.category != self.Category.FOREIGN_LANGUAGE and self.foreign_language_id:
            errors["foreign_language"] = (
                "Bu kategoriya uchun xorijiy til bo‘sh bo‘lishi kerak."
            )
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.text[:80]


class Choice(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="choices"
    )
    text = models.TextField("Javob matni", blank=True)
    image = models.ImageField(
        "Javob rasmi", upload_to="choices/", blank=True, null=True
    )
    is_correct = models.BooleanField("To‘g‘ri javob", default=False)

    class Meta:
        verbose_name = "Javob varianti"
        verbose_name_plural = "Javob variantlari"

    def clean(self):
        if not self.text.strip() and not self.image:
            raise ValidationError("Javobda matn yoki rasm bo‘lishi kerak.")

    def __str__(self):
        return self.text[:60] or f"Rasmli javob #{self.pk}"
