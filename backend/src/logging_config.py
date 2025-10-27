import os
import logging.config

LOG_DIR = "logs"
# os.makedirs() のようなファイルシステムを操作する関数は、カレントワーキングディレクトリを基準に動作します。
# ユーザーがプロジェクトのトップ階層で streamlit run app.py というコマンドを実行した場合、そのコマンドを実行した場所、
# つまりプロジェクトのトップ階層がカレントワーキングディレクトリになり、そこに logs というフォルダが生成されます。
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING_CONFIG = {
    'version': 1,

    # disable_existing_loggers: True に設定すると、dictConfigが実行された時点で既に存在していたロガー
    # （例：sqlalchemyやstreamlitなど）の disabled という内部的なフラグが True に設定されます。
    # このフラグが True になったロガーは、ログレベルに関係なく、すべてのログメッセージを破棄します。
    # これは、エラー（ERROR）や致命的な（CRITICAL）レベルのログであっても機能しなくなる。
    # つまり、単にレベル設定を無効化するというものではなく、ロガーの機能そのものを完全に停止させるという強力な設定
    'disable_existing_loggers': False,

    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s:%(funcName)s:%(lineno)d - %(levelname)s - %(message)s',
        },
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'default',
        },
        'file': {
            # RotatingFileHandler は、ログファイルが際限なく大きくなり続けるのを防ぐための仕組み
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'filename': os.path.join(LOG_DIR, 'app.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            # 過去のログは最大3世代分 (app.log.1 〜 app.log.3) までが保持されるようになる。
            'backupCount': 3,
            'encoding': 'utf-8',
        },
    },

    'loggers': {
        # 1. ルートロガー: 全てのログの「デフォルト設定」（原則）
        # ここで全てのライブラリのログレベルを'INFO'にフィルタリングします。
        # ハンドラは、アプリケーション全体の出口として、ここにだけ設定します。
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },

        # 2. 自分のアプリ(src)だけを「特別扱い」する設定（例外）
        # ルートの'INFO'設定を上書きし、'DEBUG'レベルまで詳細なログを許可します。
        # ハンドラは設定せず、ログをルートに伝播させて処理を任せます。
        'src': {
            'level': 'DEBUG',
        }
    }
}


def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)
    # __name__の値は、実質的に src.config_logging になる。
    logger = logging.getLogger(__name__)
    logger.info("ロギング設定が完了しました。")