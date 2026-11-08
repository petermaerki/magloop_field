import dataclasses


@dataclasses.dataclass(repr=True)
class Ctl:
    """
    This is the interface between the http parameters '?draft=1' and the python logic.
    """

    ctl_draft: bool = True
    ctl_detailed: bool = True

    def load_from_url_params(self, params: dict[str, str]) -> None:
        """
        loop.html?ctl_draft=1&ctl_detailed=x

        ==>

        params = {
            "ctl_draft": "1",
            "ctl_detailed": "x",
        }
        """

        def get_bool(param: str) -> bool:
            text = params.get(param, "0")
            return text == "1"

        self.ctl_draft = get_bool("ctl_draft")
        self.ctl_detailed = get_bool("ctl_detailed")


CTL = Ctl(ctl_draft=False, ctl_detailed=False)
