import dataclasses


@dataclasses.dataclass(frozen=True)
class VnaSmithRow:
    label: str
    smith_rel: str
    swr_rel: str


@dataclasses.dataclass(frozen=True)
class VnaSmithSection:
    rows: list[VnaSmithRow]


def build_vna_smith_section(chart_rows: list[dict[str, str]]) -> VnaSmithSection:
    rows: list[VnaSmithRow] = []
    for row in chart_rows:
        rows.append(
            VnaSmithRow(
                label=row["label"],
                smith_rel=row["smith_rel"],
                swr_rel=row["swr_rel"],
            )
        )
    return VnaSmithSection(rows=rows)
