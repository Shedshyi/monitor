from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Direction, Criteria, Indicator, TeacherIndicator, Notification
from .serializers import (UserSerializer, DirectionSerializer, CriteriaSerializer,
                          IndicatorSerializer, TeacherIndicatorSerializer, NotificationSerializer)
from django.db.models import Sum, Q, F

       

# ✅ API для пользователей (только для просмотра)
class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

# ✅ API для направлений (CRUD для админа)
class DirectionListCreateView(generics.ListCreateAPIView):
    queryset = Direction.objects.all()
    serializer_class = DirectionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]  

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

# ✅ API для критериев (CRUD для админа)
class CriteriaListCreateView(generics.ListCreateAPIView):
    queryset = Criteria.objects.all()
    serializer_class = CriteriaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

# ✅ API для показателей (CRUD для админа)
class IndicatorListCreateView(generics.ListCreateAPIView):
    queryset = Indicator.objects.all()
    serializer_class = IndicatorSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

# ✅ API для просмотра баллов учителя
class TeacherIndicatorListView(generics.ListAPIView):
    serializer_class = TeacherIndicatorSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        if self.request.user.is_admin:
            return TeacherIndicator.objects.all()  # Админ видит всё
        return TeacherIndicator.objects.filter(teacher=self.request.user)  # Учитель видит только свои баллы

# ✅ CRUD для направлений (чтение, создание, обновление, удаление)
class DirectionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Direction.objects.all()
    serializer_class = DirectionSerializer
    permission_classes = [AllowAny]

# ✅ CRUD для критериев (чтение, создание, обновление, удаление)
class CriteriaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Criteria.objects.all()
    serializer_class = CriteriaSerializer
    permission_classes = [AllowAny]

# ✅ Вручную пересчитать баллы
class RecalculateScoresView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        for user in User.objects.all():
            user.update_total_score()
        return Response({"message": "Баллы пересчитаны!"})

# ✅ Множественное добавление индикаторов
class TeacherIndicatorCreateView(generics.GenericAPIView):
    serializer_class = TeacherIndicatorSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        teacher_id = request.data.get('teacher')
        indicator_ids = request.data.get('indicators', [])

        if not teacher_id or not indicator_ids:
            return Response({'error': 'Нужно указать teacher и список indicators.'}, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем, существует ли учитель
        try:
            teacher = User.objects.get(id=teacher_id)
        except User.DoesNotExist:
            return Response({'error': 'Учитель не найден.'}, status=status.HTTP_404_NOT_FOUND)

        notifications = []

        # Обработка каждого индикатора
        for indicator_id in indicator_ids:
            try:
                indicator = Indicator.objects.get(id=indicator_id)

                # Проверка: если критерий не повторяемый и уже добавлен — пропускаем
                if not indicator.criteria.is_repeatable:
                    if TeacherIndicator.objects.filter(teacher=teacher, indicator__criteria=indicator.criteria).exists():
                        continue

                # Создание связи учитель ↔ показатель
                TeacherIndicator.objects.create(
                    teacher=teacher,
                    indicator=indicator,
                    # assigned_points=indicator.points
                )

                # Создаём уведомление
                notifications.append(Notification(
                    teacher=teacher,
                    message=f"Вам добавлен новый показатель: {indicator.title} ({indicator.points} баллов)."
                ))

            except Indicator.DoesNotExist:
                return Response({'error': f'Показатель с ID {indicator_id} не найден.'},
                                status=status.HTTP_404_NOT_FOUND)

        # Создаём все уведомления за раз
        Notification.objects.bulk_create(notifications)

        # Обновляем баллы учителя
        teacher.update_total_score()

        return Response({'message': 'Показатели успешно добавлены!'}, status=status.HTTP_201_CREATED)


# ✅ Уведомление при изменении баллов
# class IndicatorDetailView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Indicator.objects.all()
#     serializer_class = IndicatorSerializer
#     permission_classes = [AllowAny]

#     def perform_update(self, serializer):
#         instance = serializer.save()

#         # Пересчитываем баллы у всех, кто имеет этот показатель
#         for item in TeacherIndicator.objects.filter(indicator=instance):
#             item.assigned_points = instance.points
#             item.save(update_fields=['assigned_points'])
#             item.teacher.update_total_score()

#             # Уведомляем учителей об изменении
#             Notification.objects.create(
#                 teacher=item.teacher,
#                 message=f"Ваш показатель '{instance.title}' изменён. Новые баллы: {instance.points}."
#             )
from django.db import transaction

class IndicatorDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Indicator.objects.all()
    serializer_class = IndicatorSerializer
    permission_classes = [AllowAny]

    def perform_update(self, serializer):
        old_instance = self.get_object()
        old_points = old_instance.points  # Старое значение баллов
        instance = serializer.save()  # Сохраняем обновлённый объект

        if old_points != instance.points:
            # Используем транзакцию для атомарных операций
            with transaction.atomic():
                # Получаем все связанные TeacherIndicator
                teacher_indicators = TeacherIndicator.objects.filter(indicator=instance)

                for item in teacher_indicators:
                    item.points = instance.points  # Обновляем баллы в TeacherIndicator
                TeacherIndicator.objects.bulk_update(teacher_indicators, ['points'])  # Пакетное обновление

                # Пересчитываем общий счёт всех преподавателей
                for item in teacher_indicators:
                    item.teacher.update_total_score()

                    # Создаём уведомление для преподавателя
                    Notification.objects.create(
                        teacher=item.teacher,
                        message=f"Ваш показатель '{instance.title}' был обновлён. Новые баллы: {instance.points}."
                    )

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Notification.objects.filter(teacher=self.request.user, is_read=False)

class TestDirectionView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        directions = Direction.objects.all()
        serializer = DirectionSerializer(directions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')

        if not username or not password or not email:
            return Response({'error': 'Все поля обязательны'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Пользователь с таким именем уже существует'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, password=password, email=email)
        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Пользователь успешно зарегистрирован',
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'error': 'Введите имя пользователя и пароль'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=username, password=password)

        if not user:
            return Response({'error': 'Неверные учетные данные'}, status=status.HTTP_401_UNAUTHORIZED)

        # Генерация токенов
        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Успешный вход',
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_staff
            }
        })

