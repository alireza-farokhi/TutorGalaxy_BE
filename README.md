# TutorGalaxy Backend Server

A backend server for the TutorGalaxy application, providing tutoring services, Stripe payment integration, Google Text-to-Speech, and code execution.

> **Note**: This is the backend repository. The frontend repository can be found at [TutorGalaxy-FE](https://github.com/FarzamHejaziK/TutorGalaxy_FE).


# Table of Contents

## Quick Start
- [Getting Started](#getting-started)
  - [Installation Steps](#getting-started)
  - [Environment Setup](#set-environment-variables)
  - [Running the Server](#start-the-server)

## Project Overview
- [What is Tutor Galaxy?](#what-is-tutor-galaxy)
- [Project Structure](#project-structure)
- [Database Configuration](#database-configuration)

## Architecture
- [Architecture Overview](#architecture-overview)
- [Components](#architecture-overview)
  - [Tutor Initialization Agent](#tutor-initialization-agent)
  - [Ongoing Tutor-User Interaction Agent](#ongoing-tutor-user-interaction-agent)
    - [Planner Agent](#ongoing-tutor-user-interaction-agent)
    - [Plan Executor Agent](#ongoing-tutor-user-interaction-agent)
    - [Plan Checker](#ongoing-tutor-user-interaction-agentr)

## Core Features
- [Long-Term Learning](#long-term-learning-and-sticking-to-the-plan)
  - [Next Action Predictor](#long-term-learning-and-sticking-to-the-plan)
  - [Update System Prompt](#long-term-learning-and-sticking-to-the-plan)
  - [Plan Progress Tracker](#long-term-learning-and-sticking-to-the-plan)

## Additional Features
- [Additional Info and Features](#additional-info-and-features)
  - [Stripe Payment Integration](#additional-info-and-features)
  - [Google Text-to-Speech](#additional-info-and-features)
  - [Code Execution](#additional-info-and-features)


## Getting Started

1. **Clone the repository:**

    ```bash
    git clone https://github.com/FarzamHejaziK/TutorGalaxy_BE.git
    cd TutorGalaxy_BE
    ```

2. **Set up a virtual environment:**

    ```bash
    python -m venv myenv
    source myenv/bin/activate # On Windows: myenv\Scripts\activate
    ```

3. **Install dependencies:**

    ```bash
    # Upgrade pip first
    python -m pip install --upgrade pip

    # Install binary dependencies
    pip install -r requirements-binary.txt

    # Install remaining dependencies
    pip install -r requirements.txt
    ```

4. **Set environment variables:**

    **Required Environment Variables:**
    - **OpenAI API Keys (comma-separated)**  
      `OPENAI_API_KEYS=your-api-key-1,your-api-key-2`  
      >Note: You can only add one API key

    **Optional Environment Variables:**
    - **Stripe Keys (for payment features)**  
      `secret_key=your-stripe-secret-key`  
      `price_id=your-stripe-price-id`  
      `webhook_secret=your-stripe-webhook-secret`

    - **Google Cloud (for Text-to-Speech)**  
      `GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json`

    - **RapidAPI (for code execution)**  
      `RAPID_API_TOKEN=your-rapid-api-token`

5. **Start the server:**

    ```bash
    python wsgi.py
    ```
    The server will start on `http://localhost:8000` by default.


## Project Structure

```
TutorGalaxy-BE-Server/
├── APIs/                # API endpoints
├── init_agent/          # Tutor initialization
├── tutor_agent/         # Main tutoring logic
├── payment/             # Stripe integration
├── text_to_speech/      # Google TTS integration
├── code_execution/      # Code execution service
├── config.py            # Configuration and DB setup
└── wsgi.py              # Main application file
```
## Database Configuration

The original implementation of the database used **DynamoDB** for scalable, production-ready data storage. However, for ease of use and educational purposes, we have replaced **DynamoDB** with **TinyDB** in this version. TinyDB is an embedded, serverless database, making it simpler to set up and use for local development without requiring a separate database server. This adjustment allows users to experiment with TutorGalaxy's core functionality in a more accessible environment.

**Note:** TinyDB is suitable for lightweight, local use but has limitations, including slower performance with large datasets and lack of advanced querying features. For production or high-scale environments, transitioning back to a database like DynamoDB is recommended.

# Disclaimer

This repository hosts the code for the **TutorGalaxy** service, originally designed as a backend for [TutorGalaxy.com](https://tutor-galaxy.com). Over time, I will refine and organize the code and the README to make it more user-friendly and adaptable as a package for broader use.



# What is tutor galaxy?
Tutor Galaxy is a personal tutoring service, and its key differentiator from **ChatGPT** is its ability to create and stick to a long-term learning plan for the user. Unlike ChatGPT, which is more focused on short-term interactions, Tutor Galaxy is designed to stay committed to the user's learning plan over time. It has been observed that ChatGPT, even when attempting to plan for a user, tends to deviate from the plan as the conversation progresses. In the following section, we will dive deeper into how Tutor Galaxy addresses the challenge of maintaining commitment to long-term plans. 

# Architecture Overview
Tutor Galaxy has two conversational agents. The first agent is the Tutor Initialization Agent, which sets up the tutoring process. After that, the Tutor Agent takes over and creates a personalized tutoring session for the user. The following is the block diagram of the Tutor Galaxy service.
<img width="1877" alt="image" src="https://github.com/FarzamHejaziK/TutorGalaxy_BE/blob/main/images/git-be-1.png">





# Tutor Initialization Agent

To understand the user's expectations, the agent starts a conversation to extract the main features the tutor should have from the user's point of view. The primary features the system aims to extract are:

- The topic that the tutor should discuss with the user.
- Whether the tutor should only answer questions or also plan and teach the course to the user.
- The character or personality of the tutor.


# Ongoing Tutor-User Interaction Agent

The Tutor Agent consists of two main sub-agents: the **Planner Agent** and the **Plan Executor Agent**. Based on the features extracted in the initialization phase, the **Planner Agent** starts by understanding the user's preferred learning style and then creates a customized session plan. The Planner Agent continues the tutoring session until the session planning is done and ready to be handed off to the **Plan Executor Agent**.

The **Plan Checker** verifies whether the Planner Agent has completed the session plan and whether the user has approved it before handing off to the Plan Executor Agent. This ensures the tutoring process is aligned with the user's goals and expectations before moving forward.

The **Plan Executor Agent** is responsible for following the developed plan, answering user questions, and maintaining alignment with the session goals.

The main challenge here is **maintaining focus on the plan, as the user may ask numerous questions during each step. This makes it increasingly difficult for the tutor to stick to the original plan as the conversation becomes lengthy and complex.**

<img width="990" alt="image" src="https://github.com/FarzamHejaziK/TutorGalaxy_BE/blob/main/images/git-be-2.png">





# Long-Term Learning and Sticking to the Plan


The main objective of the Plan Executor Agent is to ensure that the tutor stays committed to the long-term learning plan and prevents deviation during the ongoing conversation with the user. It is important to note that the plan has already been extracted by the Plan Checker and is assumed to be fixed. The inputs to the agent include the conversation history, the learning plan, the plan pointer, and the latest user message. The plan pointer indicates the specific topic within the plan that the current conversation is addressing.

The first module in the agent is the **"Next Action Predictor"**, which determines the next best action among the following options:
1. Start a new topic.
2. Continue with the current topic.
3. Answer a user question.
4. Continue answering an ongoing user question.

Once the next action is predicted, the **"Update System Prompt"** module updates the system prompt, and the system responds to the user in alignment with the suggested action. After the system message is generated, the **"Plan Progress Tracker Module"** checks the conversation and updates the plan pointer accordingly.

<img width="1599" alt="image" src="https://github.com/FarzamHejaziK/TutorGalaxy_BE/blob/main/images/git-be-3.png">


# Additional Info and Features

Several additional features have been implemented:

1. Recurring payments using Stripe API for user subscriptions.
2. Text-to-speech functionality using Google APIs.
3. Code execution capability for courses where the user requests to learn a programming language.



# Collaboration & Support

I'm very open to collaboration and welcome any questions or suggestions! Feel free to:

- 🤝 **Contribute**: Submit pull requests or suggest new features
- 💡 **Ask Questions**: Open an issue or reach out directly
- 🐛 **Report Bugs**: Create an issue with a detailed description
- 🚀 **Share Ideas**: Have an idea for improvement? Let's discuss it!

### How to Get in Touch
- 📧 Email: [farzam.hejazi@gmail.com](farzam.hejazi@gmail.com)
- 🌐 LinkedIn: [Farzam Hejazi](https://www.linkedin.com/in/farzam-hejazi-5b608081/)


### Support the Project
- ⭐ Star this repository
- 📢 Share it with others
- 📝 Write about your experience using it

I believe in the power of community and collaborative development. Whether you're a beginner or an experienced developer, your input is valuable and appreciated!

---








