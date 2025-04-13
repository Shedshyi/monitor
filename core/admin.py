from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, Direction, Criteria, Indicator, TeacherIndicator

# Кастомная форма для создания пользователя (с полями password1 и password2)
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

# Кастомная форма для изменения пользователя
class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('username', 'email')

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ('username', 'is_admin', 'total_score')
    list_filter = ('is_admin',)
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Permissions', {'fields': ('is_admin', 'is_active', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_admin', 'is_active')}
        ),
    )
    search_fields = ('username', 'email')
    ordering = ('username',)

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
    list_display = ('teacher', 'indicator', 'points', 'created_at')
    def points(self, obj):
        return obj.indicator.points  # Возвращает баллы из связанной модели Indicator
    points.short_description = 'Баллы'
