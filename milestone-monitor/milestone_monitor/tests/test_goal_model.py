from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from milestone_monitor.models import User, Goal, Importance, Frequency
from milestone_monitor.tasks import send_final_task_message
from datetime import timedelta, datetime
from django_celery_beat.models import PeriodicTask
from django.core.exceptions import ObjectDoesNotExist

class NoRemindersGoalTest(TestCase):
  @classmethod
  def setUpTestData(cls):
    cls.user = User.objects.create(name='Test User', phone_number=1234567890)
    cls.end_at = timezone.now() + timezone.timedelta(days=1)
    mocked_task = MagicMock()
    mocked_task.id = '1'
    with patch('milestone_monitor.tasks.send_final_task_message.apply_async', return_value=mocked_task) as cls.mock_create_final_task:
      cls.goal = Goal.objects.create(
        user=cls.user,
        title='Test Goal',
        description='Testing Goal Creation',
        importance=Importance.HIGH,
        end_at=cls.end_at
      )
      cls.mock_create_final_task.assert_called_once_with(
        args=[cls.user.phone_number, 'Test Goal'], eta=cls.end_at
      )

  def test_goal_creation(self):
    self.assertIsInstance(self.goal, Goal)
    self.assertEqual(self.goal.user, self.user)
    self.assertEqual(self.goal.title, 'Test Goal')
    self.assertEqual(self.goal.description, 'Testing Goal Creation')
    self.assertEqual(self.goal.importance, Importance.HIGH)

  def test_goal_reminders_validation(self):
    self.assertIsNotNone(self.goal.end_at)
    self.assertFalse(self.goal.reminders_enabled)
    self.assertIsNone(self.goal.reminder_start_time)
    self.assertIsNone(self.goal.reminder_frequency)
    self.assertIsNone(self.goal.reminder_task)
    self.assertTrue(self.goal.final_task_enabled)
    self.assertIsNotNone(self.goal.final_task_id)
  
  def test_move_reminder_expiration(self):
    end_at = timezone.now() + timezone.timedelta(days=2)
    mocked_task = MagicMock()
    mocked_task.id = '1'

    with patch('milestone_monitor.tasks.send_final_task_message.apply_async', return_value=mocked_task) as mock_create_final_task:
      self.goal.modify({'end_at': end_at})
      mock_create_final_task.assert_called_once_with(
        args=[self.user.phone_number, 'Test Goal'], eta=end_at
      )
      
    self.assertIsNotNone(self.goal.end_at)
    self.assertFalse(self.goal.reminders_enabled)
    self.assertIsNone(self.goal.reminder_start_time)
    self.assertIsNone(self.goal.reminder_frequency)
    self.assertIsNone(self.goal.reminder_task)
    self.assertTrue(self.goal.final_task_enabled)
    self.assertIsNotNone(self.goal.final_task_id)

  def test_goal_modify_no_reminder_changes(self):
    self.goal.modify({'importance': Importance.LOW, 'description': 'Testing Goal Creation 2'})
    self.assertEqual(self.goal.importance, Importance.LOW)
    self.assertEqual(self.goal.description, 'Testing Goal Creation 2')
  
  def test_goal_add_recurring_reminders(self):
    self.goal.modify({'reminders_enabled': True, 'reminder_start_time': timezone.make_aware(datetime.now() + timezone.timedelta(minutes=5)), 'reminder_frequency': Frequency.DAILY})
    self.assertTrue(self.goal.reminders_enabled)
    self.assertIsNotNone(self.goal.reminder_start_time)
    self.assertEqual(self.goal.reminder_frequency, Frequency.DAILY)
    self.assertIsNotNone(self.goal.reminder_task)
    self.assertEqual(PeriodicTask.objects.get(name=self.goal.id).interval.every, 1)
    self.assertEqual(PeriodicTask.objects.get(name=self.goal.id).interval.period, 'days')
  
  def test_goal_disable_final_task(self):
    with patch('backend.celery.app.control.revoke') as mock_revoke:
      self.goal.modify({'final_task_enabled': False})
      mock_revoke.assert_called_once()
    self.assertFalse(self.goal.final_task_enabled)
    self.assertIsNone(self.goal.final_task_id)

  def test_goal_completion(self):
    self.goal.modify({'completed': True})
    self.assertTrue(self.goal.completed)
    self.assertIsNone(self.goal.reminder_task)
    self.assertFalse(self.goal.reminders_enabled)
    self.assertFalse(self.goal.final_task_enabled)

