from flask import Flask, request,render_template,session,url_for, flash,redirect
from flask_session import Session
from mongoengine import connect
from models import User,Event,Registrations,Feedback
from bson import ObjectId
from reminder_tasks import start_scheduler
from reminder_tasks import start_scheduler,send_event_reminders
from datetime import datetime
from email_handler import send_confirmation_email
import os
from werkzeug.utils import secure_filename
from ai_utils import analyze_sentiment  # Add this import at the top

from collections import defaultdict

app = Flask(__name__)
start_scheduler()
send_event_reminders()
app.secret_key="Your_secret_key"
app.config.from_object('config')
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


Session(app)

# MongoDB Configuration
db=connect(db="test", host="localhost", port=27017)

#root route
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register")
def register():
   return render_template("register.html")

@app.route("/registerUser", methods=["POST"])
def register_user():
    name = request.form["name"]
    email = request.form["email"]
    rollNo = request.form["rollNo"].strip()  # May be empty if admin
    password = request.form["password"]
    confirm_password = request.form["confirm_password"]
    admin_code = request.form["admin_code"].strip()

    # To ensure email is from pucit.edu.pk domain
    if not email.lower().endswith("@pucit.edu.pk"):
        return render_template("register.html", error="Only PUCIT emails (@pucit.edu.pk) are allowed")

    # Check if passwords match
    if password != confirm_password:
        return render_template("register.html", error="Passwords don't match")

    # Determine role
    ADMIN_SECRET=app.config["ADMIN_SECRET"]
    is_admin = (admin_code == ADMIN_SECRET)

    # If not admin, student must enter rollNo
    if not is_admin and not rollNo:
        return render_template("register.html", error="Roll Number is required")

    emailFound = User.objects(email=email).first()

    # Check if email already exists
    if emailFound:
        return render_template("login.html", error="Email already registered")

    rollNoFound= User.objects(rollNo=rollNo).first()

    # Check if rollNo already exists (for students only)
    if not is_admin and rollNoFound:
        return render_template("login.html", error="Roll Number already registered")

    # Create user
    user = User(
        name=name,
        email=email,
        rollNo=None if is_admin else rollNo,
        is_admin=is_admin
    )
    user.set_password(password)  # Hashing password via method in model
    user.save()
    session["email"] = email
    return render_template("login.html",msg="Registration successful! Please log in.")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/loginUser",methods=["POST"])
def login_user():
    email = request.form["email"]
    password = request.form["password"]


    user = User.objects(email=email).first()


    if user and user.check_password(password):
        session["user_id"] = str(user.id)
        session["is_admin"] = user.is_admin

        # Redirect to respective dashboards
        if user.is_admin:
            return render_template("admin_dashboard.html")
        else:
            return render_template("dashboard.html",name=user.name)

    else:
        return render_template("login.html", error="Invalid email or password")

