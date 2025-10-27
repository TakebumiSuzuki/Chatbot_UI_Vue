import re
import time
import datetime
from dotenv import load_dotenv

from google.cloud import aiplatform
from google import genai
from google.genai.types import EmbedContentConfig
from google.cloud.sql.connector import Connector


from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from src.models.chunk import Chunk
from src import config
from src import constants
from src import prompts

from src.exceptions import (
    RetryableRetrievalError,
    NonRetryableRetrievalError,
    RetryableGenerationError,
    NonRetryableGenerationError
)
from google.api_core import exceptions as google_exceptions
from sqlalchemy import exc as sqlalchemy_exceptions


import logging
logger = logging.getLogger(__name__)

load_dotenv()

PROJECT_ID = config.PROJECT_ID
LOCATION = config.LOCATION

# DATABASE_URL = config.DATABASE_URL
INSTANCE_CONNECTION_NAME = config.INSTANCE_CONNECTION_NAME
CLOUDSQL_USER = config.CLOUDSQL_USER
CLOUDSQL_PASSWORD = config.CLOUDSQL_PASSWORD
CLOUDSQL_DATABASE = config.CLOUDSQL_DATABASE

GEMINI_HYDE_MODEL = config.GEMINI_HYDE_MODEL
HYDE_PROMPT = prompts.HYDE_PROMPT
QA_PROMPT = prompts.QA_PROMPT
GEMINI_EMBEDDING_MODEL = config.GEMINI_EMBEDDING_MODEL
EMBEDDING_DIMENSIONS = config.EMBEDDING_DIMENSIONS

INDEX_ENDPOINT_NAME=  config.INDEX_ENDPOINT_NAME
DEPLOYED_INDEX_ID = config.DEPLOYED_INDEX_ID
GEMINI_QA_MODEL = config.GEMINI_QA_MODEL
MAX_INPUT = config.MAX_INPUT

# ここのグローバルなスコープで起こるエラーは、起動時エラーであり、そもそもここでエラーが出ると、
# どのユーザーのリクエストも正常に処理できる状態にないということになる。
# このようなスコープでは、エラーをハンドルしてゾンビ状態でアプリを稼働させるのではなく、
# Fail Fast の考え方で、即座にアプリを停止させる方が良い。よって、try exceptによるハンドルはしない。　
connector = Connector()

# getconn 関数の中では、Cloud SQL ConnectorがIAM認証、SSL/TLS暗号化、安全なトンネルの確立といった
# 全ての複雑な処理を行い、最終的に標準的なデータベース接続オブジェクトを返します。
def getconn():
    conn = connector.connect(
        # MySQLなどのデータベースサーバーが動作している仮想マシンそのものを一意に識別するための住所
        INSTANCE_CONNECTION_NAME,
        "pymysql",
        user=CLOUDSQL_USER,
        password=CLOUDSQL_PASSWORD,
        # INSTANCE_CONNECTION_NAME によって特定される仮想マシンの中には、複数のデータベースが運用
        # されている可能性があるが、一つのデータベースのみ引数で指定できる。
        db=CLOUDSQL_DATABASE
    )
    return conn

engine = create_engine(
    # creator が指定されている場合、これによって出来上がった接続を受け取って利用する
    "mysql+pymysql://",
    creator=getconn,
    # 予期せぬ接続断による実行時エラーを防ぐため、接続貸出前に生存確認を行う
    pool_pre_ping=True,
    # 接続が作成されてから一定時間が経過したら、その接続を自動的に破棄して新しいものに置き換える。
    pool_recycle=3600,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

aiplatform.init(project=PROJECT_ID, location=LOCATION)
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)


def _generate_hypothetical_document(user_query: str) -> str:
    """Generates a hypothetical document from a user query."""
    start_time = time.time()

    response = client.models.generate_content(
        model=GEMINI_HYDE_MODEL,
        contents=HYDE_PROMPT + user_query,
    )
    hypothetical_document = response.text

    logger.info(f"Using model for generating hypothetical document: {GEMINI_HYDE_MODEL}")
    logger.info(f"Generated hypothetical document: {hypothetical_document}")

    elapsed_time = time.time() - start_time
    logger.debug(f"generate_hypothetical_document execution time: {elapsed_time:.3f} seconds")

    return hypothetical_document


