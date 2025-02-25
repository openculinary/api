from flask.templating import render_template
from flask_mail import Message


class Feedback:

    @staticmethod
    def _construct(subject, sender, recipients, html):
        return Message(subject=subject, sender=sender, recipients=recipients, html=html)

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

            message = Feedback._construct(
                subject=f"User feedback: {title}",
                sender="contact@reciperadar.com",
                recipients=["feedback@reciperadar.com"],
                html=html,
            )
            message.attach("screenshot.png", "image/png", image)
            mail.send(message)

    @staticmethod
    def report(recipe_id, report_type, result_index, report_data):
        from reciperadar import app, mail

        with app.app_context():
            template = f"problem-report/{report_type.replace('-', '_')}.html"
            template_context = {
                **report_data,
                "recipe_id": recipe_id,
                "report_type": report_type,
                "result_index": result_index,
            }
            html = render_template(template, **template_context)

            message = Feedback._construct(
                subject=f"Content report: {report_type}: {recipe_id}",
                sender="contact@reciperadar.com",
                recipients=["content-reports@reciperadar.com"],
                html=html,
            )
            mail.send(message)
