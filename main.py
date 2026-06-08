import datetime
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.davofeed.feed import collect_by_date

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_OUTPUT_DIR = Path.home() / "Documents"


def main():
    yesterday = datetime.date.today() - datetime.timedelta(days=1)

    print(f"Collecting videos for {yesterday} ...")
    data = collect_by_date(yesterday)

    env = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)))
    template = env.get_template("feed.html")

    output = template.render(
        date=yesterday.strftime("%Y-%m-%d"),
        generated_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data=data,
    )

    out_path = _OUTPUT_DIR / f"{yesterday.strftime('%Y%m%d')}.html"
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
