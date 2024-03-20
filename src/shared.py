from fastui import AnyComponent
from fastui import components as c
from fastui.events import GoToEvent, PageEvent


def frame_page(*components: AnyComponent) -> list[AnyComponent]:
    return [
        c.Navbar(
            title="Scheduler",
            title_event=GoToEvent(url="/"),
            start_links=[
                c.Link(components=[c.Text(text="Jobs")], on_click=GoToEvent(url="/"), active="/"),
                c.Link(
                    components=[c.Text(text="Store")],
                    on_click=GoToEvent(url="/store"),
                    active="/store",
                ),
            ],
        ),
        c.Page(components=list(components)),
    ]


def confirm_modal(
    title: str, modal_name: str, submit_url: str, submit_trigger_name: str
) -> c.Modal:
    """
    Create a modal with a confirm button and a cancel button. The modal is opened by the
    `modal_name` event and the submit button is triggered by the `submit_trigger_name` event.

    Args:
        title (str): The title of the modal.
        modal_name (str): The name of the event that opens the modal.
        submit_url (str): The URL to submit the form to.
        submit_trigger_name (str): The name of the event that triggers the form submission.
    Returns:
        c.Modal: The modal component.
    """
    return c.Modal(
        title=title,
        body=[
            c.Paragraph(text="Are you sure to perform this action?"),
            c.Form(
                form_fields=[],
                footer=[],
                submit_url=submit_url,
                submit_trigger=PageEvent(name=submit_trigger_name),
            ),
        ],
        footer=[
            c.Button(
                text="Cancel",
                named_style="secondary",
                on_click=PageEvent(name=modal_name, clear=True),
            ),
            c.Button(
                text="Confirm",
                named_style="warning",
                on_click=PageEvent(name=submit_trigger_name),
            ),
        ],
        open_trigger=PageEvent(name=modal_name),
    )
