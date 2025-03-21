# core/utils.py

def format_duration(minutes):
    """
    Format duration in minutes to a human-readable string.
    
    Args:
        minutes (int): Duration in minutes
        
    Returns:
        str: Formatted duration string (e.g., "2h 30m")
    """
    if minutes < 60:
        return f"{minutes}m"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if remaining_minutes == 0:
        return f"{hours}h"
    
    return f"{hours}h {remaining_minutes}m"


def get_status_color(status):
    """
    Returns the appropriate color class for a given status.
    
    Args:
        status (str): Status string ('active', 'paused', 'completed')
        
    Returns:
        dict: Dictionary containing text and background color classes
    """
    colors = {
        'active': {
            'bg': 'bg-green-100',
            'text': 'text-green-800'
        },
        'paused': {
            'bg': 'bg-yellow-100',
            'text': 'text-yellow-800'
        },
        'completed': {
            'bg': 'bg-blue-100',
            'text': 'text-blue-800'
        }
    }
    
    return colors.get(status, {
        'bg': 'bg-gray-100',
        'text': 'text-gray-800'
    })
