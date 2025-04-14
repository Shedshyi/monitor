from django.urls import path
from .views import (
    UserListView, DirectionListCreateView, DirectionDetailView,
    CriteriaListCreateView, CriteriaDetailView,
    IndicatorListCreateView, IndicatorDetailView,
    TeacherIndicatorCreateView, TeacherIndicatorListView,
    RecalculateScoresView, NotificationListView,RegisterView, LoginView, MyScoresView, UserDetailView,TopTeachersView,AchievementsListView,FilteredTeachersView,FilteredTeachersByLevelView
)
from .views import TestDirectionView


urlpatterns = [
    path('users/', UserListView.as_view(), name='user-list'),
    path('directions/', DirectionListCreateView.as_view(), name='direction-list'),
    path('directions/<int:pk>/', DirectionDetailView.as_view(), name='direction-detail'),
    path('criteria/', CriteriaListCreateView.as_view(), name='criteria-list'),
    path('criteria/<int:pk>/', CriteriaDetailView.as_view(), name='criteria-detail'),
    path('indicators/', IndicatorListCreateView.as_view(), name='indicator-list'),
    path('indicators/<int:pk>/', IndicatorDetailView.as_view(), name='indicator-detail'),
    path('assign/', TeacherIndicatorCreateView.as_view(), name='assign-indicator'),
    path('my-scores/', TeacherIndicatorListView.as_view(), name='my-scores'),
    path('recalculate/', RecalculateScoresView.as_view(), name='recalculate-scores'),
    path('notifications/', NotificationListView.as_view(), name='notifications'),
    path('test-directions/', TestDirectionView.as_view(), name='test-directions'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('my-scores/', MyScoresView.as_view(), name='my-scores'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('top-teachers/', TopTeachersView.as_view(), name='top-teachers'),
    path('achievements/', AchievementsListView.as_view(), name='achievements-list'),
    path('filter-teachers/', FilteredTeachersView.as_view(), name='filtered-teachers'),
    path('api/filtered-teachers-by-level/', FilteredTeachersByLevelView.as_view(), name='filtered_teachers_by_level'),
]
