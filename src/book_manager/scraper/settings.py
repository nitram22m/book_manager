"""Configuración ética y de procesamiento del proyecto Scrapy."""

from book_manager.reportes import REPORTS_DIR

BOT_NAME = "book_manager"
SPIDER_MODULES = ["book_manager.scraper.spiders"]
NEWSPIDER_MODULE = "book_manager.scraper.spiders"

ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 1.5
CONCURRENT_REQUESTS = 2
CONCURRENT_REQUESTS_PER_DOMAIN = 1
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.5
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
RETRY_TIMES = 2
LOG_LEVEL = "INFO"

ITEM_PIPELINES = {
    "book_manager.scraper.pipelines.LogPipeline": 100,
    "book_manager.scraper.pipelines.FixDataPipeline": 200,
    "book_manager.scraper.pipelines.PersistencePipeline": 300,
}

FEED_FORMAT = "json"
FEED_URI = str(REPORTS_DIR / "cuspide_scraping_backup.json")
FEED_EXPORT_ENCODING = "utf-8"
