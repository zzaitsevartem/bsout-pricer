# Парсер Профи (siriust.ru) — детальный план

## 1. Общая информация

| Поле | Значение |
|------|----------|
| **Магазин** | ПРОФИ |
| **URL** | https://siriust.ru |
| **CMS** | CS-Cart (определено по `dispatch` в URL, структуре HTML) |
| **Язык** | Русский |
| **Валюта** | RUB |
| **Типы цен** | Розница (retail), Опт (wholesale) |
| **Класс парсера** | `ProfiParser` |
| **store_slug** | `profi` |
| **store_name** | Профи |

## 2. URL-схемы

### 2.1 Категории

```
# SEO-friendly URL (human-readable)
/{category-slug}/
/{category-slug}/{subcategory-slug}/
/{category-slug}/{subcategory-slug}/{subsubcategory-slug}/

# CS-Cart internal URL (содержит category_id)
index.php?dispatch=categories.view&category_id={id}

# Примеры SEO:
/zapchasti-dlya-sotovyh/
/zapchasti-dlya-sotovyh/zapchasti-dlya-samsung/displei/
/zapchasti-dlya-apple-i-psp/zapchasti-dlya-apple-iphone/displei-incell-dlya-iphone/
```

### 2.2 Товар

```
# SEO-friendly
/{category-path}/{product-slug}/

# CS-Cart internal
index.php?dispatch=products.view&product_id={id}
```

### 2.3 Поиск

```
# HTML-страница результатов
?dispatch=products.search&q={query}&subcats=Y

# Пример:
?dispatch=products.search&q=дисплей+samsung&subcats=Y
```

### 2.4 Фильтры категории (CS-Cart "features")

```
# Фильтр по характеристикам
?features_hash={hash}

# Пример:
?features_hash=120-130-140
```

## 3. Структура данных товара

| Поле | Источник | Пример |
|------|----------|--------|
| `external_id` | КОД товара на странице | `М12345` |
| `name` | Заголовок товара (h1) | `Дисплей Samsung Galaxy S22 Ultra` |
| `price` | Розничная цена | `4500.00` |
| `old_price` | Старая цена (если есть скидка) | `5200.00` |
| `wholesale_price` | Оптовая цена (доп. поле) | `3800.00` |
| `currency` | RUB | `RUB` |
| `in_stock` | Статус наличия | `true` / `false` |
| `category` | Хлебные крошки (breadcrumbs) | `Запчасти для сотовых -> Запчасти для Samsung -> Дисплеи` |
| `description` | Блок описания товара | HTML-описание |
| `image_url` | URL первого изображения | `https://siriust.ru/images/.../photo.jpg` |
| `product_url` | Полный URL товара | `https://siriust.ru/.../displey-samsung-s22/` |

## 4. CSS-селекторы (CS-Cart по умолчанию)

CS-Cart использует предсказуемую HTML-структуру. Ниже — селекторы для стандартной темы.

### 4.1 Страница категории/поиска (список товаров)

```python
SELECTORS = {
    # Карточка товара в списке
    "product_card": "div.ty-grid-list__item",
    # или "div.ty-column3",
    
    # Название товара в списке
    "product_name": "a.product-title",
    # или "a.ty-product-list__name",
    
    # Цена на странице списка
    "product_price": "span.ty-price-num",
    # Старая цена
    "old_price": "span.ty-list-price",
    
    # Ссылка на товар
    "product_link": "a.product-title",
    
    # Изображение
    "product_image": "img.ty-pict",
    
    # Пагинация — ссылка на следующую страницу
    "next_page": "a.ty-pagination__next",
    
    # Количество страниц
    "total_pages": "span.ty-pagination__items",
}
```

### 4.2 Страница товара (детальная)

```python
PRODUCT_SELECTORS = {
    # Заголовок
    "title": "h1.ty-product-block-title",
    # или "h1[itemprop='name']",
    
    # Цена розничная
    "price": "span.ty-price-num",
    # или "span[itemprop='price']",
    
    # Старая цена
    "old_price": "span.ty-list-price",
    # или "span.ty-strike",
    
    # Код товара (external_id)
    "sku": "span.ty-sku-item__code",
    # или "span.sku-code",
    
    # Наличие
    "in_stock": "span.ty-qty-in-stock",
    # или "span.in-stock",
    
    # Изображение
    "main_image": "img.ty-product-img__pic",
    # или "a.cm-image-previewer img",
    
    # Описание
    "description": "div.ty-wysiwyg-content",
    # или "div.product-description",
    
    # Бренд/производитель
    "brand": "a.ty-features-list__a",
    
    # Хлебные крошки
    "breadcrumbs": "div.ty-breadcrumbs",
}
```

### 4.3 Поиск

```python
SEARCH_SELECTORS = {
    # Поле ввода поиска
    "search_input": "input#search_input",
    
    # Результаты — те же карточки, что и в категории
    "results": SELECTORS["product_card"],
    
    # Сообщение "ничего не найдено"
    "no_results": "div.ty-no-items",
    
    # Количество результатов
    "results_count": "span.ty-search-found",
}
```

