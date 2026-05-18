def get_rental_data(city: str, district: str) -> dict:
    """
    Fake rental data for MVP.

    Later this can be replaced by:
    - Rental open data
    - Custom rental dataset
    - Web scraping results if legally allowed
    """
    return {
        "rental_level": "偏高",
        "studio_range": "18,000 - 28,000 元/月",
        "shared_room_range": "10,000 - 16,000 元/月",
        "summary": "此區因交通便利與商業活動密集，租金通常偏高。"
    }