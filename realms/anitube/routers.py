import re
import asyncio
import httpx
import jsbeautifier
from crawlee.crawlers import HttpCrawlingContext
from crawlee import Request
from app.core.engines import httpx_router
from parsel import Selector

# Mantenha suas variáveis globais
anitube_storage = dict[str, asyncio.Future[dict[str, str | list]]]()
anitube_cached_meta = {}


def handler_error(correlation_id: str):
    if correlation_id in anitube_storage:
        anitube_storage[correlation_id].set_result({})


@httpx_router.handler("ANITUBE_PLAYLIST_META")
async def meta_handler(context: HttpCrawlingContext) -> None:
    from realms.anitube.main import ANITUBE_USER_AGENT
    response_bytes = await context.http_response.read()
    response = response_bytes.decode()
    selector = Selector(text=response)
    episodes = selector.css("div.pagAniListaContainer a::text")
    results = []
    for episode in episodes:
        name = episode.get()
        if not name:
            continue
        match = re.search(r"Episódio\s+0*(\d+)", name)
        if not match:
            continue
        num = int(match.group(1))
        results.append({"name": name, "id": f"0:{num}", "episode": num, "season": 0})
    anitube_storage[context.request.unique_key].set_result(results)


@httpx_router.handler("ANITUBE_SEARCH")
async def search_handler(context: HttpCrawlingContext) -> None:
    from realms.anitube.main import ANITUBE_USER_AGENT
    response_bytes = await context.http_response.read()
    response = response_bytes.decode()
    selector = Selector(text=response)
    try:
        aniItem = selector.css("div.aniItem a")
        results = []
        for item in aniItem:
            href = item.attrib.get("href", "")
            match = re.search(r"video/(\d+)", href)
            if not match:
                continue
            url_id = match.group(1)
            title = item.attrib.get("title", "")
            lang = item.css(".aniCC::text").get() or ""
            data = {
                "type": "movie" if lang == "Filme" else "series",
                "id": url_id,
                "name": f"{lang} - {title}".strip(" -"),
                "poster": item.css(".aniItemImg img").attrib.get("src"),
            }
            results.append(data)
            anitube_cached_meta[data["id"]] = data
        anitube_storage[context.request.unique_key].set_result(results)
    except Exception as e:
        handler_error(context.request.unique_key)


@httpx_router.handler("ANITUBE_VIDEO")
async def video_handler(context: HttpCrawlingContext) -> None:
    """
    Este handler agora lida com o novo sistema de proteção do AniTube.
    Página -> Iframe (bg.mp4) -> Redirect (302) -> API (Packer) -> Google Video
    """
    from realms.anitube.main import ANITUBE_USER_AGENT
    response_bytes = await context.http_response.read()
    response = response_bytes.decode()
    selector = Selector(text=response)

    try:
        # 1. Encontrar o link do túnel no iframe (contém bg.mp4)
        iframe_url = selector.xpath('//iframe[contains(@src, "bg.mp4")]/@src').get()
        if not iframe_url:
            # Fallback para qualquer iframe se o padrão mudar
            iframe_url = selector.css("iframe::attr(src)").get()

        if not iframe_url:
            raise ValueError("Iframe de vídeo não encontrado")

        # 2. Iniciar cliente HTTP para seguir o fluxo de proteção
        async with httpx.AsyncClient(http2=True, timeout=10) as client:
            # Passo A: Bater no Túnel para pegar o Redirect (302)
            tunnel_headers = {
                "Referer": context.request.url,
                "User-Agent": ANITUBE_USER_AGENT,
                "Sec-Fetch-Dest": "iframe",
                "Sec-Fetch-Mode": "navigate",
            }

            # follow_redirects=False para capturar a URL da API no header Location
            res_tunnel = await client.get(
                iframe_url, headers=tunnel_headers, follow_redirects=False
            )
            api_url = res_tunnel.headers.get("Location")

            if not api_url:
                # Se não houve redirect, talvez já estejamos na API?
                api_url = iframe_url if "api." in iframe_url else None

            if not api_url:
                raise ValueError("Não foi possível obter a URL da API de vídeo")

            # Passo B: Acessar a API Final e extrair o código ofuscado
            api_headers = {
                "Referer": "https://www.anitube.news/",  # Referer fixo que a API exige
                "User-Agent": ANITUBE_USER_AGENT,
            }
            res_api = await client.get(api_url, headers=api_headers)

            # Passo C: Descompactar Packer e extrair links do Google Video
            # Procuramos o bloco eval(...)
            packer_match = re.search(
                r"eval\(function\(p,a,c,k,e,d\).+?\}\(.*\)\)", res_api.text, re.DOTALL
            )

            content_to_search = res_api.text
            if packer_match:
                content_to_search = jsbeautifier.beautify(packer_match.group(0))

            # Extrair todos os links googlevideo.com
            links = re.findall(
                r'https?://[^\s"\'\\>]+googlevideo\.com[^\s"\'\\>]+', content_to_search
            )

            if not links:
                raise ValueError("Nenhum link de vídeo encontrado no player")

            # Priorizar 720p (itag=22), senão pega o primeiro disponível
            final_link = next((l for l in links if "itag=22" in l), links[0])
            final_link = final_link.replace("\\/", "/").replace("\\", "")

            title = selector.xpath("//title/text()").get() or "Vídeo AniTube"

            anitube_storage[context.request.unique_key].set_result(
                {"url": final_link, "name": title}
            )

    except Exception as e:
        print(f"Erro no handler de vídeo: {e}")
        handler_error(context.request.unique_key)


@httpx_router.handler("ANITUBE_PLAYLIST")
async def playlist_handler(context: HttpCrawlingContext) -> None:
    response_bytes = await context.http_response.read()
    response = response_bytes.decode()
    selector = Selector(text=response)
    try:
        parts = context.request.unique_key.split(":")
        correlation_id = parts[0]
        target_episode = parts[1]
        episodes = selector.css("div.pagAniListaContainer a")
        found = False
        for link in episodes:
            if link.css("::text").re(f"Episódio 0*{target_episode}"):
                href = link.attrib.get("href")
                if href:
                    request = Request.from_url(
                        url=href,
                        unique_key=correlation_id,
                        label="ANITUBE_VIDEO",
                    )
                    await context.add_requests([request])
                    found = True
                    break
        if not found:
            raise ValueError(f"Episódio {target_episode} não encontrado na lista")
    except Exception as e:
        handler_error(context.request.unique_key.split(":")[0])