## 5. План реализации парсера

### Этап 1: Базовый HTTP-клиент

```python
class ProfiParser(Parser):
    store_slug = "profi"
    store_name = "Профи"
    base_url = "https://siriust.ru"
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "User-Agent": random.choice(USER_AGENTS),
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            },
            timeout=15.0,
            follow_redirects=True,
        )
```

### Этап 2: Метод `search(query)`

```python
async def search(self, query: str) -> list[ProductData]:
    """
    Поиск товаров по строке запроса.
    URL: ?dispatch=products.search&q={query}&subcats=Y&page={page}
    """
    results = []
    page = 1
    
    while True:
        params = {
            "dispatch": "products.search",
            "q": query,
            "subcats": "Y",
            "page": page,
        }
        response = await self._safe_request("GET", params=params)
        soup = BeautifulSoup(response.text, "lxml")
        
        # Парсим карточки товаров
        cards = soup.select(SELECTORS["product_card"])
        if not cards:
            break
        
        for card in cards:
            product = self._parse_product_card(card)
            if product:
                results.append(product)
        
        # Проверяем пагинацию
        if not self._has_next_page(soup):
            break
        page += 1
    
    return results
```

### Этап 3: Метод `parse_product(url)`

```python
async def parse_product(self, url: str) -> ProductData | None:
    """
    Парсинг детальной страницы товара.
    URL: /{category-path}/{product-slug}/
    или: index.php?dispatch=products.view&product_id={id}
    """
    response = await self._safe_request("GET", url=url)
    soup = BeautifulSoup(response.text, "lxml")
    
    # Извлекаем поля
    name = self._get_text(soup, PRODUCT_SELECTORS["title"])
    price = self._parse_price(soup, PRODUCT_SELECTORS["price"])
    old_price = self._parse_price(soup, PRODUCT_SELECTORS["old_price"])
    sku = self._get_text(soup, PRODUCT_SELECTORS["sku"])
    in_stock = self._check_in_stock(soup)
    image_url = self._get_image_url(soup, PRODUCT_SELECTORS["main_image"])
    description = self._get_html(soup, PRODUCT_SELECTORS["description"])
    breadcrumbs = self._get_breadcrumbs(soup)
    
    return ProductData(
        external_id=sku or self._extract_id_from_url(url),
        name=name,
        price=price or Decimal("0"),
        old_price=old_price,
        currency="RUB",
        in_stock=in_stock,
        category=breadcrumbs,
        description=description,
        image_url=image_url,
        product_url=url,
    )
```

### Этап 4: Метод `update_catalog()`

```python
async def update_catalog(self) -> list[ProductData]:
    """
    Обход всего каталога: категории → страницы → товары.
    """
    # Шаг 1: Получить список всех категорий
    categories = await self._get_categories()
    
    # Шаг 2: Для каждой категории обойти страницы товаров
    all_products = []
    for category_url in categories:
        products = await self._parse_category_page(category_url)
        all_products.extend(products)
    
    return all_products

async def _get_categories(self) -> list[str]:
    """
    Извлечение всех категорий из главного меню.
    """
    response = await self._safe_request("GET", url="/")
    soup = BeautifulSoup(response.text, "lxml")
    
    categories = []
    # CS-Cart хранит меню в div.top-menu или ul.menu-list
    for link in soup.select("div.ty-menu__items a.ty-menu__item-link"):
        href = link.get("href")
        if href and not href.startswith("#") and href != "/":
            categories.append(href)
    
    return categories
```

### Этап 5: Вспомогательные методы

```python
async def _safe_request(self, method: str, url: str | None = None, params: dict | None = None):
    """Безопасный запрос с retry и exponential backoff."""
    for attempt in range(3):
        try:
            if url:
                response = await self.client.get(url, params=params)
            else:
                response = await self.client.get(self.base_url, params=params)
            response.raise_for_status()
            return response
        except httpx.HTTPError as e:
            if attempt == 2:
                raise ParserConnectionError(f"Failed after 3 retries: {e}")
            await asyncio.sleep(2 ** attempt)

def _parse_price(self, soup: BeautifulSoup, selector: str) -> Decimal | None:
    """Парсинг цены из HTML. Пример: '4 500 ₽' → Decimal('4500.00')."""
    element = soup.select_one(selector)
    if not element:
        return None
    text = element.get_text(strip=True)
    # Удаляем всё кроме цифр, точки и запятой
    text = re.sub(r'[^\d.,]', '', text)
    text = text.replace(' ', '').replace(',', '.')
    try:
        return Decimal(text)
    except:
        return None

def _check_in_stock(self, soup: BeautifulSoup) -> bool:
    """Проверка наличия товара."""
    # CS-Cart: span.ty-qty-in-stock или div.stock-status
    in_stock = soup.select_one(PRODUCT_SELECTORS["in_stock"])
    out_of_stock = soup.select_one("span.ty-qty-out-of-stock")
    if out_of_stock:
        return False
    return bool(in_stock)

def _get_breadcrumbs(self, soup: BeautifulSoup) -> str | None:
    """Извлечение хлебных крошек."""
    breadcrumbs = soup.select_one("div.ty-breadcrumbs")
    if not breadcrumbs:
        return None
    items = breadcrumbs.select("a", "span")
    return " -> ".join(item.get_text(strip=True) for item in items if item.get_text(strip=True))
```

