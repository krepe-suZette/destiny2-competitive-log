from flask import Flask, render_template, request
import json

import get_info


with open("player_name", "r", encoding="utf-8") as f:
    PLAYER_NAME = f.read().strip()
app = Flask(__name__)


@app.route("/")
def root():
    with open("crucible_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    with open("daily_review.json", "r", encoding="utf-8") as f:
        review = json.load(f)
    return render_template("root.html", data=data, review=review)


@app.route("/update")
def update():
    get_info.update(PLAYER_NAME)
    return "<script language='javascript'>self.close();</script>"


@app.route("/review")
def review_update():
    date = request.args.get("date")
    with open("daily_review.json", "r", encoding="utf-8") as f:
        review = json.load(f)
    return render_template("review.html", date=date, data=review.get(date, ""))


@app.route('/review/post', methods=["POST"])
def review_post():
    # review, date
    with open("daily_review.json", "r", encoding="utf-8") as f:
        review = json.load(f)
    review[request.form["date"]] = request.form["review"]
    with open("daily_review.json", "w", encoding="utf-8") as f:
        json.dump(review, f, ensure_ascii=False, indent=2)
    return "<script language='javascript'>self.close();</script>"


@app.route("/initialize")
def initialize():
    get_info.initializing_all(PLAYER_NAME)
    get_info.update(PLAYER_NAME)
    return "<script language='javascript'>self.close();</script>"


if __name__ == "__main__":
    app.run("0.0.0.0", debug=True)
