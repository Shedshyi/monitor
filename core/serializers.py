from rest_framework import serializers
from .models import User, Direction, Criteria, Indicator, TeacherIndicator, Notification

# ✅ Сериализатор для пользователя (учителя и админа)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_admin', 'total_score')

# ✅ Сериализатор для показателей (Indicator)
class IndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Indicator
        fields = ('id', 'criteria', 'title', 'points', 'description')

# ✅ Сериализатор для критериев (Criteria)
class CriteriaSerializer(serializers.ModelSerializer):
    indicators = IndicatorSerializer(many=True, read_only=True, source='indicator_set')

    class Meta:
        model = Criteria
        fields = ('id', 'direction', 'title', 'is_repeatable', 'description', 'indicators')

# ✅ Сериализатор для направлений (Direction)
class DirectionSerializer(serializers.ModelSerializer):
    criteria = CriteriaSerializer(many=True, read_only=True, source='criteria_set')

    class Meta:
        model = Direction
        fields = ('id', 'title', 'description', 'criteria')

# ✅ Сериализатор для связи учитель ↔ показатель
# serializers.py

class TeacherIndicatorSerializer(serializers.ModelSerializer):
    indicator_title = serializers.CharField(source='indicator.title', read_only=True)  # Название показателя
    criteria_title = serializers.CharField(source='indicator.criteria.title', read_only=True)  # Название критерия
    direction_title = serializers.CharField(source='indicator.criteria.direction.title', read_only=True)  # Направление
    points = serializers.IntegerField(source='indicator.points', read_only=True)

    class Meta:
        model = TeacherIndicator
        fields = ['id', 'teacher', 'indicator', 'points', 'indicator_title', 'criteria_title', 'direction_title', 'created_at']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'message', 'is_read', 'created_at']