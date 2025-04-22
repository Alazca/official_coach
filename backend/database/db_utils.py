"""
Database utilities for the AI Weightlifting Assistant.

This module provides common database functions used across the application,
with enhanced error handling, connection management, and type safety.
"""

import sqlite3
import datetime
import traceback

from typing import Any, Dict, List, Tuple, Union, Optional, TypeVar, Callable
from contextlib import contextmanager
from functools import wraps

from backend.config.config import Config

# Type definitions
T = TypeVar('T')
Row = Dict[str, Any]
QueryResult = Union[List[Row], Row, int, None]
DBError = Union[str, Exception]

@contextmanager
def db_connection():
    """
    Context manager for database connections.
    Automatically handles connection creation, commits, and cleanup.
    
    Yields:
        sqlite3.Connection: Database connection with row factory enabled
    """
    connection = None
    try:
        # Get connection from Config
        config = Config()
        db_path = config.get_database_path()
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
 
        yield connection  
        connection.commit()
    except Exception as e:
        if connection:
            connection.rollback()
        raise e
    finally:
        if connection:
            connection.close()


def db_operation(func: Callable[..., T]) -> Callable[..., Union[T, DBError]]:
    """
    Decorator for database operations.
    Handles connection management, cursor creation, and error handling.
    
    Args:
        func: The database operation function to decorate
    
    Returns:
        Wrapped function that handles connection and error management
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Union[T, DBError]:
        try:
            with db_connection() as conn:
                cursor = conn.cursor()
                result = func(cursor, *args, **kwargs)
                cursor.close()
                return result
        except Exception as e:
            # Consider logging the error here
            return str(e)
    return wrapper


def execute_query(query: str, params: Tuple = None) -> List[Dict[str, Any]]:
    """
    Execute a database query and return results as a list of dictionaries.
    
    Args:
        query: SQL query to execute
        params: Parameters for the query
        
    Returns:
        List of dictionaries containing query results
    """
    with db_connection() as connection:
        cursor = connection.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            # Get results
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            result = [dict(row) for row in rows]
            
            return result
        finally:
            cursor.close()


def execute_insert(query: str, params: Tuple) -> int:
    """
    Execute an insert query and return the ID of the inserted row.
    
    Args:
        query: SQL insert query
        params: Parameters for the query
        
    Returns:
        ID of the inserted row
    """
    with db_connection() as connection:
        cursor = connection.cursor()
        
        try:
            cursor.execute(query, params)
            return cursor.lastrowid or 0
        finally:
            cursor.close()


def execute_update(query: str, params: Tuple) -> int:
    """
    Execute an update query and return the number of affected rows.
    
    Args:
        query: SQL update query
        params: Parameters for the query
        
    Returns:
        Number of affected rows
    """
    with db_connection() as connection:
        cursor = connection.cursor()
        
        try:
            cursor.execute(query, params)
            return cursor.rowcount
        finally:
            cursor.close()


@db_operation
def user_exists(cursor, email: str) -> Union[Row, bool, DBError]:
    """
    Check if a user with the given email exists.
    
    Args:
        cursor: Database cursor
        email: User's email address
    
    Returns:
        User data if exists, False otherwise, or error message
    """
    # Using parameterized query to prevent SQL injection
    cursor.execute(
        "SELECT user_id, email, password_hash FROM users WHERE email = ?", 
        (email,)
    )
    data = cursor.fetchone()
    
    if data:
        return dict(data)
    return False


@db_operation
def get_all_checkins(
    cursor, 
    user_id: int, 
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None
) -> Union[List[Row], DBError]:
    """
    Get all check-ins for a user, optionally filtered by date range.
    
    Args:
        cursor: Database cursor
        user_id: User ID to fetch check-ins for
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
    
    Returns:
        List of check-in records or error message
    """
    if end_date and start_date:
        cursor.execute("""
            SELECT * FROM daily_checkins
            WHERE user_id = ? AND check_in_date BETWEEN ? AND ? 
            ORDER BY check_in_date DESC
            """, (user_id, start_date, end_date))
    else:
        cursor.execute("""
            SELECT * FROM daily_checkins
            WHERE user_id = ?
            ORDER BY check_in_date DESC
            """, (user_id,))

    data = cursor.fetchall()
    return [dict(row) for row in data]


@db_operation
def get_workout_history(
    cursor,
    user_id: Optional[int] = None, 
    startdate: Optional[str] = None, 
    enddate: Optional[str] = None
) -> Union[List[Row], DBError]:
    """
    Get workout history for a user, optionally filtered by date range.
    
    Args:
        cursor: Database cursor
        user_id: User ID to fetch workouts for
        startdate: Optional start date filter (YYYY-MM-DD)
        enddate: Optional end date filter (YYYY-MM-DD)
    
    Returns:
        List of workout records or error message
    """
    if not user_id:
        return []
        
    # Build query parameters
    params = [user_id]
    query = "SELECT workout_id, workout_type, workout_date, notes FROM workouts WHERE user_id = ?"
    
    # Add date filters if provided
    if startdate and enddate:
        query += " AND workout_date BETWEEN ? AND ?"
        params.extend([startdate, enddate])
    elif startdate:
        query += " AND workout_date >= ?"
        params.append(startdate)
    elif enddate:
        query += " AND workout_date <= ?"
        params.append(enddate)
    
    # Add order by clause
    query += " ORDER BY workout_date DESC"
    
    cursor.execute(query, params)
    data = cursor.fetchall()
    return [dict(row) for row in data]


# @db_operation
def register_user(
    cursor,
    email, 
    password_hash, 
    name, 
    gender, 
    dob, 
    height, 
    weight, 
    activity_level
) -> Union[int, DBError]:
    """
    Register a new user in the database.
    
    Args:
        cursor: Database cursor
        email: User's email address
        password_hash: Hashed password
        name: User's name
        gender: User's gender (Male, Female, Other)
        dob: Date of birth (YYYY-MM-DD)
        height: Height in cm
        weight: Weight in kg
        activity_level: Initial activity level (Sedentary, Casual, Moderate, Active, Intense)
    
    Returns:
        New user ID or error message
    """
    cursor.execute('''
            INSERT INTO users (
                email, 
                password_hash, 
                name, 
                gender, 
                dateOfBirth, 
                height, 
                weight, 
                initialActivityLevel
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (email, password_hash, name, gender, dob, height, weight, activity_level))

    user_id = cursor.lastrowid

    if not user_id:
        raise ValueError("Failed to create user - no ID returned")
    
    return user_id

@db_operation
def insert_check_in(
    cursor,
    user_id: int, 
    weight: float, 
    sleep: int, 
    stress: int, 
    energy: int, 
    soreness: int, 
    check_in_date: str
) -> Union[int, DBError]:
    """
    Insert a new daily check-in record and calculate readiness score.
    
    Args:
        cursor: Database cursor
        user_id: User ID
        weight: User's weight in kg
        sleep: Sleep quality (1-10)
        stress: Stress level (1-10)
        energy: Energy level (1-10)
        soreness: Soreness level (1-10)
        check_in_date: Check-in date (YYYY-MM-DD)
    
    Returns:
        New check-in ID or error message
    """
    try:
        # First insert the check-in record
        cursor.execute("""
        INSERT INTO daily_checkins(
            user_id,
            weight,
            sleep_quality,
            stress_level,
            energy_level,
            soreness_level,
            check_in_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, weight, sleep, stress, energy, soreness, check_in_date))
        
        checkin_id = cursor.lastrowid
        if not checkin_id:
            raise ValueError("Failed to create check-in - no ID returned")
        
        # Calculate readiness score (simplified algorithm)
        readiness_score = calculate_readiness_score(sleep, stress, energy, soreness)
        
        # Now insert the readiness score
        cursor.execute("""
        INSERT INTO readiness_scores(
            user_id,
            readiness_score,
            contributing_factors,
            readiness_date,
            source,
            alignment_score,
            overtraining_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, 
            readiness_score, 
            f"Sleep: {sleep}, Stress: {stress}, Energy: {energy}, Soreness: {soreness}",
            check_in_date,
            'Auto',
            (sleep + energy) / 20.0,  # Simple alignment score
            (stress + soreness) / 20.0  # Simple overtraining risk
        ))
        
        readiness_id = cursor.lastrowid
        
        # Update the check-in with the readiness ID reference
        if readiness_id:
            cursor.execute("""
            UPDATE daily_checkins SET readiness_id = ? WHERE checkin_id = ?
            """, (readiness_id, checkin_id))
        
        return checkin_id
    except Exception as e:
        raise Exception(f"Error in insert_check_in: {str(e)}")


def calculate_readiness_score(sleep: int, stress: int, energy: int, soreness: int) -> int:
    """
    Calculate readiness score based on check-in metrics.
    
    Args:
        sleep: Sleep quality (1-10)
        stress: Stress level (1-10)
        energy: Energy level (1-10)
        soreness: Soreness level (1-10)
        
    Returns:
        Readiness score (0-100)
    """
    # Normalize stress and soreness (10 = good, 1 = bad)
    adjusted_stress = 11 - stress
    adjusted_soreness = 11 - soreness
    
    # Calculate average of all factors (all now on 1-10 scale where 10 is optimal)
    average = (sleep + adjusted_stress + energy + adjusted_soreness) / 4.0
    
    # Scale to 0-100
    return int(average * 10)


def get_user_data(user_id: int) -> Dict[str, Any]:
    """
    Get user data for a specific user.
    
    Args:
        user_id: User ID
        
    Returns:
        User data or None if user not found
    """
    query = "SELECT * FROM users WHERE user_id = ?"
    results = execute_query(query, (user_id,))
    
    return results[0] if results else None


def get_latest_checkin(user_id: int) -> Dict[str, Any]:
    """
    Get the latest daily check-in for a user.
    
    Args:
        user_id: User ID
        
    Returns:
        Latest check-in data or None if no check-ins found
    """
    query = """
    SELECT * FROM daily_checkins 
    WHERE user_id = ? 
    ORDER BY check_in_date DESC 
    LIMIT 1
    """
    
    results = execute_query(query, (user_id,))
    return results[0] if results else None


def save_readiness_score(readiness_data: Dict[str, Any]) -> int:
    """
    Save readiness score to the database.
    
    Args:
        readiness_data: Readiness data to save
        
    Returns:
        ID of the inserted readiness record
    """
    query = """
    INSERT INTO readiness_scores 
    (user_id, readiness_score, contributing_factors, readiness_date, 
     source, alignment_score, overtraining_score)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    
    params = (
        readiness_data["user_id"],
        readiness_data["readiness_score"],
        readiness_data["contributing_factors"],
        readiness_data["readiness_date"],
        readiness_data.get("source", "Auto"),
        readiness_data.get("alignment_score", 0),
        readiness_data.get("overtraining_score", 0)
    )
    
    return execute_insert(query, params)


def update_checkin_with_readiness(checkin_id: int, readiness_id: int) -> bool:
    """
    Update a check-in record with its associated readiness ID.
    
    Args:
        checkin_id: Check-in ID to update
        readiness_id: Readiness ID to associate
        
    Returns:
        True if update was successful, False otherwise
    """
    query = "UPDATE daily_checkins SET readiness_id = ? WHERE checkin_id = ?"
    
    affected_rows = execute_update(query, (readiness_id, checkin_id))
    return affected_rows > 0


@db_operation
def get_readiness_score(cursor, user_id: int, date: Optional[str] = None) -> Union[Row, None, DBError]:
    """
    Get the readiness score for a user on a specific date.
    
    Args:
        cursor: Database cursor
        user_id: User ID
        date: Optional date (YYYY-MM-DD), defaults to today
        
    Returns:
        Readiness score data or None if not found
    """
    if not date:
        date = datetime.datetime.now().strftime('%Y-%m-%d')
        
    cursor.execute("""
    SELECT * FROM readiness_scores 
    WHERE user_id = ? AND readiness_date = ?
    ORDER BY created_at DESC
    LIMIT 1
    """, (user_id, date))
    
    data = cursor.fetchone()
    if data:
        return dict(data)
    return None


@db_operation
def get_user_goals(cursor, user_id: int) -> Union[List[Row], DBError]:
    """
    Get all goals for a user.
    
    Args:
        cursor: Database cursor
        user_id: User ID
        
    Returns:
        List of goals
    """
    cursor.execute("""
    SELECT * FROM Goals
    WHERE user_id = ?
    ORDER BY target_date ASC
    """, (user_id,))
    
    data = cursor.fetchall()
    return [dict(row) for row in data]


@db_operation
def add_user_goal(
    cursor, 
    user_id: int, 
    goal_type: str, 
    description: str, 
    target_date: str
) -> Union[int, DBError]:
    """
    Add a new goal for a user.
    
    Args:
        cursor: Database cursor
        user_id: User ID
        goal_type: Type of goal (Strength, Endurance, Weight-Loss, Performance)
        description: Description of the goal
        target_date: Target date (YYYY-MM-DD)
        
    Returns:
        New goal ID
    """
    cursor.execute("""
    INSERT INTO Goals (
        user_id,
        goalType,
        description,
        target_date
    ) VALUES (?, ?, ?, ?)
    """, (user_id, goal_type, description, target_date))
    
    goal_id = cursor.lastrowid
    if not goal_id:
        raise ValueError("Failed to create goal - no ID returned")
        
    return goal_id


def validate_date(date_string: str) -> bool:
    """
    Validate if a string is a proper date in YYYY-MM-DD format.
    
    Args:
        date_string: Date string to validate
    
    Returns:
        True if valid, False otherwise
    """
    try:
        datetime.datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False



if __name__ == "__main__":
    # Example usage
    test_user_id = 1
    checkins = get_all_checkins(test_user_id, start_date='2025-04-03', end_date='2025-04-08')
    print(f"Found {len(checkins) if isinstance(checkins, list) else 0} check-ins")
