from app.vision.models import FoodObservation

def build_retrieval_query(
    user_question: str,
    observation: FoodObservation,
) -> str:
    parts = [user_question.strip()]
    if observation.food_name:
        parts.append(f"Observed food candidate: {observation.food_name}")
    if observation.visible_ingredients:
        parts.append(
            "Observed possible ingredients: " + ", ".join(observation.visible_ingredients)
        )
    if observation.preparation_characteristics:
        parts.append(
            "Observed preparation characteristics: "
            + ", ".join(observation.preparation_characteristics)
        )
    parts.append(
        "Visual observations: "
        + (", ".join(observation.visual_observations) or "none")
    )
    parts.append(
        "Important: visual observations are uncertain evidence; retrieve authoritative "
        "food information rather than treating them as exact facts."
    )
    return "\n".join(parts)
