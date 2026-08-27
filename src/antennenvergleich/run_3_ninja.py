"""Generate experimental per-antenna ninja pages in parallel to antenna_generated.html."""


def main() -> None:
    from antennenvergleich.ninja_pipeline.main import main as pipeline_main

    pipeline_main()


if __name__ == "__main__":
    main()
