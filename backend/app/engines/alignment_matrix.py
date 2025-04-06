import sqlite3
import os
from numpy import array, dot
from numpy.linalg import norm

def normalize(data):
    return data / norm(data)


def weightedSimilarity(userVector, targetVector, factor):
    userVectorWeight = userVector * factor
    targetVectorWeight = targetVector * factor
    return (
        dot(userVectorWeight, targetVectorWeight)
        / norm(userVectorWeight)
        * norm(targetVectorWeight)
    )


def evaluateVectors(user_input: dict, user_id: int, factors: list = None) -> dict:
    factors = array(factors or [1, 1, 1, 1, 1, 1, 1])
    goalRow = UserGoalVector.query.filter_by(user_id=user_id).first()
    overtrainingRow = OvertrainingVector.query.first()
    factors = array(factors or [1, 1, 1, 1, 1, 1, 1, 1])

    with get_connection() as conn:
        goal_cursor = conn.execute(
            """
            SELECT protein, calories, carbs, fats, sleep_quality, stress_level, soreness, readiness
            FROM user_goal_vectors
            WHERE user_id = ?
            """,
            (user_id,)
        )
        goalRow = goal_cursor.fetchone()
        overtraining_cursor = conn.execute(
            """
            SELECT protein, calories, carbs, fats, sleep_quality, stress_level, soreness, readiness
            FROM overtrainingvector
            LIMIT 1
            """
        )

        overtrainingRow = overtraining_cursor.fetchone()

    if not goalRow:
        return {"error": f"No goal vector found for user {user_id}"}
    if not overtrainingRow:
        return {"error": "Overtraining reference vector not defined in database."}

    userVector = normalize(
        array[
            user_input.get("protein", 0),
            user_input.get("calories", 0),
            user_input.get("carbs", 0),
            user_input.get("fats", 0),
        ]
    )

    goalVector = normalize(
        array[
            goalRow.protein,
            goalRow.calories,
            goalRow.carbs,
            goalRow.fats,
        ]
    )

    overtrainingVector = normalize(
        array[
            overtrainingRow.protein,
            overtrainingRow.calories,
            overtrainingRow.carbs,
            overtrainingRow.fats,
        ]
    )

    return {
        "goal_alignment": goal_alignment,
        "overtraining_risk": overtraining_risk,
        "recommendation": recommendation,
    }
