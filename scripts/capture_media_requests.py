import argparse
from urllib.parse import urlparse

import pandas as pd
from playwright.sync_api import sync_playwright


IMAGE_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
)

IMAGE_CONTENT_HINTS = (
    "image/",
    "application/octet-stream",
)


def looks_like_image(url: str, resource_type: str, content_type: str) -> bool:
    if resource_type == "image":
        return True

    parsed = urlparse(url)
    path = parsed.path.lower()
    if any(path.endswith(ext) for ext in IMAGE_EXTENSIONS):
        return True

    ctype = (content_type or "").lower()
    if "image/" in ctype:
        return True

    # Algunos CDNs devuelven octet-stream aunque el archivo sí es imagen.
    if "application/octet-stream" in ctype:
        return any(path.endswith(ext) for ext in IMAGE_EXTENSIONS)

    return False


def capture_image_requests(url: str, wait_ms: int, headless: bool) -> pd.DataFrame:
    records: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        def on_response(response) -> None:
            req = response.request
            ctype = response.headers.get("content-type", "")
            if not looks_like_image(response.url, req.resource_type, ctype):
                return

            records.append(
                {
                    "url": response.url,
                    "status": response.status,
                    "resource_type": req.resource_type,
                    "content_type": ctype,
                    "method": req.method,
                }
            )

        page.on("response", on_response)
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(wait_ms)
        browser.close()

    if not records:
        return pd.DataFrame(columns=["url", "status", "resource_type", "content_type", "method"])

    df = pd.DataFrame(records).drop_duplicates(subset=["url", "method"]).reset_index(drop=True)
    return df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Captura requests de imagen desde una URL usando Playwright.")
    parser.add_argument("--url", required=True, help="URL objetivo")
    parser.add_argument("--wait-ms", type=int, default=8000, help="Tiempo de espera para capturar requests")
    parser.add_argument(
        "--output",
        default="image_requests.csv",
        help="Archivo de salida (.csv, .xlsx o .json)",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Ejecuta con navegador visible para sitios que bloquean headless",
    )
    return parser.parse_args()


def save_output(df: pd.DataFrame, output: str) -> None:
    lower_output = output.lower()

    if lower_output.endswith(".xlsx"):
        df.to_excel(output, index=False)
    elif lower_output.endswith(".json"):
        df.to_json(output, orient="records", force_ascii=False, indent=2)
    else:
        df.to_csv(output, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    df = capture_image_requests(url=args.url, wait_ms=args.wait_ms, headless=not args.headed)
    save_output(df, args.output)

    print(f"Total requests de imagen capturados: {len(df)}")
    print(f"Archivo generado: {args.output}")

    if not df.empty:
        print("\nPrimeros resultados:")
        print(df.head(10).to_string(index=False))
    else:
        print("\nNo se detectaron requests de imagen con los filtros actuales.")


if __name__ == "__main__":
    main()
