import dataclasses


@dataclasses.dataclass(frozen=True)
class VnaFileListRow:
    file_name: str
    f0_mhz: str
    bswr_khz: str
    alpha_db: str
    tau_ns: str
    swr_min: str
    eta_swr_ant: str


@dataclasses.dataclass(frozen=True)
class VnaFileListSection:
    rows: list[VnaFileListRow]


def _fmt(value: object, decimals: int | None) -> str:
    if value is None:
        return "-"
    if isinstance(value, (int, float)):
        if decimals is None:
            return f"{value:.0f}"
        return f"{value:.{decimals}f}"
    return str(value)


def build_vna_filelist_section(
    values_rows: list[dict[str, object]],
) -> VnaFileListSection:
    rows: list[VnaFileListRow] = []
    for row in values_rows:
        rows.append(
            VnaFileListRow(
                file_name=str(row.get("file_name") or "-"),
                f0_mhz=_fmt(row.get("f0_mhz"), 3),
                bswr_khz=_fmt(row.get("bswr_khz"), 1),
                alpha_db=_fmt(row.get("alpha_db"), 3),
                tau_ns=_fmt(row.get("tau_ns"), 2),
                swr_min=_fmt(row.get("swr_min"), 2),
                eta_swr_ant=_fmt(row.get("eta_swr_ant"), 3),
            )
        )

    return VnaFileListSection(rows=rows)
