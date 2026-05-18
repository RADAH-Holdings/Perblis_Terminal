"""
Scheduled tasks for the bookings module.

Auto-completion: bookings past their end_date with status 'active' are
automatically transitioned to 'completed'. Per FSD §9.5.2:
"End date passes with no cancellation → Rental period concluded successfully."

This task is scheduled to run daily via Django Q2.
"""

from datetime import date

from .models import Booking, BookingStatus


def complete_expired_bookings():
    """
    Transition all active bookings whose end_date has passed to 'completed'.
    Also transitions confirmed (paid) bookings past their end_date.

    Returns a summary dict for logging/admin visibility.
    """
    today = date.today()

    expired_bookings = Booking.objects.filter(
        status__in=[BookingStatus.ACTIVE, BookingStatus.CONFIRMED],
        end_date__lt=today,
    )

    count = expired_bookings.count()
    if count > 0:
        expired_bookings.update(status=BookingStatus.COMPLETED)

    print(f"[BOOKING AUTO-COMPLETE] {count} booking(s) marked as completed (end_date < {today})")
    return {'completed_count': count, 'date': str(today)}


def setup_booking_auto_complete_schedule():
    """
    Register the auto-complete task to run daily at 1:00 AM (Africa/Lagos).
    Idempotent — will not create duplicate schedules.
    """
    from django_q.models import Schedule

    schedule_name = 'booking_auto_complete_daily'

    if not Schedule.objects.filter(name=schedule_name).exists():
        Schedule.objects.create(
            name=schedule_name,
            func='bookings.tasks.complete_expired_bookings',
            schedule_type=Schedule.DAILY,
            minutes=60,
            repeats=-1,
        )
        print(f"[SCHEDULER] Created schedule: {schedule_name}")
    else:
        print(f"[SCHEDULER] Schedule already exists: {schedule_name}")
