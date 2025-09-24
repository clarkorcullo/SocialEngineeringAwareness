"""
Central mapping of lesson keys to YouTube VIDEO_IDs for embeds.
Update as you add more videos.
"""

VIDEO_IDS = {
    # Module 1
    "module1_lesson_1_1_a": "G6GBRIRmsAg",
    "module1_lesson_1_2_a": "QGGkMDP69jM",
    "module1_lesson_1_2_b": "weeRmfND82E",

    # Module 2
    "module2_lesson_2_1_a": "sD8quANkXZk",
    "module2_lesson_2_2_a": "N1z1u_y6bEA",
}

from typing import Optional

def get_video_id(key: str) -> Optional[str]:
    return VIDEO_IDS.get(key)


