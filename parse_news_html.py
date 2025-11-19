"""
Script para parsear o conteúdo completo dos anúncios do HTML capturado.
"""

import json
from html.parser import HTMLParser
from bs4 import BeautifulSoup
import re

class NewsAnnouncement:
    def __init__(self, title, date, content="", url=""):
        self.title = title
        self.date = date
        self.content = content
        self.url = url

def parse_news_html(html_file):
    """Extrai anúncios do HTML."""

    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    announcements = []

    # Procurar pela tabela de anúncios (data-list-id ou similar)
    tables = soup.find_all('table')
    print(f"Encontradas {len(tables)} tabelas no HTML")

    # A tabela principal de anúncios deve ter 33 linhas segundo o output anterior
    main_table = None
    for table in tables:
        tbody = table.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
            if len(rows) == 16:  # Tabela com os anúncios reais
                main_table = table
                break

    if not main_table:
        # Tentar encontrar por outro critério
        for table in tables:
            tbody = table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                # A tabela correta terá células com conteúdo real (não vazias)
                if len(rows) > 10:
                    # Verificar se tem anúncios reais
                    has_announcements = False
                    for row in rows[:3]:
                        cells = row.find_all('td')
                        if len(cells) >= 2:
                            text = cells[0].get_text(strip=True)
                            if 'Reminder' in text or 'Building' in text or 'Sprint' in text:
                                has_announcements = True
                                break
                    if has_announcements:
                        main_table = table
                        break

    # Procurar direto por linhas que contêm anúncios (usando TH em vez de TD)
    rows = soup.find_all('tr')
    print(f"Total de {len(rows)} linhas encontradas no HTML")

    for row in rows:
        # Procurar por célula TH ou TD que contenha um link com anúncio
        title_link = row.find('a', class_='d2l-link-inline')

        if title_link:
            title = title_link.get_text(strip=True)
            url = title_link.get('href', '')

            # Procurar pela data na mesma linha
            cells = row.find_all(['td', 'th'])
            date = ''
            if len(cells) >= 2:
                date = cells[-1].get_text(strip=True)  # Última célula geralmente é a data

            if title and not title.startswith('Show') and not title.startswith('Search'):
                announcement = {
                    'title': title,
                    'date': date,
                    'url': url,
                    'index': len(announcements) + 1
                }
                announcements.append(announcement)

    return announcements, soup

def extract_full_content(html_file):
    """Extrai o conteúdo completo das páginas de anúncios."""

    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    # Procurar por divs de conteúdo
    content_divs = soup.find_all('div', class_=['d2l-widget', 'content-item', 'd2l-news-item'])

    full_content = {
        'announcements': [],
        'raw_text': soup.get_text()
    }

    return full_content

def main():
    html_file = "news_page_content.html"

    print("="*80)
    print("PARSEANDO ANÚNCIOS DO HTML")
    print("="*80)

    announcements, soup = parse_news_html(html_file)

    print(f"\n✓ {len(announcements)} anúncios encontrados\n")

    # Salvar como JSON
    output_json = {
        'total': len(announcements),
        'course': 'INFO-6156-(01)-25F',
        'announcements': announcements
    }

    with open('parsed_announcements.json', 'w', encoding='utf-8') as f:
        json.dump(output_json, f, indent=2, ensure_ascii=False)

    print("Anúncios extraídos:")
    print("="*80)
    for idx, ann in enumerate(announcements, 1):
        print(f"\n{idx}. {ann['title']}")
        print(f"   Data: {ann['date']}")
        if ann['url']:
            print(f"   URL: {ann['url']}")

    print("\n" + "="*80)
    print(f"Total de anúncios: {len(announcements)}")
    print("Arquivo salvo: parsed_announcements.json")
    print("="*80)

if __name__ == "__main__":
    main()
