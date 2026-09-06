import pathlib, pytest
from  PIL import Image, ImageChops

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from db_bridge import DBBridge
from orm import Config, Color, Author, Sentence, Quote

BASE = pathlib.Path(__file__).parent / "baseline"
OUT = pathlib.Path(__file__).parent / "output"


@pytest.fixture
def test_bridge(tmp_path):
    def _fill_db(bridge: DBBridge):
        load_dotenv()
        with Session(bridge.engine) as session:
            session.add(Config())

            color1 = Color(
                red=217,
                green=19,
                blue=19,
            )
            color2 = Color(
                red=82,
                green=237,
                blue=43,
            )

            author1 = Author(
                id='1',
                signature='👍Test1😊',
                color=color1,
            )
            author2 = Author(
                id='2',
                signature='👾Loooooong Author 🐍',
                color=color2,
            )

            single_author_short = Quote(confirmed=True)
            single_author_long = Quote(confirmed=True)
            dialogue = Quote(confirmed=True)
            not_confirmed = Quote()

            session.add_all([
                Sentence(
                    number=0,
                    author=author1,
                    quote=single_author_short,
                    sentence="Lore ipsum"
                ),
                Sentence(
                    number=0,
                    author=author2,
                    quote=single_author_long,
                    sentence="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamc"
                ),
                Sentence(
                    number=0,
                    author=author1,
                    quote=dialogue,
                    sentence="Lorem ipsum dolor sit amet consectetur adipiscing elit."
                ),
                Sentence(
                    number=1,
                    author=author2,
                    quote=dialogue,
                    sentence="Consectetur adipiscing elit quisque faucibus ex sapien vitae."
                ),
                Sentence(
                    number=2,
                    author=author1,
                    quote=dialogue,
                    sentence="Ex sapien vitae pellentesque sem placerat in id."
                ),
                Sentence(
                    number=0,
                    author=author2,
                    quote=not_confirmed,
                    sentence="This one should work only after approve"
                ),
            ])

            session.commit()

    bridge = DBBridge(db_path=tmp_path / "test.db")
    _fill_db(bridge)

    yield bridge
    bridge.engine.dispose()

def pytest_addoption(parser):
    parser.addoption("--update-baselines", action="store_true")

def _dump(name, ref, cur, diff):
    OUT.mkdir(parents=True, exist_ok=True)
    w, h = cur.size
    sheet = Image.new("RGBA", (w * 3 + 20, h), (30, 30, 30, 255))
    sheet.paste(ref, (0, 0))
    sheet.paste(cur, (w + 10, 0))
    if diff:
        sheet.paste(diff, (2 * w + 20, 0))
    sheet.save(OUT / f"{name}.png")

@pytest.fixture
def assert_image(request):
    def _cmp(img, name, tolerance=0.002, threshold=8):
        base = BASE / f"{name}.png"
        if request.config.getoption("--update-baselines"):
            base.parent.mkdir(parents=True, exist_ok=True)
            img.save(base)
            pytest.skip(f"base line updated: {name}")
        if not base.exists():
            pytest.fail(f"no base image for: {name}; run pytest --update-baselines")

        ref, cur = Image.open(base).convert("RGBA"), img.convert("RGBA")
        if ref.size != cur.size:
            pytest.fail(f"{name}: size {cur.size} != baseline {ref.size}")

        diff = ImageChops.difference(ref, cur)
        mask = diff.convert("L").point(lambda p: 255 if p > threshold else 0)
        frac = sum(mask.point(bool).getdata()) / (ref.width * ref.height)
        if frac > tolerance:
            _dump(name, ref, cur, diff)
            pytest.fail(f"{name}: {frac:.2%} of pixels changed (limit {tolerance:.2%})")
    return _cmp