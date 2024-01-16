from flask_mail import Message


class Feedback:
    __tablename__ = "feedback"

    @staticmethod
    def distribute(issue, image):
        from reciperadar import app, mail

        with app.app_context():
            description = issue.pop("issue") or "(empty)"
            title = description if len(description) < 25 else f"{description[:25]}..."

            html = "<html><body><table>"
            for k, v in issue.items():
                html += "<tr>"
                html += f"<th>{k}</th>"
                html += f"<td>{v}</td>"
                html += "</tr>"
            html += f"</table><hr /><p>{description}</p></body></html>"

            message = Message(
                subject=f"User feedback: {title}",
                sender="contact@reciperadar.com",
                recipients=["feedback@reciperadar.com"],
                html=html,
            )
            message.attach("screenshot.png", "image/png", image)
            mail.send(message)
