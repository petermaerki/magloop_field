import dataclasses
import enum
import pathlib

from antennenvergleich import datatypes

from . import renderer_html


class EnumCategory(enum.StrEnum):
    BRAND = "Brand"
    NAME = "Name"
    LOCATION = "Location"
    BAND = "Band"


@dataclasses.dataclass(frozen=True, repr=True)
class AntennaJoin:
    directory: pathlib.Path
    brand: str
    name: str
    location: str
    band: str
    color: str

    def value(self, category: EnumCategory) -> str:
        assert isinstance(category, EnumCategory)

        if category == EnumCategory.BRAND:
            return self.brand
        if category == EnumCategory.NAME:
            return self.name
        if category == EnumCategory.LOCATION:
            return self.location
        assert category == EnumCategory.BAND
        return self.band

    @property
    def text(self) -> str:
        return " / ".join(
            [f"{v:<20s}" for v in (self.band, self.name, self.location, self.band)]
        )


def get_antenna_joins(
    antenna_entries: list[datatypes.AntennaPlusDirectory],
) -> list[AntennaJoin]:
    assert isinstance(antenna_entries, list)

    color_map = build_color_map_from_entries(antenna_entries)

    antenna_joins: list[AntennaJoin] = []
    for antenna_entry in antenna_entries:
        antenna = antenna_entry.antenna
        color = color_map[renderer_html._antenna_label(antenna)]
        assert isinstance(antenna.bands, list)
        for band in antenna.bands:
            band_str = renderer_html._band_from_frequency(f_Hz=band.f_Hz.value)
            print(antenna.selection_location)
            antenna_joins.append(
                AntennaJoin(
                    directory=antenna_entry.directory,
                    brand=antenna.selection_brand,
                    name=antenna.selection_name,
                    location=antenna.selection_location,
                    band=band_str,
                    color=color,
                )
            )
    return antenna_joins


def build_color_map_from_entries(
    antenna_entries: list[datatypes.AntennaPlusDirectory],
) -> dict[str, str]:
    return renderer_html.build_antenna_color_map(
        [entry.antenna for entry in antenna_entries]
    )


class CheckboxState(enum.StrEnum):
    CHECKED = "x"
    UNCHECKED = "/"
    INVISIBLE = "_"


@dataclasses.dataclass(slots=True)
class Checkbox:
    name: str
    state: CheckboxState = CheckboxState.CHECKED

    def reset(self) -> None:
        self.state = CheckboxState.CHECKED

    @property
    def text(self) -> None:
        return f"{self.name}[{self.state.value}]"

    @property
    def checked(self) -> bool:
        return self.state == CheckboxState.CHECKED

    def set_checked(self, checked: bool) -> None:
        self.state = CheckboxState.CHECKED if checked else CheckboxState.UNCHECKED

    def set_visible(self, visible: bool) -> None:
        if visible:
            if self.state == CheckboxState.INVISIBLE:
                self.state = CheckboxState.UNCHECKED
            return
        self.state = CheckboxState.INVISIBLE


class CategoryStats:
    def __init__(
        self,
        category: EnumCategory,
        antenna_filters: list[AntennaJoin],
    ) -> None:
        self.category = category

        values = {f.value(category=category) for f in antenna_filters}
        self.checkboxes: list[Checkbox] = [Checkbox(c) for c in sorted(values)]

    def reset(self) -> None:
        for c in self.checkboxes:
            c.reset()

    def is_checkable(self, antenna_join: AntennaJoin) -> None:
        return antenna_join.value(category=self.category) in self.checked

    def dump(self) -> None:
        values = [c.text for c in self.checkboxes]
        print(f"    {self.category.name}: {' '.join(values)}")

    def updated_checked(self, set_checked: set[str]) -> None:
        for checkbox in self.checkboxes:
            checked = checkbox.name in set_checked
            checkbox.set_checked(checked=checked)

    @property
    def set_checked(self) -> set[str]:
        return {c.name for c in self.checkboxes if c.state == CheckboxState.CHECKED}

    def filter(self, antenna_joins: list[AntennaJoin]) -> list[AntennaJoin]:
        set_checked = self.set_checked
        return [
            aj
            for aj in antenna_joins
            if aj.value(category=self.category) in set_checked
        ]


class Filter:
    """
    There are checkboxes for each FilterLevel.
    ALL possible checkboxes exist!
    If a checkbox will not influence the result it will be set invisible.
    A checkbox may be checked or unchecked.
    """

    def __init__(self, antenna_joins: list[AntennaJoin]) -> None:
        assert isinstance(antenna_joins, list)

        self.antenna_joins = antenna_joins

        self.category_stats: list[CategoryStats] = [
            CategoryStats(EnumCategory.BRAND, self.antenna_joins),
            CategoryStats(EnumCategory.NAME, self.antenna_joins),
            CategoryStats(EnumCategory.LOCATION, self.antenna_joins),
            CategoryStats(EnumCategory.BAND, self.antenna_joins),
        ]

        self.reset()

    def reset(self) -> None:
        for level in self.category_stats:
            level.reset()

    def _find_category(self, category: EnumCategory) -> CategoryStats:
        assert isinstance(category, EnumCategory)
        for l in self.category_stats:
            if l.category == category:
                return l
        else:
            raise ValueError(f"Programming error: {category.level.name} not found!")

    def update_level(self, category: EnumCategory, set_checked: set[str]) -> None:
        """
        Given level BRAND with all selected brands: All other Levels:
        """
        assert isinstance(set_checked, set)

        # Initial pass: Set the checkboxes of the current category
        current_category = self._find_category(category=category)
        current_category.updated_checked(set_checked=set_checked)

        def aj_dump():
            for aj in aj_remaining:
                print(aj.text)

        # First pass: Collect remaining antenna_joins for current category
        aj_remaining = self.antenna_joins.copy()
        print(f" Start:      aj_remaining={len(aj_remaining)}")
        set_checked = current_category.set_checked

        aj_remaining = [
            aj
            for aj in aj_remaining
            if aj.value(category=current_category.category) in set_checked
        ]

        print(f" First pass: aj_remaining={len(aj_remaining)}")

        for c in self.category_stats:
            set_category_checked = c.set_checked
            aj_remaining = [
                aj
                for aj in aj_remaining
                if aj.value(category=c.category) in set_category_checked
            ]

        print(f" Second pass: aj_remaining={len(aj_remaining)}")

        # Third pass: Make checkboxes invisible
        for c in self.category_stats:
            if c.category == category:
                continue

            set_remaining = {aj.value(category=c.category) for aj in aj_remaining}
            for checkbox in c.checkboxes:
                visible = checkbox.name in set_remaining
                checkbox.set_visible(visible=visible)

    @property
    def aj_filtered(self) -> list[AntennaJoin]:
        aj_remaining = self.antenna_joins.copy()
        for c in self.category_stats:
            aj_remaining = c.filter(antenna_joins=aj_remaining)
        return aj_remaining

    @property
    def set_antenna_dir(self) -> set[pathlib.Path]:
        aj_filtered = self.aj_filtered
        return {aj.directory for aj in aj_filtered}

    def dump(self) -> None:
        print("---------------")
        for level in self.category_stats:
            level.dump()
