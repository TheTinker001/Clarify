"""Pagination helper functions."""


def get_page_slots(cur, max_pages):
    """Return a compact pagination sequence.

    If there are less than 9 pages, return every page number.
    Otherwise:
    - If the current page is in the first 4 pages, show pages 1 to 7, an ellipsis and the final page
    - If the current page is in the last 4 pages, show the first page, an ellipsis and the last 7 pages
    - If the current page is after the first 4 pages and before the last 4 pages, show the first page, an ellipsis, 2 pages on either side
    of the current page, another ellipsis and the final page
    """

    if max_pages <= 9:
        return list(range(1, max_pages + 1))
    slots = []
    if cur <= 4:
        slots = list(range(1, 8)) + ["...", max_pages]
    elif cur >= max_pages - 3:
        slots = [1, "..."] + list(range(max_pages - 6, max_pages + 1))
    else:
        slots = [1, "..."] + list(range(cur - 2, cur + 3)) + ["...", max_pages]
    return slots
