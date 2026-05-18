"""
Management command to register all Django Q2 scheduled tasks.
Run once after deployment: python manage.py setup_schedules
"""

from django.core.management.base import BaseCommand

from bookings.tasks import setup_booking_auto_complete_schedule


class Command(BaseCommand):
    help = 'Register scheduled tasks (booking auto-complete, etc.)'

    def handle(self, *args, **options):
        setup_booking_auto_complete_schedule()
        self.stdout.write(self.style.SUCCESS('Scheduled tasks registered.'))
