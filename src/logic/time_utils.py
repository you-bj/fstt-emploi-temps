# src/logic/time_utils.py
"""
Time utilities for schedule management.

Provides:
- TimeSlot class for representing time slots
- TimeUtils class with static utility methods for time operations
"""

from datetime import datetime, time, timedelta
from typing import Optional, List, Tuple


class TimeSlot:
    """Represents a time slot with date, start time, and end time."""
    
    def __init__(self, date: str, heure_debut: str, heure_fin: str):
        """
        Initialize a time slot.
        
        Args:
            date: Date string in YYYY-MM-DD format
            heure_debut: Start time in HH:MM format
            heure_fin: End time in HH:MM format
        """
        self.date = date
        self.heure_debut = heure_debut
        self.heure_fin = heure_fin
    
    def __str__(self) -> str:
        return f"{self.date} {self.heure_debut}-{self.heure_fin}"
    
    def __repr__(self) -> str:
        return f"TimeSlot({self.date!r}, {self.heure_debut!r}, {self.heure_fin!r})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, TimeSlot):
            return False
        return (self.date == other.date and 
                self.heure_debut == other.heure_debut and 
                self.heure_fin == other.heure_fin)
    
    def overlaps_with(self, other: 'TimeSlot', min_pause: int = 0) -> bool:
        """
        Check if this time slot overlaps with another, considering a minimum pause.
        
        Args:
            other: Another TimeSlot to check against
            min_pause: Minutes of pause required between sessions (default: 0)
            
        Returns:
            True if slots overlap (or are too close considering the pause)
        """
        if self.date != other.date:
            return False
        
        return TimeUtils.times_overlap(
            self.heure_debut, self.heure_fin,
            other.heure_debut, other.heure_fin,
            min_pause
        )
    
    def contains(self, other: 'TimeSlot') -> bool:
        """Check if this time slot fully contains another time slot."""
        if self.date != other.date:
            return False
        return TimeUtils.time_contains(
            self.heure_debut, self.heure_fin,
            other.heure_debut, other.heure_fin
        )
    
    def get_duration_minutes(self) -> int:
        """Get the duration of this time slot in minutes."""
        return TimeUtils.calculate_duration(self.heure_debut, self.heure_fin)
    
    def get_duration_hours(self) -> float:
        """Get the duration of this time slot in hours."""
        return self.get_duration_minutes() / 60.0
    
    def is_valid(self) -> bool:
        """Check if this time slot has valid times."""
        return TimeUtils.is_valid_time_range(self.heure_debut, self.heure_fin)


