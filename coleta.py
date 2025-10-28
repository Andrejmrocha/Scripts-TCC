import json
import csv
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os


def scrap_instagram_comments(link, chave_partida, data_partida, numero_rolagens=40):
    """
    Faz scraping de comentários de um post do Instagram.

    Args:
        link: URL do post do Instagram
        chave_partida: Chave da partida (ex: "BAH_X_CSC")
        data_partida: Data da partida (ex: "20.07.2025")
        numero_rolagens: Número de rolagens para carregar comentários

    Returns:
        list: Lista de comentários únicos coletados
    """
    perfil_temporario = os.path.abspath("chrome_selenium_profile")
    os.makedirs(perfil_temporario, exist_ok=True)

    caminho_driver = "chromedriver-win64\\chromedriver.exe"

    opcoes_chrome = ChromeOptions()
    opcoes_chrome.add_argument("--start-maximized")
    opcoes_chrome.add_argument(f"--user-data-dir={perfil_temporario}")
    servico = ChromeService(executable_path=caminho_driver)
    driver = webdriver.Chrome(service=servico, options=opcoes_chrome)

    try:
        print(f"\n{'=' * 60}")
        print(f"Processando: {chave_partida} - {data_partida}")
        print(f"Link: {link}")
        print(f"{'=' * 60}")

        print("Acessando o post...")
        driver.get(link)

        print("Aguardando o carregamento da página...")
        time.sleep(5)

        div_scroll_class = "x5yr21d.xw2csxc.x1odjw0f.x1n2onr6"

        try:
            wait = WebDriverWait(driver, 15)
            scrollable_div = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"div.{div_scroll_class}"))
            )
            print("Área de comentários encontrada. Iniciando rolagem...")

            for i in range(numero_rolagens):
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
                print(f"Rolagem {i + 1}/{numero_rolagens}...")
                time.sleep(2)

        except TimeoutException:
            print("\nERRO: Não foi possível encontrar a área de comentários para rolar.")
            print("Possíveis causas:")
            print("1. O Instagram atualizou as classes HTML do site.")
            print("2. A página não carregou corretamente.")
            return []

        print("\nColetando os textos dos comentários...")

        comment_span_class = "x1lliihq x1plvlek xryxfnj x1n2onr6 xyejjpt x15dsfln x193iq5w xeuugli x1fj9vlw x13faqbe x1vvkbs x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x1i0vuye xl565be xo1l8bm x5n08af x10wh9bi xpm28yp x8viiok x1o7cslx"

        comment_spans = driver.find_elements(By.XPATH, f"//span[@class='{comment_span_class}']")

        if not comment_spans:
            print("\nAVISO: Nenhum comentário foi encontrado com a classe especificada.")
            return []

        comments_list = [span.text for span in comment_spans]
        unique_comments = list(dict.fromkeys(comments_list))

        filtered_comments = [comment for comment in unique_comments if len(comment) <= 111]

        print(f"\n--- Total de comentários coletados: {len(unique_comments)} ---")
        print(f"--- Comentários filtrados (≤111 caracteres): {len(filtered_comments)} ---")
        print(f"--- Comentários descartados: {len(unique_comments) - len(filtered_comments)} ---")

        # Concatena o nome do arquivo: chave + data
        nome_arquivo = f"./dados/coletados/{chave_partida}_{data_partida}.csv"

        # Garante que o diretório existe
        os.makedirs(os.path.dirname(nome_arquivo), exist_ok=True)

        with open(nome_arquivo, "w", encoding="utf-8", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Número', 'Comentário'])  # Cabeçalho

            for i, comment in enumerate(filtered_comments, 1):
                print(f"{i}: {comment}")
                writer.writerow([i, comment])

        print(f"\nSucesso! Os comentários foram salvos no arquivo {nome_arquivo}.")
        return unique_comments

    except Exception as e:
        print(f"\nERRO: Ocorreu um erro ao extrair os textos dos comentários: {e}")
        return []

    finally:
        print("\nFechando o navegador.")
        driver.quit()


def process_json_file(json_path):
    """
    Processa um arquivo JSON com múltiplas partidas e faz scraping de todas.

    Args:
        json_path: Caminho para o arquivo JSON
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"\nTotal de partidas a processar: {len(data)}")

        results = {}
        for chave_partida, match_data in data.items():
            link = match_data[0]
            data_partida = match_data[1]

            comments = scrap_instagram_comments(link, chave_partida, data_partida)
            results[chave_partida] = {
                'data': data_partida,
                'comments_count': len(comments)
            }

            # Pausa entre requisições para não sobrecarregar
            time.sleep(3)

        print("\n" + "=" * 60)
        print("RESUMO DO PROCESSAMENTO")
        print("=" * 60)
        for match, info in results.items():
            print(f"{match} ({info['data']}): {info['comments_count']} comentários")

    except FileNotFoundError:
        print(f"\nERRO: Arquivo JSON não encontrado: {json_path}")
    except json.JSONDecodeError:
        print(f"\nERRO: Arquivo JSON inválido: {json_path}")
    except Exception as e:
        print(f"\nERRO: {e}")


if __name__ == "__main__":
    # Exemplo de uso
    json_file = "../arquivos_scrap/lote_partidas/lote2.json"  # Altere para o caminho do seu arquivo JSON
    process_json_file(json_file)
