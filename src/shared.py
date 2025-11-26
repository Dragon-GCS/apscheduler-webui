from urllib.parse import parse_qs, urlencode, urlparse
from uuid import uuid4

from fastui import AnyComponent
from fastui import components as c
from fastui.events import GoToEvent, PageEvent

Components = list[AnyComponent]


def frame_page(*components: AnyComponent) -> Components:
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
                c.Link(
                    components=[c.Text(text="Executor")],
                    on_click=GoToEvent(url="/executor"),
                    active="/executor",
                ),
                c.Link(
                    components=[c.Text(text="Log")],
                    on_click=GoToEvent(url="/log/jobs"),
                    active="startswith:/log",
                ),
            ],
        ),
        c.Page(components=list(components)),
    ]


def confirm_modal(title: str, submit_url: str) -> c.Modal:
    """
    Create a modal to be confirm this click action. Modal will be open by trigger_name which is the title of the modal.

    Args:
        title (str): The title of the modal.
        submit_url (str): The URL to submit the form to.
    Returns:
        c.Modal: The modal component.
    """
    trigger_name = "_".join(title.lower().split())
    return c.Modal(
        title=title,
        body=[
            c.ServerLoad(
                path=submit_url,
                load_trigger=PageEvent(name="confirm"),
                method="POST",
                components=[
                    c.Paragraph(text="Are you sure to perform this action?"),
                    c.Div(
                        components=[
                            c.Button(
                                text="Cancel",
                                named_style="secondary",
                                on_click=PageEvent(name=trigger_name, clear=True),
                            ),
                            c.Button(text="Confirm", on_click=PageEvent(name="confirm")),
                        ],
                        class_name="d-flex justify-content-around",
                    ),
                ],
            ),
        ],
        open_trigger=PageEvent(name=trigger_name),
    )


def reload_event(current_url: str) -> GoToEvent:
    """
    Use uuid4 to generate a unique query parameter to force the browser to reload the page,
    see https://github.com/pydantic/FastUI/issues/255
    """
    parsed_url = urlparse(current_url)
    params = {"refresh": str(uuid4())} | parse_qs(parsed_url.query)
    return GoToEvent(url=f"{parsed_url.path}?{urlencode(params, doseq=True)}")


def h_stack(*component: AnyComponent, class_name: str = "") -> c.Div:
    """
    Center components horizontally.
    """

    return c.Div(
        components=list(component),
        class_name=f"d-flex justify-content-center {class_name}",
    )


def error(description: str, title: str = "Error", status_code: int = 500) -> c.Error:
    return c.Error(
        title=title,
        description=description,
        status_code=status_code,
    )
