import argparse
import datetime
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.davofeed.feed import collect_by_date

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_OUTPUT_DIR = Path.home() / "Documents"


def main():
    parser = argparse.ArgumentParser(description="Generate YouTube daily feed HTML.")
    parser.add_argument(
        "--date",
        metavar="YYYYMMDD",
        default=datetime.date.today().strftime("%Y%m%d"),
        help="Date to collect videos for (default: today)",
    )
    args = parser.parse_args()

    try:
        target = datetime.datetime.strptime(args.date, "%Y%m%d").date()
    except ValueError:
        print(f"Error: invalid date '{args.date}', expected YYYYMMDD")
        return 1

    print(f"Collecting videos for {target} ...")
    data = collect_by_date(target)

    env = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)))
    template = env.get_template("feed.html")

    output = template.render(
        date=target.strftime("%Y-%m-%d"),
        generated_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data=data,
    )

    out_path = _OUTPUT_DIR / f"{target.strftime('%Y%m%d')}.html"
    out_path.write_text(output, encoding="utf-8")

    errors = [
        (handle, reason)
        for categories in data.values()
        for info in categories.values()
        for handle, reason in info["error_handles"]
    ]
    if errors:
        print("\nFetch errors:")
        for handle, reason in errors:
            print(f"  {handle}: {reason}")

    print(f"\nDone: {out_path}")


if __name__ == "__main__":
    sys.exit(main())
