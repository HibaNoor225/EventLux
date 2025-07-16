# ✨ EventLux – Event Management Web Application

**EventLux** is a full-stack event management system built using Flask and MongoDB. It allows students and admins to manage, register for, and give feedback on university events. The system includes role-based access, automated email confirmations, feedback sentiment analysis, and reminder scheduling.

---

## 🚀 Features

### 👩‍🎓 Student / User
- Register with **PUCIT email only**
- Secure login with password hashing
- Browse and register for upcoming events
- Filter events by category
- View only your registered events
- Submit feedback after the event ends

### 🧑‍💼 Admin Panel
- Admin login via secret code
- Add, edit, or delete events (with image uploads)
- View all event registrations with student details
- Access feedback with **sentiment analysis** using TextBlob

### 💡 Other Highlights
- 📧 Confirmation emails sent upon registration
- ⏰ Event reminders handled via scheduled background tasks
- 🧠 Sentiment-based feedback insights: **Positive**, **Neutral**, or **Negative**
- 📂 Image/file uploads saved in `static/uploads`

---

## 🛠️ Tech Stack

| Layer      | Technology               |
|------------|---------------------------|
| Backend    | Python, Flask             |
| Database   | MongoDB with MongoEngine  |
| Templates  | Jinja2, HTML/CSS          |
| Auth       | Flask-Session             |
| Scheduler  | BackgroundScheduler       |
| NLP        | TextBlob (for sentiment)  |
| Email      | SMTP (Gmail/Yahoo etc.)   |

---

## 📧 Email & Reminders

- Event registration automatically sends a **confirmation email** to the user.
- `reminder_tasks.py` schedules and sends **event reminders** in the background.

---

## 📊 Feedback Sentiment

- Students submit feedback after attending events.
- Admins view all comments along with an **average sentiment score**:
  - 😃 Positive
  - 😐 Neutral
  - 😞 Negative

---

## 👩‍💻 Author

**Hiba Noor**  
B.S. Computer Science  

---