def _split_last_brackets(input_string: str) -> tuple[str, str]:
    """Splits off a bracketed `[...]` part from the end of a string."""
    match = re.match(r"(.*)(\[.*?\])$", input_string, re.DOTALL)
    if match:
        prompt_part = match.group(1).strip()
        bracket_part = match.group(2)
        return prompt_part, bracket_part
    else:
        return input_string, ""


def _extract_language(text: str) -> str:
    if 'japanese' in text.lower():
        return constants.JAPANESE
    elif 'spanish' in text.lower():
        return constants.SPANISH
    elif 'indonesian' in text.lower():
        return constants.INDONESIAN
    elif 'korean' in text.lower():
        return constants.KOREAN
    elif 'vietnamese' in text.lower():
        return constants.VIETNAMESE
    elif 'thai' in text.lower():
        return constants.THAI
    else:
        return constants.ENGLISH


def _get_text_embedding(text_to_embed: str) -> list[float]:
    """Generates a vector embedding for the given text."""
    response = client.models.embed_content(
        model=GEMINI_EMBEDDING_MODEL,
        contents=[text_to_embed],
        config=EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=EMBEDDING_DIMENSIONS,
        ),
    )
    text_embedding = response.embeddings[0].values
    logger.debug(f"Embeddings have been successfully generated.")
    return text_embedding


def _retrieve_from_vector_search(
    index_endpoint_id: str,
    deployed_index_id: str,
    query_embedding: list[float],
    num_neighbors: int = 4,
    language: str = 'English'
) -> list[dict[str, str|float ]]:
    """Retrieves similar document IDs from Vertex AI Vector Search for a given embedding."""
    logger.info("Starting retrieval from Vertex AI Vector Search.")

    # 2. インデックスエンドポイントのインスタンスを作成
    # index_endpoint_id は、数値のIDでも、完全なリソース名
    # ("projects/.../indexEndpoints/...") のどちらでも可
    index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
        index_endpoint_name=index_endpoint_id
    )

    # 3. find_neighbors メソッドで近傍探索を実行
    # queries引数はベクトルのリストを受け付けるため、単一のクエリでもリストでラップする
    response = index_endpoint.find_neighbors(
        queries=[query_embedding],
        deployed_index_id=deployed_index_id,
        num_neighbors=num_neighbors,
        return_full_datapoint=True
    )

    # 4. 結果を分かりやすい形式に整形
    search_results = []
    # responseはクエリごとの結果リストのリスト [[neighbor1, neighbor2,...]]
    if response and response[0]:
        for neighbor in response[0]:
            scraped_at_timestamp = None
            scraped_at = None

            for restrict_namespace in neighbor.restricts:

                # nameが'scraped_at_timestamp'であるものを探す
                if restrict_namespace.name == 'scraped_at_timestamp':

                    # allow_tokensリストの最初の要素を取得
                    timestamp_str = restrict_namespace.allow_tokens[0]

                    logger.debug(f"Retrieved timestamp (string): {timestamp_str}")

                    # (オプション) 文字列を整数に変換して計算などに使う
                    scraped_at_timestamp = int(timestamp_str)
                    logger.debug(f"Converted timestamp (integer): {scraped_at_timestamp}")

                    # (オプション) 日付に変換して確認する
                    dt_object = datetime.datetime.fromtimestamp(scraped_at_timestamp)
                    # 指定されたフォーマットの文字列に変換
                    scraped_at = dt_object.strftime("%Y/%m/%d %H:%M")

                    logger.debug(f"Formatted local datetime: {scraped_at}")

                    break

            search_results.append({
                "id": neighbor.id,          # データポイントのID
                "distance": neighbor.distance, # クエリとの距離 (値が小さいほど類似)
                "scraped_at_timestamp": scraped_at_timestamp,
                "scraped_at": scraped_at
            })

    logger.debug(f"Retrieved {len(search_results)} similar data points from Vector Search.")
    return search_results




