from flask_mail import Message


class Feedback(object):
    __tablename__ = "feedback"

    @staticmethod
    def distribute(issue, image):
        from reciperadar import app, mail

        with app.app_context():
            title = issue.pop("issue") or "(empty)"
            title = issue if len(issue) < 25 else f"{issue[:25]}..."

            html = "<html><body><table>"
            for k, v in issue.items():
                html += "<tr>"
                html += f"<th>{k}</th>"
                html += f"<td>{v}</td>"
                html += "</tr>"
            html += f"</table><hr /><p>{issue}</p></body></html>"

            message = Message(
                subject=f"User feedback: {title}",
                sender="contact@reciperadar.com",
                recipients=["feedback@reciperadar.com"],
                html=html,
            )
            message.attach("screenshot.png", "image/png", image)
            mail.send(message)
