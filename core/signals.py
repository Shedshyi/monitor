from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from .models import Indicator, TeacherIndicator, Notification


@receiver(post_save, sender=Indicator)
def update_teacher_indicators_on_indicator_change(sender, instance, **kwargs):
    teacher_indicators = TeacherIndicator.objects.filter(indicator=instance)

    for item in teacher_indicators:
        item.save()  # Триггерим сохранение и, возможно, update
        item.teacher.update_total_score()

        Notification.objects.create(
            teacher=item.teacher,
            message=f"Ваш показатель '{instance.title}' был обновлён. Новые баллы: {instance.points}."
        )


@receiver(pre_delete, sender=Indicator)
def on_indicator_delete(sender, instance, **kwargs):
    teacher_indicators = TeacherIndicator.objects.filter(indicator=instance)
    affected_teachers = set(item.teacher for item in teacher_indicators)

    # Если FK уже настроен на CASCADE, то удаление происходит автоматически

    for teacher in affected_teachers:
        teacher.update_total_score()


@receiver(post_save, sender=TeacherIndicator)
def on_teacherindicator_create_or_update(sender, instance, **kwargs):
    instance.teacher.update_total_score()


@receiver(post_delete, sender=TeacherIndicator)
def on_teacherindicator_delete(sender, instance, **kwargs):
    instance.teacher.update_total_score()
