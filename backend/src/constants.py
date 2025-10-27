CSS = """
    <style>
        .st-emotion-cache-liupih { padding-top: 2.5rem; }

    </style>
"""

TAB_ICON = None

JAPANESE = 'Japanese'
SPANISH = 'Spanish'
INDONESIAN = 'Indonesian'
KOREAN = 'Korean'
VIETNAMESE = 'Vietnamese'
THAI = 'Thai'
ENGLISH = 'English'


def TAB_TITLE(l):
    return 'YouTube Help AI Assistant'


def TITLE(l):
    if l == JAPANESE:
        return 'パートナーマネージャー AI サポート'
    else:
        return 'YouTube Help AI Assistant'

def SUBTITLE(l):
    if l == JAPANESE:
        return '⚠️ YouTubeヘルプに書いている情報のみ答えられます。AIの情報を鵜呑みにせずに、左カラムの情報ソースのリンクを必ず確認して下さい。'
    elif l == SPANISH:
        return '⚠️ Solo puedo responder la información escrita en la Ayuda de YouTube. No se limite a tomar la información de la IA al pie de la letra; asegúrese de consultar los enlaces de fuentes de información en la columna de la izquierda.'
    elif l == INDONESIAN:
        return '⚠️ Saya hanya bisa menjawab informasi yang tertulis di Bantuan YouTube. Jangan hanya menerima informasi AI begitu saja; pastikan untuk memeriksa tautan sumber informasi di kolom kiri.'
    elif l == KOREAN:
        return '⚠️ YouTube 도움말에 기재된 정보에만 답변해드릴 수 있습니다. AI 정보를 액면 그대로 받아들이지 마십시오. 왼쪽 열의 정보 소스 링크를 확인하세요.'
    elif l == VIETNAMESE:
        return '⚠️ Tôi chỉ có thể trả lời những thông tin được ghi trong Trợ giúp YouTube. Đừng chỉ lấy thông tin AI theo mệnh giá; hãy chắc chắn kiểm tra các liên kết nguồn thông tin ở cột bên trái.'
    elif l == THAI:
        return 'ฉันสามารถตอบได้เฉพาะข้อมูลที่เขียนไว้ในวิธีใช้ของ YouTube เท่านั้น อย่าเพิ่งใช้ข้อมูล AI ตามมูลค่าที่กำหนด อย่าลืมตรวจสอบลิงก์แหล่งข้อมูลในคอลัมน์ด้านซ้าย'
    else:
        return 'Disclaimer: This AI is designed to provide information based on the YouTube Help documentation. Users are advised to consult the original source links in the left column for verification.'


def INPUT_HOLDER(l):
    if l == JAPANESE:
        return 'YouTubeに関する質問をして下さい。また、過去の会話は記憶しないことにご留意ください。'
    elif l == SPANISH:
        return 'Por favor haga preguntas sobre YouTube. Además, tenga en cuenta que las conversaciones pasadas no se recuerdan.'
    elif l == INDONESIAN:
        return 'Silakan ajukan pertanyaan tentang YouTube. Harap dicatat juga bahwa percakapan masa lalu tidak diingat.'
    elif l == KOREAN:
        return '유튜브에 대해 질문해주세요. 또한, 과거 대화 내용은 기억되지 않으니 주의하시기 바랍니다.'
    elif l == VIETNAMESE:
        return 'Vui lòng đặt câu hỏi về YouTube. Ngoài ra, xin lưu ý rằng các cuộc trò chuyện trong quá khứ không được ghi nhớ.'
    elif l == THAI:
        return 'กรุณาถามคำถามเกี่ยวกับ YouTube นอกจากนี้ โปรดทราบว่าการสนทนาที่ผ่านมาจะไม่ถูกจดจำ'
    else:
        return 'Ask about YouTube. (Note: Conversation history is not saved.)'


def CLEAR_BUTTON(l):
    return 'CLEAR'

def DOC_HISTORY(l):
    return 'Doc History'

def SIDEBAR_SUBTITLE(l):
    if l == JAPANESE:
        return '[情報ソース]'
    elif l == SPANISH:
        return '[FUENTES]'
    elif l == INDONESIAN:
        return '[SUMBER]'
    elif l == KOREAN:
        return '[출처]'
    elif l == VIETNAMESE:
        return '[NGUỒN THÔNG TIN]'
    elif l == THAI:
        return '[แหล่งข้อมูล]'
    else:
        return '[Sources]'