def _fetch_records_from_db(datapoints: list[dict[str, str|float]]) -> list[dict|None]:
    """
    Fetches document records from the Cloud SQL database based on a list of search result IDs.

    Note: The order of the returned records matches the order of the input datapoints.
    If an ID is not found in the database, its corresponding entry in the list will be None.
    """
    logger.info("Fetching corresponding records from Database.")

    id_list = [datapoint["id"] for datapoint in datapoints if "id" in datapoint]
    if not id_list:
        logger.warning("No valid IDs found in datapoints. Returning an empty list.")
        return []

    # SQLAlchemy の select を使ってクエリを構築
    stmt = select(Chunk).where(Chunk.id.in_(id_list))
    # SessionLocal() 自体が context manager なので with で閉じられる
    with SessionLocal() as session:
        # 構築した select 文 (stmt) を実行する
        # パラメータは select 文に含まれているため、ここでは渡す必要がない
        records = session.execute(stmt).scalars().all()

    # 結果を datapoints の順に整列させるため、IDをキーにした辞書を作成します
    records_with_id_key = {record.id: record for record in records}

    # 元のIDリストの順序に従って、レコードのリストを再構築します
    ordered_records = []
    for id in id_list:
        found_record = records_with_id_key.get(id)
        if found_record is None:
            logger.error(f'Database discrepancy occured. The chunk text of id:{id} cound not be found in the database')
            continue
        ordered_records.append(found_record)

    logger.debug(f"Fetched {len(records)} records for {len(id_list)} IDs from the database.")
    return ordered_records


def _make_final_context(chunk_records: list) -> str:
    documents = []
    for chunk in chunk_records:
        if chunk is None:
            continue
        scraped_at = chunk.scraped_at.strftime("%Y/%m/%d %H:%M")
        text = 'Data as of: ' + scraped_at + '\n' + chunk.content
        documents.append(text)

    final_context = "\n---\n" + "\n---\n".join(documents)
    logger.info(final_context)

    return final_context


def handle_retrieval(user_query: str) -> tuple[str, str]:
    """
    Orchestrates the RAG document retrieval pipeline.

    Args:
        user_query: The raw input string from the user.

    Returns:
        A tuple containing the concatenated document chunks and the detected language.

    Raises:
        RetryableRetrievalError: For temporary issues where a retry might succeed.
        NonRetryableRetrievalError: For permanent issues where a retry would fail.
    """
    try:
        if not user_query or not user_query.strip():
            raise NonRetryableRetrievalError('User query is empty or contains only whitespace.')

        if len(user_query) > MAX_INPUT:
            logger.info(f"Input length exceeded {MAX_INPUT} characters. Truncating the input.")
            user_query = user_query[:MAX_INPUT]

        hypothetical_document = _generate_hypothetical_document(user_query)
        hypothetical_document, bracket_part = _split_last_brackets(hypothetical_document)
        language = _extract_language(bracket_part)
        hyde_embedding = _get_text_embedding(hypothetical_document)
        search_results = _retrieve_from_vector_search(
            index_endpoint_id=INDEX_ENDPOINT_NAME,
            deployed_index_id=DEPLOYED_INDEX_ID,
            query_embedding=hyde_embedding,
            num_neighbors=config.K
        )
        if not search_results:
            logger.info("No relevant datapoints found for the user's query.")
            raise NonRetryableRetrievalError("No relevant datapoints found for the question.")

        chunk_records = _fetch_records_from_db(search_results)

        if not chunk_records:
            logger.error("No chunks found from datapoint ids.")
            raise NonRetryableRetrievalError("No chunks were found from datapoint ids.")

        final_context = _make_final_context(chunk_records)

        return final_context, language

    # --- Exception Handling ---

    except (RetryableRetrievalError, NonRetryableRetrievalError):
        raise

    # [Retryable] API rate limits or temporary server errors.
    except (google_exceptions.ResourceExhausted, google_exceptions.ServiceUnavailable, google_exceptions.DeadlineExceeded) as e:
        logger.warning(f"A retryable API error occurred: {e}", exc_info=True)
        raise RetryableRetrievalError("Access to the external API is temporarily unavailable due to high traffic.") from e

    # [Retryable] Temporary database connection errors.
    except sqlalchemy_exceptions.OperationalError as e:
        logger.warning(f"A retryable database error occurred: {e}", exc_info=True)
        raise RetryableRetrievalError("The connection to the database was temporarily lost.") from e

    # [Non-Retryable] Authentication/permission errors (e.g., invalid API key).
    except google_exceptions.PermissionDenied as e:
        logger.error(f"A non-retryable API permission error occurred: {e}", exc_info=True)
        raise NonRetryableRetrievalError("Permission denied for the external API. Please check the configuration.") from e

    # [Non-Retryable] Invalid arguments or resource not found (e.g., wrong index ID).
    except (google_exceptions.NotFound, google_exceptions.InvalidArgument) as e:
        logger.error(f"A non-retryable API resource error occurred: {e}", exc_info=True)
        raise NonRetryableRetrievalError("The specified resource was not found or the request was invalid.") from e

    # [Non-Retryable] DB SQL syntax errors or data inconsistencies (likely a code bug).
    except sqlalchemy_exceptions.SQLAlchemyError as e:
        logger.error(f"A non-retryable database SQL error occurred: {e}", exc_info=True)
        raise NonRetryableRetrievalError("An error occurred during a database operation.") from e

    # [Non-Retryable] Catch-all for any other unexpected errors.
    except Exception as e:
        logger.error(f"An unexpected error occurred during the retrieval process: {e}", exc_info=True)
        # It's safer to treat unexpected errors as non-retryable until the root cause is known.
        raise NonRetryableRetrievalError("An unexpected error occurred during the search.") from e


