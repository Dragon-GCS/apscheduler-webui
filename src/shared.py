from fastui import AnyComponent
from fastui import components as c
from fastui.events import GoToEvent


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
