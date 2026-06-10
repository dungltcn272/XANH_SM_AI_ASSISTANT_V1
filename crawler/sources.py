SOURCE_PROFILES = {
    "main_site": {
        "base_url": "https://www.greensm.com/vn-vi/",
        "registry": "db:crawl_sources",
        "seed_file": "crawler/urls.json",
        "output_strategy": "by_url_category",
        "default_output_dir": "data/user",
    },
    "platform": {
        "base_url": "https://platform.greensm.com/VN-vi",
        "registry": "db:crawl_sources",
        "output_strategy": "platform_markdown",
        "default_output_dir": "data/vehicle",
    },
    "platform_pdf": {
        "registry": "db:crawl_sources",
        "source_type": "pdf",
        "output_strategy": "pdf_markdown",
        "default_output_dir": "data/vehicle",
    },
    "overview": {
        "registry": "generated",
        "output_strategy": "catalog_markdown",
        "default_output_dir": "data/overview",
    },
}