## 6. Особенности CS-Cart

### 6.1 Структура HTML

CS-Cart генерирует предсказуемую HTML-структуру:

```html
<!-- Категория: список товаров -->
<div class="ty-grid-list">
  <div class="ty-column3">
    <div class="ty-grid-list__item">
      <form action="https://siriust.ru" method="post">
        <div class="ty-grid-list__image">
          <a href="/...product-slug.../">
            <img class="ty-pict" src="...image.jpg" alt="...name..." />
          </a>
        </div>
        <div class="ty-grid-list__item-name">
          <a href="/...product-slug.../" class="product-title">Название товара</a>
        </div>
        <div class="ty-grid-list__price">
          <span class="ty-price">
            <span class="ty-price-num">4 500</span>
            <span class="ty-price-num">₽</span>
          </span>
        </div>
      </form>
    </div>
  </div>
</div>

<!-- Пагинация -->
<div class="ty-pagination">
  <a class="ty-pagination__next">Вперед</a>
  <span class="ty-pagination__items">
    <a class="ty-pagination__item">1</a>
    <a class="ty-pagination__item">2</a>
  </span>
</div>
```

### 6.2 Возможные JSON-эндпоинты

CS-Cart может предоставлять JSON API через те же dispatch-параметры, если добавить `?format=json` или через AJAX:

```python
# Возможные JSON-ручки (нужно проверить через DevTools):
# 1. Поиск через AJAX:
#    ?dispatch=products.search&q={query}&format=json
# 2. Категория через AJAX:
#    ?dispatch=categories.view&category_id={id}&format=json
# 3. Товар через AJAX:
#    ?dispatch=products.view&product_id={id}&format=json
```

Проверить наличие JSON API — приоритет при реализации, так как JSON парсится надёжнее HTML.

### 6.3 Анти-парсинг

- **Yandex Metrika:** есть счётчик (`mc.yandex.ru`), не влияет на парсинг
- **Cookies:** требуется acceptance cookie (`cookies_accepted=Y`)
- **Rate limiting:** стандартный для CS-Cart (nginx), рекомендуется задержка 1-2 сек между запросами
- **User-Agent:** ротация 5+ вариантов

## 7. Обработка ошибок

| Ситуация | Действие |
|----------|----------|
| 404 (товар/категория не найдена) | Пропустить, залогировать |
| 429 (Too Many Requests) | Подождать 30 сек, повторить |
| 503 (сервер перегружен) | Exponential backoff, до 5 попыток |
| Изменение HTML-структуры | Ловить исключение `ParserParseError`, залогировать селектор |
| Сеть недоступна | `ParserConnectionError`, retry 3 раза |
| Пустая страница категории | Пропустить категорию |

## 8. Тестирование

| Тест | Что проверяет |
|------|---------------|
| `test_search_samsung` | Поиск по "дисплей samsung", проверить > 0 результатов |
| `test_search_no_results` | Поиск по несуществующему запросу, проверить пустой результат |
| `test_parse_product` | Парсинг конкретного товара по URL, проверить все поля |
| `test_parse_price` | Парсинг цены из текста "4 500 ₽" → Decimal |
| `test_normalize_name` | Нормализация "Дисплей Samsung Galaxy S22 Ultra" |
| `test_category_pagination` | Обход категории с 2+ страницами |

## 9. Fixtures (HTML-образцы)

Для тестов сохранить HTML-страницы:
- `tests/fixtures/html/profi/category.html` — страница категории с товарами
- `tests/fixtures/html/profi/product.html` — детальная страница товара
- `tests/fixtures/html/profi/search.html` — страница результатов поиска
- `tests/fixtures/html/profi/search_empty.html` — пустые результаты

## 10. Зависимости

- `httpx` — асинхронный HTTP-клиент
- `beautifulsoup4` + `lxml` — парсинг HTML
- `re` — regex для извлечения цен и ID
- `asyncio` — асинхронный обход категорий

## 11. Потенциальные риски и их решение

| Риск | Решение |
|------|---------|
| Изменение CSS-классов после обновления CS-Cart | Вынести селекторы в конфиг, добавить fallback-селекторы |
| Блокировка по IP при частых запросах | Задержка 1-3 сек между запросами, ротация User-Agent |
| Изменение URL-схемы | Использовать dispatch-параметры как fallback |
| Большой каталог (>10k товаров) | Разбить обход на чанки по категориям, пагинация |
| CAPTCHA при частых запросах | Пока не обнаружена; при появлении — увеличить задержки |
