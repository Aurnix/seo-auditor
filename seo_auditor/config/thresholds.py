"""SEO rule thresholds for issue detection."""
from dataclasses import dataclass


@dataclass(frozen=True)
class TitleThresholds:
    min_length: int = 30
    max_length: int = 60
    optimal_min: int = 50
    optimal_max: int = 60
    max_pixel_width: int = 600


@dataclass(frozen=True)
class MetaDescriptionThresholds:
    min_length: int = 70
    max_length: int = 160
    optimal_min: int = 120
    optimal_max: int = 155
    max_pixel_width: int = 920


@dataclass(frozen=True)
class HeadingThresholds:
    h1_min_length: int = 20
    h1_max_length: int = 70
    max_h1_count: int = 1
    max_h2_count: int = 15


@dataclass(frozen=True)
class ContentThresholds:
    thin_content_words: int = 300
    low_content_words: int = 500
    optimal_min_words: int = 800
    optimal_max_words: int = 2500


@dataclass(frozen=True)
class LinkThresholds:
    max_links_per_page: int = 100
    min_internal_links: int = 3
    max_crawl_depth: int = 4
    orphan_page_threshold: int = 1


@dataclass(frozen=True)
class ImageThresholds:
    max_file_size_kb: int = 200
    min_alt_text_length: int = 5
    max_alt_text_length: int = 125


@dataclass(frozen=True)
class RedirectThresholds:
    max_redirect_chain_length: int = 2
    redirect_chain_warning: int = 1


@dataclass(frozen=True)
class GSCThresholds:
    low_ctr_threshold: float = 0.02
    high_impressions_threshold: int = 100
    position_opportunity_min: float = 4.0
    position_opportunity_max: float = 20.0
    significant_clicks: int = 10


@dataclass
class SEOThresholds:
    title: TitleThresholds = None
    meta_description: MetaDescriptionThresholds = None
    heading: HeadingThresholds = None
    content: ContentThresholds = None
    link: LinkThresholds = None
    image: ImageThresholds = None
    redirect: RedirectThresholds = None
    gsc: GSCThresholds = None
    
    def __post_init__(self):
        self.title = self.title or TitleThresholds()
        self.meta_description = self.meta_description or MetaDescriptionThresholds()
        self.heading = self.heading or HeadingThresholds()
        self.content = self.content or ContentThresholds()
        self.link = self.link or LinkThresholds()
        self.image = self.image or ImageThresholds()
        self.redirect = self.redirect or RedirectThresholds()
        self.gsc = self.gsc or GSCThresholds()


thresholds = SEOThresholds()
