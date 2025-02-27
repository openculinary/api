from typing import Literal, ReadOnly, Required, TypedDict

from flask.templating import render_template
from flask_mail import Message

from reciperadar.models.recipes import Recipe


class ProblemReport(TypedDict):
    recipe_id: Required[ReadOnly[str]]
    report_type: Required[
        ReadOnly[
            Literal[
                "removal-request",
                "unsafe-content",
                "correction",
            ]
        ]
    ]
    result_index: Required[ReadOnly[int]]


class RemovalRequest(ProblemReport):
    content_owner_email: Required[ReadOnly[str | None]]
    content_reuse_policy: Required[ReadOnly[str | None]]
    content_noindex_directive: Required[ReadOnly[bool]]


class UnsafeContent(ProblemReport):
    pass


class Correction(ProblemReport):
    content_expected: Required[ReadOnly[str]]
    content_found: Required[ReadOnly[str]]


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
    def register_report(recipe: Recipe, report: ProblemReport) -> None:
        from reciperadar import app, mail

        with app.app_context():
            report_type = report["report_type"]
            template = f"problem-report/{report_type.replace('-', '_')}.html"
            html = render_template(template, recipe=recipe, report=report)

            message = Feedback._construct(
                subject=f"Content report: {report_type}: {recipe.id}",
                sender="contact@reciperadar.com",
                recipients=["content-reports@reciperadar.com"],
                html=html,
            )
            mail.send(message)
