import re
import regex
import pandas as pd
import emoji  # Importe a biblioteca

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F700-\U0001F77F"  # alchemical symbols
    "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
    "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    "\U00002702-\U000027B0"  # Dingbats
    "\U000024C2-\U0001F251"
    "]",
    flags=re.UNICODE
)

def normalizar(texto:str):
    # Reduz repetições de letras/números para 2
    texto = re.sub(r'(\w)\1{2,}', r'\1\1', texto)
    # Reduz repetições de pontuação para 2
    texto = re.sub(r'([!?.])\1{3,}', r'\1\1', texto)
    # Remove espaços extras
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto


def separar_emoji_grapheme(texto: str) -> str:
    clusters = regex.findall(r"\X", texto)  # quebra por grapheme cluster
    out = []
    for c in clusters:
        if emoji.is_emoji(c):
            out.append(f" {c} ")
        else:
            out.append(c)
    s = "".join(out)
    s = regex.sub(r"\s+", " ", s).strip()
    return s

def substituir_urls_mencoes(texto: str) -> str:
    """
    Processa um texto para:
    1. Remover o símbolo '@' das menções (mantendo o nome de usuário).
    2. Substituir URLs por '<URL>'.
    """
    # Remove @ de menções (ex: @usuario -> usuario)
    texto = re.sub(r'@(\w+)', r'\1', texto)
    # Substitui URLs (http(s):// ou www.)
    texto = re.sub(r'http\S+|www\.\S+', '<URL>', texto)
    return texto.strip()


def demojize_text(texto: str) -> str:
    """Substitui emojis por sua descrição textual (Estratégia para BERTimbau, BERTweetBR)"""
    return emoji.demojize(texto, delimiters=(" :", ": "), language="pt")

def remover_comentarios_sem_letras_ou_emojis(texto: str) -> str:
    if any(c.isalpha() for c in texto) or any(emoji.is_emoji(c) for c in texto):
        return texto
    return "" # Retorna string vazia se for só pontuação/número


def validar_comentario(texto: str, min_length: int = 3) -> bool:
    """
    Valida se o comentário é válido.

    Args:
        texto: Texto a ser validado
        min_length: Comprimento mínimo aceitável

    Returns:
        True se válido, False caso contrário
    """
    if not texto or not isinstance(texto, str):
        return False

    texto_limpo = texto.strip()

    # Muito curto
    if len(texto_limpo) < min_length:
        return False

    # Verifica se tem letras OU emojis
    tem_letras = any(c.isalpha() for c in texto_limpo)
    tem_emojis = bool(EMOJI_PATTERN.search(texto_limpo))

    return tem_letras or tem_emojis


def pre_processar(texto: str, emoji_strategy: str = 'separate'):
    """
    Executa o pipeline de pré-processamento completo.

    Args:
        texto (str): O texto de entrada.
        emoji_strategy (str):
            'separate': Apenas separa emojis de palavras (para BERTugues).
            'demojize': Substitui emojis por texto (para BERTimbau/BERTweetBR).
            'none': Não faz nada com emojis.
    """
    if not isinstance(texto, str):
        return ""

    resultado = substituir_urls_mencoes(texto)
    resultado = normalizar(resultado)

    if emoji_strategy == 'separate':
        resultado = separar_emoji_grapheme(resultado)
    elif emoji_strategy == 'demojize':
        resultado = demojize_text(resultado)

    if not validar_comentario(resultado):
        return None

    return resultado


def limpar_dataframe(df, coluna_processado='Comentário_Processado', verbose=True):
    """
    Remove duplicados e comentários vazios/inválidos do DataFrame.

    Args:
        df: DataFrame com comentários processados
        coluna_processado: Nome da coluna com texto processado
        verbose: Se True, mostra estatísticas

    Returns:
        DataFrame limpo
    """
    tamanho_inicial = len(df)

    # 1. Remover linhas onde o processamento retornou None/NaN
    df_limpo = df.dropna(subset=[coluna_processado])
    removidos_invalidos = tamanho_inicial - len(df_limpo)

    # 2. Remover comentários vazios (strings vazias)
    df_limpo = df_limpo[df_limpo[coluna_processado].str.strip() != '']
    removidos_vazios = len(df.dropna(subset=[coluna_processado])) - len(df_limpo)

    # 3. Remover duplicados (mantém a primeira ocorrência)
    tamanho_antes_duplicados = len(df_limpo)
    df_limpo = df_limpo.drop_duplicates(subset=[coluna_processado], keep='first')
    removidos_duplicados = tamanho_antes_duplicados - len(df_limpo)

    # 4. Resetar índice
    df_limpo = df_limpo.reset_index(drop=True)

    if verbose:
        print(f"\n📊 ESTATÍSTICAS DE LIMPEZA:")
        print(f"   Total inicial:           {tamanho_inicial}")
        print(f"   Removidos (inválidos):   {removidos_invalidos}")
        print(f"   Removidos (vazios):      {removidos_vazios}")
        print(f"   Removidos (duplicados):  {removidos_duplicados}")
        print(f"   Total removido:          {tamanho_inicial - len(df_limpo)}")
        print(f"   ✅ Total final:          {len(df_limpo)}")

        if tamanho_inicial > 0:
            percentual_mantido = (len(df_limpo) / tamanho_inicial) * 100
            print(f"   Percentual mantido:      {percentual_mantido:.1f}%")

    return df_limpo


if __name__ == "__main__":
    import os

    # --- Configuração dos Caminhos ---
    pasta_entrada = r"C:\Users\ajona\PycharmProjects\PLN\oficial\dados\coletados"
    pasta_saida = r"C:\Users\ajona\PycharmProjects\PLN\oficial\dados\pre_processados"

    # --- Garantir que a pasta de saída exista ---
    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)
        print(f"Diretório de saída criado em: {pasta_saida}")

    # --- Loop pelos arquivos de entrada ---
    for arquivo in os.listdir(pasta_entrada):
        if arquivo.endswith(".csv"):

            caminho_arquivo_entrada = os.path.join(pasta_entrada, arquivo)

            nome_base, _ = os.path.splitext(arquivo)

            print(f"Lendo {caminho_arquivo_entrada}...")

            try:
                df_original = pd.read_csv(caminho_arquivo_entrada, sep=",")

                if 'Comentário' not in df_original.columns:
                    print(f"  AVISO: Coluna 'Comentário' não encontrada em {arquivo}. Pulando...")
                    continue


                df_processado = df_original.copy()
                df_processado['Comentário_Processado'] = df_processado['Comentário'].apply(
                    lambda txt: pre_processar(txt, emoji_strategy='separate')
                )

                df_limpo = limpar_dataframe(df_processado, verbose=True)

                df_limpo['length'] = df_limpo['Comentário_Processado'].apply(len)

                # Constrói o nome de saída
                nome_saida = f"{nome_base}.csv"
                caminho_saida = os.path.join(pasta_saida, nome_saida)

                df_limpo.to_csv(caminho_saida, index=False, encoding="utf-8")
                print(f"  Salvo em: {caminho_saida}")

            except pd.errors.EmptyDataError:
                print(f"  AVISO: Arquivo {arquivo} está vazio. Pulando...")
            except Exception as e:
                print(f"  ERRO inesperado ao processar {arquivo}: {e}")

    print("\n--- Pré-processamento concluído. ---")