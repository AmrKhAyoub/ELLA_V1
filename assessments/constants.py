# assessments/constants.py

# Extracted from assesment.py
ACADEMIC_QUESTIONS = [
    # Beginner Level (A1 - A2)
    {
        "id": 1,
        "level": "A1",
        "question": "She __________ to the gym every day.",
        "options": ["go", "goes", "going", "gone"],
        "correct": 2,
        "explanation": "We use the Present Simple with singular subjects (She/He/It) by adding 's' or 'es' to the verb.",
    },
    {
        "id": 2,
        "level": "A1",
        "question": "I want to buy some fresh bread. Let's go to the __________.",
        "options": ["library", "bakery", "pharmacy", "museum"],
        "correct": 2,
        "explanation": "A 'bakery' is a place where fresh bread and baked goods are made and sold.",
    },
    {
        "id": 3,
        "level": "A2",
        "question": "We __________ a movie when suddenly the power went out.",
        "options": ["watch", "were watching", "watched", "have watched"],
        "correct": 2,
        "explanation": "We use the Past Continuous (was/were + v-ing) for an ongoing action that was interrupted by another event in the Past Simple.",
    },
    {
        "id": 4,
        "level": "A2",
        "question": "He is very __________. He always shares his things and helps everyone.",
        "options": ["selfish", "generous", "lazy", "stubborn"],
        "correct": 2,
        "explanation": "'Generous' means willing to give money, help, or kindness freely.",
    },
    # Intermediate Level (B1 - B2)
    {
        "id": 5,
        "level": "B1",
        "question": "If I had known about the traffic jam, I __________ earlier.",
        "options": ["would leave", "will leave", "would have left", "had left"],
        "correct": 3,
        "explanation": "This is a Third Conditional sentence expressing regret about the past: If + Past Perfect -> would have + Past Participle.",
    },
    {
        "id": 6,
        "level": "B1",
        "question": "The company decided to __________ the product launch until next month due to technical issues.",
        "options": ["postpone", "cancel", "accelerate", "promote"],
        "correct": 1,
        "explanation": "'Postpone' means to delay an event until a later time.",
    },
    {
        "id": 7,
        "level": "B2",
        "question": "Hardly __________ entered the classroom when the exam started.",
        "options": ["I had", "had I", "I have", "did I"],
        "correct": 2,
        "explanation": "Starting a sentence with negative adverbs like 'Hardly' requires subject-auxiliary inversion, making it 'had I'.",
    },
    {
        "id": 8,
        "level": "B2",
        "question": "She has an __________ eye for detail, which makes her an excellent editor.",
        "options": ["acute", "obtuse", "approximate", "indifferent"],
        "correct": 1,
        "explanation": "An 'acute eye for detail' is an idiomatic phrase meaning a keen or highly developed ability to notice details.",
    },
    # Advanced Level (C1)
    {
        "id": 9,
        "level": "C1",
        "question": "Were it not for your timely intervention, we __________ in deep trouble right now.",
        "options": ["will be", "would have been", "would be", "are"],
        "correct": 3,
        "explanation": "This is a Mixed Conditional: an imaginary past condition (Were it not for...) paired with a present result (would be).",
    },
    {
        "id": 10,
        "level": "C1",
        "question": "The politician's speech was full of empty promises and lacked any __________ solutions.",
        "options": ["superficial", "tangible", "transient", "ambiguous"],
        "correct": 2,
        "explanation": "'Tangible' means clear, real, and concrete—the opposite of empty promises.",
    },
]

# We will use this to grade the user later
CORRECT_ANSWERS_MAP = {q["id"]: q["correct"] for q in ACADEMIC_QUESTIONS}