def get_stream(inputText: str, docs: str, language: str):
    """
    Generates a response stream from the LLM using the provided context.

    Args:
        inputText (str): The user's question to be answered.
        docs (str): A string of retrieved documents to provide context.
        language (str): The target language for the LLM's response.

    Returns:
        A stream of response chunks from the language model.

    Raises:
        RetryableGenerationError: For temporary API issues where a retry might succeed.
        NonRetryableGenerationError: For permanent errors where a retry would fail.
    """
    try:
        qa_template = QA_PROMPT
        qa_base_prompt = qa_template.format(language=language, context=docs) + " Here's the question: "
        logger.debug(qa_base_prompt)

        start_time = time.time()

        logger.info(f"Using model for final QA generation: {GEMINI_QA_MODEL}")
        stream = client.models.generate_content_stream(model=GEMINI_QA_MODEL, contents=qa_base_prompt + inputText)

        elapsed_time = time.time() - start_time

        logger.debug(f"Final QA generation time: {elapsed_time:.3f} seconds")


        return stream

    # [Retryable] API rate limits or temporary server errors.
    except (RetryableGenerationError, NonRetryableGenerationError):
        raise

    except (google_exceptions.ResourceExhausted, google_exceptions.ServiceUnavailable, google_exceptions.DeadlineExceeded) as e:
        logger.warning(f"A retryable LLM generation error occurred: {e}", exc_info=True)
        raise RetryableGenerationError("The response generation service is temporarily unavailable due to high traffic.") from e

    # [Non-Retryable] Authentication/permission errors.
    except google_exceptions.PermissionDenied as e:
        logger.error(f"A non-retryable LLM permission error occurred: {e}", exc_info=True)
        raise NonRetryableGenerationError("Permission denied for the response generation service.") from e

    # [Non-Retryable] Invalid request, e.g., oversized prompt or content policy violation.
    except (google_exceptions.InvalidArgument, google_exceptions.FailedPrecondition) as e:
        logger.error(f"A non-retryable LLM invalid request error occurred: {e}", exc_info=True)
        raise NonRetryableGenerationError("The request is invalid or may have violated the content policy.") from e

    # [Non-Retryable] Catch-all for any other unexpected errors.
    except Exception as e:
        logger.error(f"An unexpected error occurred during stream generation: {e}", exc_info=True)
        raise NonRetryableGenerationError("An unexpected error occurred while generating the response.") from e


"""

---
Data as of: 2025/10/17 06:43
# Create YouTube Shorts

YouTube Shorts is a way for anyone to turn an idea into a chance to connect with new audiences anywhere in the world. All you need is a smartphone and the Shorts camera built right into the YouTube app to create Shorts up to three minutes long. The latest Shorts creation tools make it fast, fun, and easy to be a creator on YouTube. Enhance your YouTube Shorts.

## Create a Short

### Select a thumbnail

You can choose a frame from your Short to be used as the thumbnail before and after you upload your Shorts. Keep in mind that you can only edit your thumbnail from the YouTube app and not from Studio.

Here’s how to select a thumbnail for your Short:

  1. Tap **Create** **Short**.
  2. Record your Short and enter video detail.
  3. Navigate to the final upload screen tap the **Edit** on the thumbnail of your video.
  4. Select a frame to use as your thumbnail.
     * Tip: You can add text and apply filters to your thumbnail. Once done with an edit, you cannot go back to previous edits to make any changes.
  5. Tap **Done.**

Get _Shorts editing tips_.Give feedback about this articleChoose a section to give feedback on

[SOURCE]: https://support.google.com/youtube/answer/10343433?hl=en&ref_topic=10343432
[CATEGORY]: Create Shorts


"""


