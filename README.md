# Strength & Conditioning AI Assistant

## Overview

This project is a web application that provides personalized strength and conditioning workout plans using AI. It allows users to input their fitness goals, experience level, and available equipment, and then generates customized workout routines tailored to their needs.

## Features

*   **User Authentication:** Secure user registration and login system.
*   **Profile Management:** Users can create and manage their profiles, including fitness goals, experience level, and available equipment.
*   **AI-Powered Workout Generation:** Generates personalized workout plans based on user input using an AI model.
*   **Exercise Database:** A comprehensive database of exercises with descriptions, images/videos, and instructions.
*   **Workout Tracking:** Users can track their progress and record their workouts.
*   **Progress Visualization:** Displays user progress through charts and graphs.
*   **Responsive Design:** The web app is designed to work well on different devices (desktops, tablets, smartphones).

## Technologies Used

*   **Backend:**
    *   Python
    *   Flask (web framework)
    *   SQLite3
*   **Frontend:**
    *   JavaScript
    *   HTML
    *   CSS
*   **AI:**
    *   OpenAI API
*   **Deployment:**
    *   Gunicorn (WSGI server)

## Prerequisites

Before you begin, ensure you have met the following requirements:

*   Python 3.0+
*   SQLite3

## Installation

Follow these steps to set up the project locally:

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/Alazca/official_coach.git
    cd official_coach
    ```

2.  **Create a virtual environment:**

    **Using `venv`:**

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # Linux/macOS
         # OR
    .venv\Scripts\activate  # Windows
    ```

3.  **Install dependencies:**

    *   **Using the `venv`:**

        ```bash
        pip install -r requirements.txt
        ```

4.  **Configure the application:**

    *   Create a `.env` file in the root directory of the project.
    *   After database is selected, WIP
   
    *   **Important:** Replace the placeholder values with your actual values.  *Never* commit your `.env` file to version control.

5.  **Initialize the database:**

## Usage

1.  **Run the application:**

    ```bash
    flask run
    ```

2.  **Access the web app:**

    Open your web browser and navigate to `http://127.0.0.1:5000/` (or the address and port where your application is running).


## Contributing

We welcome contributions to this project! To contribute, please follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes and commit them with clear and concise commit messages.
4.  Submit a pull request.

Please adhere to the following guidelines:

*   Write unit tests for your code.
*   Document your code clearly.
*   Ensure that your changes do not break existing functionality.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

*   [Acknowledge any libraries, frameworks, or resources that you used in the project]
*   Acknowledge the following people for their support and aid:
    - Chimmy, SJSU Student : Provided expertise in proper database deployment
    - Yohan / Jin, SJSU Students : Comedic support and mad jokes about backshots
    - Dr. Daphne Chen : Professor and mentor to students

## Future Enhancements

*   WIP
