from django.db import models
from django.contrib.auth.models import AbstractUser

# ✅ Пользовательская модель (Учитель или Админ)
class User(AbstractUser):
    is_admin = models.BooleanField(default=False)  # Роль: Админ или Учитель
    total_score = models.IntegerField(default=0)   # Итоговый балл

    def update_total_score(self):
        # Пересчёт баллов при изменениях
        # total = sum(item.assigned_points for item in self.teacherindicator_set.all())
        # self.total_score = total
        # self.save()
        total = sum(item.indicator.points for item in self.teacherindicator_set.all())
        self.total_score = total
        self.save()

    def __str__(self):
        return self.username

# ✅ Направления научно-методической работы
class Direction(models.Model):
    title = models.CharField(max_length=255, unique=True)    # Название
    description = models.TextField(blank=True, null=True)    # Описание

    def __str__(self):
        return self.title

# ✅ Критерии (внутри направлений)
class Criteria(models.Model):
    direction = models.ForeignKey(Direction, on_delete=models.CASCADE)  # Связь с направлением
    title = models.CharField(max_length=255)                            # Название критерия
    is_repeatable = models.BooleanField(default=False)                  # Можно ли добавлять несколько раз?
    description = models.TextField(blank=True, null=True)               # Описание

    def __str__(self):
        return f"{self.direction.title} → {self.title}"

# ✅ Показатели (с баллами внутри критериев)
class Indicator(models.Model):
    criteria = models.ForeignKey(Criteria, on_delete=models.CASCADE)  # Связь с критерием
    title = models.CharField(max_length=255)                          # Название показателя
    points = models.IntegerField()                                    # Баллы за показатель
    description = models.TextField(blank=True, null=True)             # Описание

    def __str__(self):
        return f"{self.criteria.title} → {self.title} ({self.points} балл(ов))"

# ✅ Связь: Учитель ↔ Показатели
class TeacherIndicator(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)       # Какому учителю принадлежит
    indicator = models.ForeignKey(Indicator, on_delete=models.CASCADE) # Какой показатель
    description = models.TextField(null=True, blank=True)    
    created_at = models.DateTimeField(auto_now_add=True)              # Дата создания

    def save(self, *args, **kwargs):
        # Обновляем баллы при добавлении нового показателя
        super().save(*args, **kwargs)
        self.teacher.update_total_score()

    def __str__(self):
        # return f"{self.teacher.username} → {self.indicator.title} ({self.assigned_points} баллов)"
        return f"{self.teacher.username} - {self.indicator.title}"

class Notification(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Уведомление для {self.teacher.username}"
