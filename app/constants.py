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

CATEGORY_KEYS = list(CATEGORY_LABELS.keys())
CATEGORY_NAME_TO_KEY = {v.lower(): k for k, v in CATEGORY_LABELS.items()}
