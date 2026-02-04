from momo import parse_momox_page


def test_parse_momox_page_extracts_title_and_price():
    html = """
    <html>
      <body>
        <div class="product-title">Le Petit Prince</div>
        <div class="searchresult-price">4,99 €</div>
      </body>
    </html>
    """
    title, price = parse_momox_page(html)
    assert title == "Le Petit Prince"
    assert price == "4,99 €"


def test_parse_momox_page_missing_price():
    html = """
    <html>
      <body>
        <div class="product-title">Le Petit Prince</div>
      </body>
    </html>
    """
    title, price = parse_momox_page(html)
    assert title == "Le Petit Prince"
    assert price is None


def test_parse_momox_page_missing_title():
    html = """
    <html>
      <body>
        <div class="searchresult-price">4,99 €</div>
      </body>
    </html>
    """
    title, price = parse_momox_page(html)
    assert title is None
    assert price == "4,99 €"
