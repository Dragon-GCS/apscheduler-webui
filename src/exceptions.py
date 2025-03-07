class InvalidTrigger(Exception):
    def __init__(self, trigger: str) -> None:
        msg = f"Invalid trigger: {trigger}(type: {type(trigger)}"
        super().__init__(msg)


class InvalidJobStore(Exception):
    def __init__(self, store: str) -> None:
        msg = f"Invalid job store: {store}"
        super().__init__(msg)


class InvalidExecutor(Exception):
    def __init__(self, executor: str) -> None:
        msg = f"Executor type {executor} not supported"
        super().__init__(msg)


class InvalidAction(Exception):
    def __init__(self, action: str) -> None:
        msg = f"Invalid action: {action}"
        super().__init__(msg)
