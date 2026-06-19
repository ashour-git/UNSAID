CAMPAIGN_IMAGES: tuple[str, ...] = (
    "https://images.pexels.com/photos/15097440/pexels-photo-15097440/free-photo-of-luxury-fragrances-in-glass-bottles.jpeg?auto=compress&cs=tinysrgb&dpr=1&w=1200",
    "https://images.pexels.com/photos/12556542/pexels-photo-12556542.jpeg?auto=compress&cs=tinysrgb&dpr=1&w=1200",
    "https://images.pexels.com/photos/5567098/pexels-photo-5567098.jpeg?auto=compress&cs=tinysrgb&dpr=1&w=1200",
    "https://images.pexels.com/photos/4736027/pexels-photo-4736027.jpeg?auto=compress&cs=tinysrgb&dpr=1&w=1200",
    "https://images.pexels.com/photos/16266295/pexels-photo-16266295/free-photo-of-vial-of-perfume.jpeg?auto=compress&cs=tinysrgb&dpr=1&w=1200",
    "https://images.pexels.com/photos/15007560/pexels-photo-15007560/free-photo-of-close-up-of-a-perfume-in-a-bottle.jpeg?auto=compress&cs=tinysrgb&dpr=1&w=1200",
)


def campaign_image_for_index(index: int) -> str:
    return CAMPAIGN_IMAGES[index % len(CAMPAIGN_IMAGES)]