class MyScoresView(generics.ListAPIView):
    serializer_class = TeacherIndicatorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TeacherIndicator.objects.filter(teacher=self.request.user)

# ✅ API для просмотра профиля конкретного пользователя
class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        user = self.get_object()
        
        # Получаем все показатели (индикаторы) пользователя
        indicators = TeacherIndicator.objects.filter(teacher=user)
        indicator_data = TeacherIndicatorSerializer(indicators, many=True).data

        return Response({
            'user': UserSerializer(user).data,
            'indicators': indicator_data,
            'total_score': user.total_score,
        })

class TopTeachersView(generics.ListAPIView):
    queryset = User.objects.filter(is_admin=False).order_by('-total_score')[:10]
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


# ✅ Эндпоинт для получения всех достижений (направления → критерии → показатели)
class AchievementsListView(generics.ListAPIView):
    queryset = Direction.objects.prefetch_related('criteria_set__indicator_set').all()
    serializer_class = DirectionSerializer
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        directions = self.get_queryset()
        data = self.get_serializer(directions, many=True).data
        return Response(data)

from django.db.models import Sum, Q
from rest_framework import generics
from .serializers import UserSerializer
from .models import User

# class FilteredTeachersView(generics.ListAPIView):
#     serializer_class = UserSerializer

#     def get_queryset(self):
#         # Получаем параметры из запроса
#         direction_id = self.request.query_params.get('direction_id')
#         criteria_id = self.request.query_params.get('criteria_id')
#         indicator_id = self.request.query_params.get('indicator_id')
#         points = self.request.query_params.get('points')

#         # Основной queryset, без агрегации
#         queryset = User.objects.all()

#         # Фильтрация по переданным параметрам
#         filters = Q()
#         if direction_id:
#             filters &= Q(teacherindicator__indicator__criteria__direction_id=direction_id)
#         if criteria_id:
#             filters &= Q(teacherindicator__indicator__criteria_id=criteria_id)
#         if indicator_id:
#             filters &= Q(teacherindicator__indicator_id=indicator_id)
#         if points:
#             # Если у вас есть поле для баллов, используйте его для фильтрации
#             filters &= Q(teacherindicator__some_other_field=points)  # Здесь подставьте правильное поле

#         # Применяем фильтрацию
#         queryset = queryset.filter(filters).distinct()

#         # Если нужно, добавьте другие поля для агрегации
#         # Например, если нужно агрегировать по какому-то другому полю
#         # queryset = queryset.annotate(total_points=Sum('teacherindicator__some_other_field')).order_by('-total_points')

#         return queryset 
class FilteredTeachersView(generics.ListAPIView):
    serializer_class = UserSerializer

    def get_queryset(self):
        # Получаем параметры из запроса
        direction_id = self.request.query_params.get('direction_id')
        criteria_id = self.request.query_params.get('criteria_id')
        indicator_id = self.request.query_params.get('indicator_id')
        points = self.request.query_params.get('points')

        # Основной queryset, без агрегации
        queryset = User.objects.all()

        # Фильтрация по переданным параметрам
        filters = Q()
        if direction_id:
            filters &= Q(teacherindicator__indicator__criteria__direction_id=direction_id)
        if criteria_id:
            filters &= Q(teacherindicator__indicator__criteria_id=criteria_id)
        if indicator_id:
            filters &= Q(teacherindicator__indicator_id=indicator_id)
        if points:
            filters &= Q(teacherindicator__points=points)  # Здесь подставьте правильное поле для баллов

        # Применяем фильтрацию
        queryset = queryset.filter(filters).distinct()

        # Подсчитываем баллы за показатели, критерии и направления
        queryset = queryset.annotate(
            indicator_score=Sum('teacherindicator__points'),  # Суммируем баллы за показатели
            criteria_score=Sum('teacherindicator__indicator__criteria__points'),  # Суммируем баллы по критериям
            direction_score=Sum('teacherindicator__indicator__criteria__direction__points')  # Суммируем баллы по направлениям
        )

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        # Применяем сериализацию данных
        serializer = self.get_serializer(queryset, many=True)

        # Обрабатываем данные перед отправкой
        for user in serializer.data:
            # Здесь можно добавить логику, если нужно преобразовать или обработать данные
            user['total_score'] = user['indicator_score']  # Пример, если все баллы суммируются в общий балл

        return Response(serializer.data)