@app.route("/admin/dashboard")
def admin_dashboard():
    return render_template("admin_dashboard.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return render_template("login.html")

    id = session["user_id"]
    user = User.objects(id=id).first()
    return render_template("dashboard.html",name=user.name)

@app.route("/forgot_password")
def forgot_password():
    return render_template("forgot_password.html")

@app.route("/reset_password", methods=["POST"])
def reset_password():
    email = request.form["email"]
    new_password = request.form["new_password"]
    confirm_password = request.form["confirm_password"]

    user = User.objects(email=email).first()

    if not user:
        return render_template("forgot_password.html", error="Email not found")

    if new_password != confirm_password:
        return render_template("forgot_password.html", error="Passwords do not match")

    user.set_password(new_password)
    user.save()

    return render_template("login.html", msg="Password reset successful. Please log in.")

@app.route("/logout")
def logout():
    session.clear()
    return render_template("login.html")



from collections import defaultdict

@app.route("/all_events", methods=["GET"])
def all_events():
    user_id = session.get('user_id')
    if not user_id:
        return render_template("login.html")

    search_category = request.args.get("category", "").strip().lower()

    # Get all events or filter by category
    all_events = Event.objects.order_by('date')
    grouped_events = defaultdict(list)

    for event in all_events:
        if search_category and (not event.category or search_category not in event.category.lower()):

            continue

        deadline_passed = datetime.today().date() > event.registration_deadline
        already_registered = Registrations.objects(user_id=user_id, event_id=str(event.id)).first() is not None
        spots_available = event.spots > 0
        show_button = not already_registered and spots_available and not deadline_passed

        message = ""
        if not spots_available:
            message = f"No spots left for '{event.title}'."
        elif deadline_passed:
            message = f"Registration deadline for '{event.title}' has passed."
        elif already_registered:
            message = f"You are already registered for '{event.title}'."

        grouped_events[event.category].append({
            "id": str(event.id),
            "title": event.title,
            "description": event.description,
            "date": event.date.strftime('%Y-%m-%d'),
            "time": event.time,
            "location": event.location,
            "spots": event.spots,
            "registration_deadline": event.registration_deadline.strftime('%Y-%m-%d'),
            "show_button": show_button,
            "message": message
        })

    return render_template("all-events.html", grouped_events=grouped_events, search=search_category)

@app.route('/register_event', methods=['POST'])
def register_event():
    user_id = session.get("user_id")
    user = User.objects(id=user_id).first()
    user_email=user.email
    user_name=user.name
    if not user_id:
        return render_template("login.html")

    event_id = request.form.get("event_id")

    event = Event.objects(id=event_id).first()
    try:

     registration = Registrations(user_id=user_id, event_id=event_id)
     registration.save()


     event.spots -= 1
     event.save()
     send_confirmation_email(user_email, event,user_name)
     return render_template("SuccessUser.html",message="Event successfully registered.")
    except Exception as e:
        return render_template("Error.html", error="You are already registered for this event.")

@app.route("/my_events")
def my_events():
    user_id = session.get("user_id")
    if not user_id:
        return render_template("login.html")

    search_category = request.args.get("category", "").strip().lower()
    registrations = Registrations.objects(user_id=user_id)
    grouped_events = defaultdict(list)

    for reg in registrations:
        try:
            event = Event.objects(id=ObjectId(reg.event_id)).first()
        except:
            continue

        if not event:
            continue

        # Filter by category
        if search_category and (not event.category or search_category not in event.category.lower()):
            continue

        event_date_passed = datetime.today().date() > event.date
        feedback = Feedback.objects(user_id=user_id, event_id=reg.event_id).first()
        feedback_given = feedback is not None
        can_give_feedback = event_date_passed and not feedback_given

        grouped_events[event.category].append({
            "id": str(event.id),
            "title": event.title,
            "description": event.description,
            "date": event.date.strftime('%Y-%m-%d'),
            "time": event.time,
            "location": event.location,
            "feedback_given": feedback_given,
            "can_give_feedback": can_give_feedback,
            "registration_deadline": event.registration_deadline.strftime('%Y-%m-%d'),
        })

    return render_template("my-events.html", grouped_events=grouped_events, search=search_category)

@app.route("/feedback/<event_id>", methods=["GET", "POST"])
def feedback(event_id):
    user_id = session.get("user_id")
    if not user_id:
        return render_template("login.html")

    event = Event.objects(id=event_id).first()
    if not event:
        return "Event not found", 404

    registration = Registrations.objects(user_id=user_id, event_id=event_id).first()
    if not registration:
        return "You are not registered for this event", 403

    if datetime.today().date() <= event.date:
        return "You can give feedback only after the event ends", 403

    # If feedback already exists
    feedback = Feedback.objects(user_id=user_id, event_id=event_id).first()
    if feedback:
        return render_template("error.html",error="You have already give feedback for this event.")

    # POST: submit feedback
    if request.method == "POST":
        rating = request.form.get("rating")
        comments=request.form.get("comments")


        Feedback(user_id=user_id, event_id=event_id, rating=rating,comments=comments).save()
        return render_template("SuccessUser.html", message="Feedback successfully submitted.")

    # GET: show feedback form
    return render_template("feedback.html", event=event)

#List,add,edit and delete events
@app.route("/admin/events", methods=["GET", "POST"])
def manage_events():
    if not session.get("is_admin"):
        return "Unauthorized", 403

    events = Event.objects.order_by("date")

    return render_template("admin_events.html", events=events)

@app.route("/addEvent", methods=["GET", "POST"])
def add_event():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        date = request.form["date"]
        time = request.form["time"]
        location = request.form["location"]
        capacity = int(request.form["capacity"])
        registration_deadline = request.form["registration_deadline"]
        category = request.form.get("category")

        new_event = Event(
            title=title,
            description=description,
            date=date,
            time=time,
            location=location,
            capacity=capacity,
            spots=capacity,
            registration_deadline=registration_deadline,
            category=category,
            images=[]
        )

        # Handle image upload
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file.filename:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    new_event.images.append(filename)

        new_event.save()
        return render_template("Success.html", message="Event added successfully.")  # Your original success flow

    return render_template("event_form.html", action="Add", event=None)

@app.route('/edit_event/<event_id>', methods=['GET', 'POST'])
def edit_event(event_id):
    event = Event.objects(id=event_id).first()

    if request.method == 'POST':
        # Only handle save when the form_action is "save" or if form_action is missing (fallback)
        form_action = request.form.get("form_action", "save")  # default to save if not present

        if form_action == "save":
            event.title = request.form['title']
            event.description = request.form['description']
            event.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            event.time = request.form['time']
            event.location = request.form['location']
            event.capacity = int(request.form['capacity'])
            event.registration_deadline = datetime.strptime(request.form['registration_deadline'], '%Y-%m-%d').date()
            event.category = request.form['category']

            uploaded_images = request.files.getlist('images')
            for image in uploaded_images:
                if image.filename:
                    filename = secure_filename(image.filename)
                    image.save(os.path.join(app.root_path, 'static/uploads', filename))
                    event.images.append(filename)

            event.save()
            flash("Event updated successfully!", "success")
            return redirect(url_for('manage_events'))

    return render_template('event_form.html', action="Edit", event=event)

@app.route("/admin/events/delete/<event_id>", methods=["POST"])
def delete_event(event_id):
    if not session.get("is_admin"):
        return "Unauthorized", 403

    event = Event.objects(id=event_id).first()
    if event:
        event.delete()
    return render_template("success.html", message="Event deleted successfully.")
@app.route("/admin/event/<event_id>/delete_image/<image_name>", methods=["POST"])
def delete_event_image(event_id, image_name):
    event = Event.objects(id=event_id).first()
    if not event:
        return "Event not found", 404

    # Remove image from DB
    if image_name in event.images:
        event.images.remove(image_name)
        event.save()

    # Remove image file from static/uploads if it exists
    image_path = os.path.join("static/uploads", image_name)
    if os.path.exists(image_path):
        os.remove(image_path)

    return redirect(url_for("edit_event", event_id=event_id))

@app.route("/admin/event/<event_id>/registrations")
def view_event_registrations(event_id):
    if not session.get("is_admin"):
        return "Unauthorized", 403

    event = Event.objects(id=event_id).first()
    if not event:
        return "Event not found", 404

    registrations = Registrations.objects(event_id=event_id)
    users = []
    for reg in registrations:
        user = User.objects(id=reg.user_id).first()
        if user:
            users.append({
                "name": user.name,
                "email": user.email,
                "rollNo": user.rollNo
            })

    return render_template("view_registrations.html", event=event, users=users)

from textblob import TextBlob  # Make sure this is installed

@app.route("/admin/event/<event_id>/feedbacks")
def view_event_feedbacks(event_id):
    if not session.get("is_admin"):
        return "Unauthorized", 403

    event = Event.objects(id=event_id).first()
    if not event:
        return "Event not found", 404

    feedbacks = Feedback.objects(event_id=event_id)

    feedback_data = []
    sentiment_scores = []

    for fb in feedbacks:
        user = User.objects(id=fb.user_id).first()
        name = user.name if user else "Unknown"
        email = user.email if user else "Unknown"
        comment = fb.comments or ""

        # Sentiment analysis using TextBlob
        analysis = TextBlob(comment)
        polarity = analysis.sentiment.polarity  # -1 to 1
        sentiment_scores.append(polarity)

        feedback_data.append({
            "name": name,
            "email": email,
            "rating": fb.rating,
            "comments": comment
        })

    # Calculate average sentiment
    if sentiment_scores:
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        if avg_sentiment > 0.1:
            overall_sentiment = "Positive"
        elif avg_sentiment < -0.1:
            overall_sentiment = "Negative"
        else:
            overall_sentiment = "Neutral"
    else:
        overall_sentiment = "No feedback yet"

    return render_template("admin_event_feedbacks.html", event=event, feedbacks=feedback_data, sentiment=overall_sentiment)

@app.route("/event/<event_id>")
def event_details(event_id):
    user_id = session.get("user_id")
    if not user_id:
        return render_template("login.html")

    event = Event.objects(id=event_id).first()
    if not event:
        return "Event not found", 404

    deadline_passed = datetime.today().date() > event.registration_deadline
    already_registered = Registrations.objects(user_id=user_id, event_id=str(event.id)).first() is not None
    spots_available = event.spots > 0
    show_button = not already_registered and spots_available and not deadline_passed

    message = ""
    if not show_button:
        if not spots_available:
            message = f"No spots left for this event."
        elif deadline_passed:
            message = f"Registration deadline has passed."
        elif already_registered:
            message = f"You are already registered for this event."

    return render_template(
        "event_details_register.html",
        event=event,
        show_button=show_button,
        message=message
    )
@app.route("/my_event/<event_id>")
def my_event_details(event_id):
    user_id = session.get("user_id")
    if not user_id:
        return render_template("login.html")

    event = Event.objects(id=event_id).first()
    if not event:
        return "Event not found", 404

    registration = Registrations.objects(user_id=user_id, event_id=str(event.id)).first()
    if not registration:
        return "Not registered", 403

    event_date_passed = datetime.today().date() > event.date
    feedback = Feedback.objects(user_id=user_id, event_id=str(event.id)).first()
    feedback_given = feedback is not None
    can_give_feedback = event_date_passed and not feedback_given

    # ✨ Add this logic to send a meaningful message to the template
    if feedback_given:
        message = "You have already submitted feedback for this event."
    elif not event_date_passed:
        message = "You can give feedback only after the event ends."
    else:
        message = ""  # feedback can be given, so no error message

    return render_template(
        "event_details_feedback.html",
        event=event,
        can_give_feedback=can_give_feedback,
        feedback_given=feedback_given,
        message=message,
        datetime=datetime
    )



if __name__=="__main__":
    app.run(debug=True)
