import dataclasses
import enum
import pathlib

from antennenvergleich import datatypes

from . import renderer_compare_html


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
            band_str = renderer_compare_html._band_from_frequency(f_Hz=band.f_Hz.value)
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


@dataclasses.dataclass(slots=True)
class Checkbox:
    name: str
    checked: bool = True
    greyed: bool = False
    element_input: object | None = None
    element_label: object | None = None

    def reset(self) -> None:
        self.checked = True
        self.greyed = False
        self._apply_dom_state()

    def bind_dom(self, element_label: object, element_input: object) -> None:
        self.element_label = element_label
        self.element_input = element_input
        self._apply_dom_state()

    @property
    def text(self) -> None:
        checked_state = "x" if self.checked else "/"
        grey_state = "G" if self.greyed else "N"
        return f"{self.name}[{checked_state}{grey_state}]"

    def set_checked(self, checked: bool) -> None:
        self.checked = checked
        self._apply_dom_state()

    def set_greyed(self, greyed: bool) -> None:
        self.greyed = greyed
        self._apply_dom_state()

    def _apply_dom_state(self) -> None:
        if self.element_input is not None:
            self.element_input.checked = self.checked

        if self.element_label is not None:
            if self.greyed:
                self.element_label.classList.add("filter-option-empty")
            else:
                self.element_label.classList.remove("filter-option-empty")


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

    def find_checkbox(self, name: str) -> Checkbox:
        for checkbox in self.checkboxes:
            if checkbox.name == name:
                return checkbox
        raise ValueError(
            f"Programming error: checkbox '{name}' not found in {self.category.name}"
        )

    @property
    def set_checked(self) -> set[str]:
        return {c.name for c in self.checkboxes if c.checked}

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
        self.update_grey_states()

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

    def update_grey_states(self) -> None:
        for category_stat in self.category_stats:
            category = category_stat.category
            for checkbox in category_stat.checkboxes:
                has_match = self.option_has_matches(category, checkbox.name)
                checkbox.set_greyed(not has_match)

    def find_category(self, category: EnumCategory) -> CategoryStats:
        assert isinstance(category, EnumCategory)
        for category_stat in self.category_stats:
            if category_stat.category == category:
                return category_stat
        raise ValueError(f"Programming error: {category.name} not found")

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
