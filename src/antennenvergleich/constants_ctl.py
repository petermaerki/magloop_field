import dataclasses


@dataclasses.dataclass(repr=True)
class Ctl:
    """
    This is the interface between the http parameters '?draft=1' and the python logic.
    """

    draft: bool = True
    detailed: bool = True

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

        self.draft = get_bool("ctl_draft")
        self.detailed = get_bool("ctl_detailed")

        print(f"{self.draft=}")


CTL = Ctl(draft=False, detailed=False)
