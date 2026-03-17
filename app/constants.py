CATEGORY_LABELS = {
    "academic_study_skills": "Academic & Study Skills",
    "career_internships": "Career & Internships",
    "wellness_mental_health": "Wellness & Mental Health",
    "sports_fitness": "Sports & Fitness",
    "arts_culture": "Arts & Culture",
    "community_service_volunteering": "Community Service & Volunteering",
    "entrepreneurship_hackathons": "Entrepreneurship & Hackathons",
    "residential_college_life": "Residential College Life",
    "admin_deadlines": "Admin & Deadlines",
    "social_networking": "Social & Networking",
    "other": "Other",
}

CATEGORY_KEYS = [
    "academic_study_skills",
    "sports_fitness",
    "wellness_mental_health",
    "arts_culture",
    "social_networking",
    "other",
]
CATEGORY_NAME_TO_KEY = {v.lower(): k for k, v in CATEGORY_LABELS.items()}

ALLOWED_RCS = [
    "Tembusu",
    "CAPT",
    "RC4",
    "RVRC",
    "NUSC",
    "Acacia",
    "UTR",
]
ALLOWED_RCS_MAP = {rc.lower(): rc for rc in ALLOWED_RCS}


def category_label(key: str) -> str:
    return CATEGORY_LABELS.get(key, key.replace("_", " ").title())
