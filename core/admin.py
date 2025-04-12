from django.contrib import admin
from .models import User, Direction, Criteria, Indicator, TeacherIndicator

# ✅ Настройка отображения в админке
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'is_admin', 'total_score')
    list_filter = ('is_admin',)

@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'description')

@admin.register(Criteria)
class CriteriaAdmin(admin.ModelAdmin):
    list_display = ('title', 'direction', 'is_repeatable', 'description')

@admin.register(Indicator)
class IndicatorAdmin(admin.ModelAdmin):
    list_display = ('title', 'criteria', 'points', 'description')

@admin.register(TeacherIndicator)
class TeacherIndicatorAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'indicator', 'points', 'created_at')  # убери assigned_points и добавь points

    def points(self, obj):
        return obj.indicator.points  # возвращаем баллы из связанной модели

    points.short_description = 'Баллы'  # читаемое название в админке
