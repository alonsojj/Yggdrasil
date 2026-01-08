from crawlee.crawlers import HttpCrawler, PlaywrightCrawler, HttpCrawlingContext
from crawlee.http_clients import HttpxHttpClient, CurlImpersonateHttpClient
from crawlee.browsers import PlaywrightBrowserPlugin, BrowserPool
from crawlee.storage_clients import MemoryStorageClient
from crawlee.router import Router

storage = MemoryStorageClient()


httpx_router = Router[HttpCrawlingContext]()
curl_router = Router[HttpCrawlingContext]()
httpxCrawl = HttpCrawler(
    http_client=HttpxHttpClient(),
    storage_client=storage,
    request_handler=httpx_router,
    keep_alive=True,
    max_request_retries=1,
    use_session_pool=False,
)
curlCrawnl = HttpCrawler(
    http_client=CurlImpersonateHttpClient(),
    storage_client=storage,
    request_handler=curl_router,
)
plugin_chromium = PlaywrightBrowserPlugin(
    browser_type="chromium", max_open_pages_per_browser=1
)
plugin_firefox = PlaywrightBrowserPlugin(
    browser_type="firefox", max_open_pages_per_browser=1
)
playwrightCrawl = PlaywrightCrawler(
    browser_pool=BrowserPool(plugins=[plugin_chromium, plugin_firefox]),
    max_requests_per_crawl=10,
    storage_client=storage,
)