class GoalWithRemindersTest(TestCase):
  @classmethod
  def setUpTestData(cls):
    cls.user = User.objects.create(name='Test User', phone_number=1234567890)
    cls.end_at = timezone.now() + timezone.timedelta(days=1)
    mocked_task = MagicMock()
    mocked_task.id = '1'
    with patch('milestone_monitor.tasks.send_final_task_message.apply_async', return_value=mocked_task) as cls.mock_create_final_task:
      cls.goal = Goal.objects.create(
        user=cls.user,
        title='Test Goal',
        description='Testing Goal Creation',
        importance=Importance.HIGH,
        end_at=cls.end_at,
        reminder_start_time=timezone.now(),
        reminder_frequency=Frequency.DAILY
      )
      cls.mock_create_final_task.assert_called_once_with(
        args=[cls.user.phone_number, 'Test Goal'], eta=cls.end_at
      )
  
  def test_goal_creation(self):
    self.assertIsInstance(self.goal, Goal)
    self.assertEqual(self.goal.user, self.user)
    self.assertEqual(self.goal.title, 'Test Goal')
    self.assertEqual(self.goal.description, 'Testing Goal Creation')
    self.assertEqual(self.goal.importance, Importance.HIGH)
  
  def test_goal_reminders_validation(self):
    self.assertIsNotNone(self.goal.end_at)
    self.assertTrue(self.goal.reminders_enabled)
    self.assertIsNotNone(self.goal.reminder_start_time)
    self.assertEqual(self.goal.reminder_frequency, Frequency.DAILY)
    self.assertIsNotNone(self.goal.reminder_task)
    self.assertTrue(self.goal.final_task_enabled)
    self.assertIsNotNone(self.goal.final_task_id)
    self.assertIsNotNone(PeriodicTask.objects.get(name=self.goal.id))

  def test_goal_modify_reminder_frequency(self):
    with patch('backend.celery.app.control.revoke') as mock_revoke:
      self.goal.modify({'reminder_frequency': Frequency.WEEKLY})
      mock_revoke.assert_not_called()
    self.assertEqual(self.goal.reminder_frequency, Frequency.WEEKLY)
    self.assertIsNotNone(PeriodicTask.objects.get(name=self.goal.id))
    self.assertEqual(PeriodicTask.objects.get(name=self.goal.id).interval.every, 7)
    self.assertEqual(PeriodicTask.objects.get(name=self.goal.id).interval.period, 'days')
  
  def test_goal_modify_no_reminder_changes(self):
    self.goal.modify({'importance': Importance.LOW, 'description': 'Testing Goal Creation 2'})
    self.assertEqual(self.goal.importance, Importance.LOW)
    self.assertEqual(self.goal.description, 'Testing Goal Creation 2')
  
  def test_goal_modify_remove_recurring_reminders(self):
    with patch('backend.celery.app.control.revoke') as mock_revoke:
      self.goal.modify({'reminders_enabled': False})
      mock_revoke.assert_not_called()
    self.assertFalse(self.goal.reminders_enabled)
    self.assertIsNone(self.goal.reminder_start_time)
    self.assertIsNone(self.goal.reminder_task)
    with self.assertRaises(ObjectDoesNotExist):
      PeriodicTask.objects.get(name=self.goal.id)
  
  def test_goal_remove_final_task(self):
    with patch('backend.celery.app.control.revoke') as mock_revoke:
      self.goal.modify({'final_task_enabled': False})
      mock_revoke.assert_called_once()
    self.assertFalse(self.goal.final_task_enabled)
    self.assertIsNone(self.goal.final_task_id)
  
  def test_goal_remove_reminder_expiration(self):
    with patch('backend.celery.app.control.revoke') as mock_revoke:
      self.goal.modify({'end_at': None})
      mock_revoke.assert_called_once()
    self.assertIsNone(self.goal.end_at)
    self.assertTrue(self.goal.reminders_enabled)
    self.assertIsNotNone(self.goal.reminder_start_time)
    self.assertIsNotNone(self.goal.reminder_frequency)
    self.assertIsNotNone(self.goal.reminder_task)
    self.assertFalse(self.goal.final_task_enabled)
    self.assertIsNone(self.goal.final_task_id)
    self.assertEqual(PeriodicTask.objects.get(name=self.goal.id).interval.every, 1)
    self.assertEqual(PeriodicTask.objects.get(name=self.goal.id).interval.period, 'days')
    self.assertIsNone(PeriodicTask.objects.get(name=self.goal.id).expires)
  
  def test_move_reminder_expiration(self):
    end_at = timezone.now() + timezone.timedelta(days=2)
    mocked_task = MagicMock()
    mocked_task.id = '1'

    with patch('milestone_monitor.tasks.send_final_task_message.apply_async', return_value=mocked_task) as mock_create_final_task:
      self.goal.modify({'end_at': end_at})
      mock_create_final_task.assert_called_once_with(
        args=[self.user.phone_number, 'Test Goal'], eta=end_at
      )
      
    self.assertIsNotNone(self.goal.end_at)
    self.assertTrue(self.goal.reminders_enabled)
    self.assertIsNotNone(self.goal.reminder_start_time)
    self.assertIsNotNone(self.goal.reminder_frequency)
    self.assertIsNotNone(self.goal.reminder_task)
    self.assertTrue(self.goal.final_task_enabled)
    self.assertIsNotNone(self.goal.final_task_id)
    self.assertEqual(PeriodicTask.objects.get(name=self.goal.id).interval.every, 1)
    self.assertEqual(PeriodicTask.objects.get(name=self.goal.id).interval.period, 'days')
    self.assertIsNotNone(PeriodicTask.objects.get(name=self.goal.id).expires)
  
  def test_goal_disable_reminders_and_final_task(self):
    with patch('backend.celery.app.control.revoke') as mock_revoke:
      self.goal.modify({'reminders_enabled': False, 'final_task_enabled': False})
      mock_revoke.assert_called_once()
    self.assertFalse(self.goal.reminders_enabled)
    self.assertIsNone(self.goal.reminder_start_time)
    self.assertIsNone(self.goal.reminder_task)
    self.assertFalse(self.goal.final_task_enabled)
    self.assertIsNone(self.goal.final_task_id)
    with self.assertRaises(ObjectDoesNotExist):
      PeriodicTask.objects.get(name=self.goal.id)
  
  def test_goal_completion(self):
    self.goal.modify({'completed': True})
    self.assertTrue(self.goal.completed)
    self.assertIsNone(self.goal.reminder_task)
    self.assertFalse(self.goal.reminders_enabled)
    self.assertFalse(self.goal.final_task_enabled)
    with self.assertRaises(ObjectDoesNotExist):
      PeriodicTask.objects.get(name=self.goal.id)
    
class InvalidGoalTest(TestCase):
  @classmethod
  def setUpTestData(cls):
    cls.user = User.objects.create(name='Test User', phone_number=1234567890)
    cls.goal = Goal.objects.create(
      user=cls.user,
      title='Test Invalid Goal',
      description='Testing Goal Creation',
      importance=Importance.HIGH,
      end_at=timezone.now() - timezone.timedelta(days=1),
      reminder_start_time=timezone.now(),
      reminder_frequency=Frequency.DAILY
    )
  
  def test_goal_creation(self):
    self.assertIsInstance(self.goal, Goal)
    self.assertEqual(self.goal.user, self.user)
    self.assertEqual(self.goal.title, 'Test Invalid Goal')
    self.assertEqual(self.goal.description, 'Testing Goal Creation')
    self.assertEqual(self.goal.importance, Importance.HIGH)
  
  def test_no_final_task_set(self):
    self.assertFalse(self.goal.final_task_enabled)
    self.assertIsNone(self.goal.final_task_id)
  
  def test_no_reminders_set(self):
    self.assertFalse(self.goal.reminders_enabled)
    self.assertIsNone(self.goal.reminder_task)