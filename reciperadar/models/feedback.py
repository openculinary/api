from flask_mail import Message


class Feedback:
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

    @staticmethod
    def report(recipe_id, report_type, result_index, report_data):
        from reciperadar import app, mail

        with app.app_context():
            msg = f"Please inspect {recipe_id!r} at {result_index} for {report_type}"
            html = f"<html><body>{msg}</body></html>"

            # TODO: add per-report-type content inspection instructions
            #
            # 1. removal requests:
            #   a) verify the identity of the requestor (email domain, policy hyperlink, or presence of HTML noindex for the relevant recipe(s)).
            #   b) confirm that the removal request is valid.
            #   c) if either check (a) or (b) fails, stop here and do not process the request.
            #   d) remove the requested recipe(s) from the database and search index, then generate an updated current-backup.
            #   e) if the request was made by email, then reply with confirmation that the removal has been processed.
            #
            # 2. unsafe content:
            #   a) check that the domain name is a recipe domain already contained within the reciperadar database with indexing enabled.
            #   b) if check (a) fails, do nothing and stop processing this request.
            #   b) if check (a) succeeds, remove the recipe from the database and search index, then generate an updated current-backup.
            #
            # 3. corrections:
            #   a) open the relevant recipe search result in the application.
            #   b) confirm that the reported mistake exists in the recipe, and inspect for any other apparent problems.
            #   c) file a bugreport against the 'crawler' microservice with details of the expected and found results.

            message = Message(
                subject=f"Content report: {report_type}: {recipe_id}",
                sender="contact@reciperadar.com",
                recipients=["content-reports@reciperadar.com"],
                html=html,
            )
            mail.send(message)