class TimeUtils:
    """Static utility methods for time operations."""
    
    @staticmethod
    def parse_time(time_str: str) -> Optional[time]:
        """
        Parse a time string in HH:MM format.
        
        Args:
            time_str: Time string to parse
            
        Returns:
            time object or None if parsing fails
        """
        if not time_str:
            return None
        try:
            parts = time_str.strip().split(':')
            if len(parts) >= 2:
                hour = int(parts[0])
                minute = int(parts[1])
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    return time(hour, minute)
        except (ValueError, AttributeError, TypeError):
            pass
        return None
    
    @staticmethod
    def time_to_minutes(time_str: str) -> Optional[int]:
        """
        Convert a time string to total minutes since midnight.
        
        Args:
            time_str: Time string in HH:MM format
            
        Returns:
            Total minutes or None if parsing fails
        """
        t = TimeUtils.parse_time(time_str)
        if t:
            return t.hour * 60 + t.minute
        return None
    
    @staticmethod
    def minutes_to_time(minutes: int) -> str:
        """
        Convert total minutes since midnight to a time string.
        
        Args:
            minutes: Total minutes since midnight
            
        Returns:
            Time string in HH:MM format
        """
        if minutes < 0:
            minutes = 0
        if minutes >= 24 * 60:
            minutes = 23 * 60 + 59
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"

    @staticmethod
    def times_overlap(start1: str, end1: str, start2: str, end2: str, min_pause: int = 0) -> bool:
        """
        Check if two time ranges overlap, considering a minimum pause.
        
        Logic: Overlap exists if:
        - start1 < (end2 + pause) AND start2 < (end1 + pause)
        
        Args:
            start1, end1: First time range
            start2, end2: Second time range
            min_pause: Minutes of pause to consider between ranges
            
        Returns:
            True if ranges overlap or are too close
        """
        start1_min = TimeUtils.time_to_minutes(start1)
        end1_min = TimeUtils.time_to_minutes(end1)
        start2_min = TimeUtils.time_to_minutes(start2)
        end2_min = TimeUtils.time_to_minutes(end2)
        
        if None in [start1_min, end1_min, start2_min, end2_min]:
            return False
        
        # Add pause to the end of each slot to "expand" the occupied zone
        return start1_min < (end2_min + min_pause) and start2_min < (end1_min + min_pause)

    @staticmethod
    def time_contains(container_start: str, container_end: str, 
                     contained_start: str, contained_end: str) -> bool:
        """
        Check if one time range fully contains another.
        
        Args:
            container_start, container_end: The containing time range
            contained_start, contained_end: The potentially contained time range
            
        Returns:
            True if the contained range is fully within the container
        """
        container_start_min = TimeUtils.time_to_minutes(container_start)
        container_end_min = TimeUtils.time_to_minutes(container_end)
        contained_start_min = TimeUtils.time_to_minutes(contained_start)
        contained_end_min = TimeUtils.time_to_minutes(contained_end)
        
        if None in [container_start_min, container_end_min, contained_start_min, contained_end_min]:
            return False
        return (container_start_min <= contained_start_min and 
                container_end_min >= contained_end_min)

    @staticmethod
    def is_valid_time_range(start: str, end: str) -> bool:
        """
        Check if a time range is valid (start before end).
        
        Args:
            start: Start time in HH:MM format
            end: End time in HH:MM format
            
        Returns:
            True if start is before end
        """
        start_min = TimeUtils.time_to_minutes(start)
        end_min = TimeUtils.time_to_minutes(end)
        if None in [start_min, end_min]:
            return False
        return start_min < end_min

    @staticmethod
    def format_time(time_str: str) -> str:
        """
        Format a time string to ensure HH:MM format with zero-padding.
        
        Args:
            time_str: Time string to format
            
        Returns:
            Formatted time string or original if parsing fails
        """
        t = TimeUtils.parse_time(time_str)
        if t:
            return f"{t.hour:02d}:{t.minute:02d}"
        return time_str

    @staticmethod
    def calculate_duration(start: str, end: str) -> int:
        """
        Calculate the duration in minutes between two times.
        
        Args:
            start: Start time in HH:MM format
            end: End time in HH:MM format
            
        Returns:
            Duration in minutes (0 if invalid)
        """
        start_min = TimeUtils.time_to_minutes(start)
        end_min = TimeUtils.time_to_minutes(end)
        if start_min is not None and end_min is not None:
            return max(0, end_min - start_min)
        return 0
    
    @staticmethod
    def add_minutes(time_str: str, minutes: int) -> str:
        """
        Add minutes to a time string.
        
        Args:
            time_str: Time string in HH:MM format
            minutes: Minutes to add (can be negative)
            
        Returns:
            New time string
        """
        current = TimeUtils.time_to_minutes(time_str)
        if current is None:
            return time_str
        return TimeUtils.minutes_to_time(current + minutes)
    
    @staticmethod
    def get_day_name(date_str: str, lang: str = "fr") -> str:
        """
        Get the day name from a date string.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            lang: Language code ("fr" for French, "en" for English)
            
        Returns:
            Day name or empty string if parsing fails
        """
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            days_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
            days_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            
            day_index = date_obj.weekday()
            if lang == "fr":
                return days_fr[day_index]
            return days_en[day_index]
        except (ValueError, TypeError):
            return ""
    
    @staticmethod
    def is_weekend(date_str: str) -> bool:
        """
        Check if a date is on a weekend (Saturday or Sunday).
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            True if weekend
        """
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.weekday() >= 5
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def get_week_dates(start_date_str: str, num_days: int = 5) -> List[str]:
        """
        Get a list of dates starting from a given date.
        
        Args:
            start_date_str: Start date string in YYYY-MM-DD format
            num_days: Number of days to return (default: 5 for weekdays)
            
        Returns:
            List of date strings
        """
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            return [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") 
                    for i in range(num_days)]
        except (ValueError, TypeError):
            return []
    
    @staticmethod
    def get_next_monday(from_date: datetime = None) -> str:
        """
        Get the date of the next Monday.
        
        Args:
            from_date: Starting date (default: today)
            
        Returns:
            Date string of the next Monday
        """
        if from_date is None:
            from_date = datetime.now()
        
        days_ahead = (7 - from_date.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7  # If today is Monday, get next Monday
        
        next_monday = from_date + timedelta(days=days_ahead)
        return next_monday.strftime("%Y-%m-%d")