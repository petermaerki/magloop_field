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

    antenna_joins: list[AntennaJoin] = []
    for antenna_entry in antenna_entries:
        antenna = antenna_entry.antenna
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
                )
            )
    return antenna_joins


class CheckboxState(enum.StrEnum):
    CHECKED = "x"
    UNCHECKED = "/"
    INVISIBLE = "_"


@dataclasses.dataclass(slots=True)
class Checkbox:
    name: str
    state: CheckboxState = CheckboxState.CHECKED
    # TODO Peter
    # Remove state
    # Add: checked: bool
    # Add: grayed: bool

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

    def option_has_matches(self, category: EnumCategory, option_name: str) -> bool:
        for antenna_join in self.antenna_joins:
            if antenna_join.value(category=category) != option_name:
                continue

            is_match = True
            for category_stat in self.category_stats:
                if category_stat.category == category:
                    continue
                if (
                    antenna_join.value(category=category_stat.category)
                    not in category_stat.set_checked
                ):
                    is_match = False
                    break

            if is_match:
                return True
        return False

    def find_category(self, category: EnumCategory) -> CategoryStats:
        assert isinstance(category, EnumCategory)
        for l in self.category_stats:
            if l.category == category:
                return l
        else:
            raise ValueError(f"Programming error: {category.level.name} not found!")
    @property
    def set_antenna_dir(self) -> set[pathlib.Path]:
        aj_remaining = self.antenna_joins.copy()
        for c in self.category_stats:
            aj_remaining = c.filter(antenna_joins=aj_remaining)
        return {aj.directory for aj in aj_remaining}

    def dump(self) -> None:
        print("---------------")
        for level in self.category_stats:
            level.dump()
