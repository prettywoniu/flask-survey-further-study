from flask import Flask, request, render_template, redirect, make_response, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from surveys import surveys

# key names will use to store some things in the session;
# put here as constants so we're guaranteed to be consistent in
# our spelling of these
RESPONSES_KEY = "responses"
CURRENT_SURVEY_KEY = "current_survey"



app = Flask(__name__)
app.config['SECRET_KEY'] = "1234"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

debug = DebugToolbarExtension(app)


@app.route('/')
def pick_survey():
    """Select a survey"""
    return render_template('pick-survey.html',
                           surveys=surveys)

@app.route('/survey-start')
def show_survey_start():
    """Show instruction"""
    survey_id = request.args["survey_code"]
    survey = surveys[survey_id]
    session[CURRENT_SURVEY_KEY] = survey_id

    # don't let them re-take a survey until cookie times out
    if request.cookies.get(f"completed_{survey_id}"):
        return render_template("already-done.html")

    return render_template('survey-start.html',
                           survey=survey)


@app.route('/begin')
def survey_begin():
    """Clear the session of responses."""
    
    session[RESPONSES_KEY] = []

    return redirect("/question/0")
    

@app.route("/question/<int:qid>")
def show_question(qid):
    """Display current question."""

    responses = session.get(RESPONSES_KEY)
    survey_code = session[CURRENT_SURVEY_KEY]
    survey = surveys[survey_code]

    if (responses is None):
        # trying to access question page too soon
        return redirect("/")
    
    if (len(responses) == len(survey.questions)):
        # They've answered all the questions! Thank them.
        return redirect("/complete")
    
    if (len(responses) != qid):
        # Trying to access questions out of order.
        flash(f"Invalid question id: {qid}.")
        return redirect(f"/question/{len(responses)}")
    
    question = survey.questions[qid]
    return render_template(
        "question.html", question_num=qid, question=question)


@app.route('/answer')
def handle_questions():
    """Save response and redirect to next question."""

    # get the response choice and text
    choice = request.args["answer"]
    text = request.args.get("text", "")
    
    # add this response to the session
    responses = session[RESPONSES_KEY]
    responses.append({"choice": choice, "text": text})
    session[RESPONSES_KEY] = responses

    survey_id = session[CURRENT_SURVEY_KEY]
    survey = surveys[survey_id]

    if (len(responses) == len(survey.questions)):
        # They've answered all the questions! Thank them.
        return redirect("/complete")
    else:
        return redirect(f"/question/{len(responses)}")
    

@app.route('/complete')
def say_thanks():
    """Thank user and list responses."""

    responses = session.get(RESPONSES_KEY)
    survey_id = session[CURRENT_SURVEY_KEY]
    survey = surveys[survey_id]

    html = render_template("complete.html", 
                           responses=responses,
                           survey=survey)
    
    # Set cookie noting this survey is done so they can't re-do it
    resp = make_response(html)
    resp.set_cookie(f"completed_{survey_id}", "yes", max_age=60)
    return resp